"""Rebuild observed BRS font caches after exact source-cell identification.

No wildcard keys. Unknown nonblank cells fail closed. Does not claim unseen-cache coverage.
"""
import argparse, collections, hashlib, json, shutil, sys, unicodedata
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding='utf8')
UI = Path('P:/AI/Codex/projects/black-rock-shooter-hd-ui-fonts')
PROJECT = Path('P:/AI/Codex/projects/black-rock-shooter-hd-retexture')
SESSION = PROJECT/'release/combined-test-20260924-001005'
OUT = PROJECT/'workspace/font-repair-20260924'
sys.path.insert(0, str(UI/'tools'))
from brs_font_pipeline import parse_font_layout, cell_bytes, decoded_cell_image
import font_heritage as style
S = 8
def sha(b): return hashlib.sha256(b).hexdigest()
def savej(p, value): p.write_text(json.dumps(value, ensure_ascii=False, indent=2), 'utf8')

def build():
    manifest = json.loads((SESSION/'build-manifest.json').read_text('utf-8-sig'))
    assert manifest['iso_sha256'] == 'ffd94390d4f0703a5ba4c2fe66e15cf576215ffaabf588a2a0574cdb7398dd42'
    # Verify input identity once per batch, rather than trusting arbitrary dump directories.
    assert sha((SESSION/'BRS_4K_combined_test.iso').read_bytes()) == manifest['iso_sha256']
    src = UI/'workspace/source/font'
    layout, payload = parse_font_layout((src/'font.lpk').read_bytes())
    aliases = {a['font_index']: a for a in json.loads((src/'glyph_alias_map.json').read_text('utf8'))['aliases']}
    native = {}; lookup = collections.defaultdict(list); glyphs = {}; glyphinfo = []
    for i in range(layout.glyph_count):
        cell = cell_bytes(payload, layout, i)
        im = decoded_cell_image(cell, layout.palette_rgba); native[i] = im
        if not im.getchannel('A').getbbox(): continue
        lookup[im.tobytes()].append(i)
        if i in aliases:
            a = aliases[i]; assert sha(cell) == a['patched_cell_sha256']
            char = a['character']; high = style.body_glyph(char); method = 'Orbit body profile'
        else:
            # Original Shift-JIS code table identifies the glyph. Normalize only fullwidth ASCII.
            original = layout.codes[i].to_bytes(2, 'big').decode('cp932', errors='strict')
            char = unicodedata.normalize('NFKC', original)
            if len(char) != 1 or not (33 <= ord(char) <= 126): continue
            style.require_chars(char)
            mask = Image.new('L', (512,512))
            ImageDraw.Draw(mask).text((40,0), char, font=style.font(256), fill=255)
            bbox = mask.getbbox(); assert bbox and bbox[2] < 512 and bbox[3] < 512
            # Fit original ink bounds, preserving baseline, half/fullwidth metrics and advance.
            x0,y0,x1,y1 = im.getchannel('A').getbbox()
            mask = mask.crop(bbox).resize(((x1-x0)*S,(y1-y0)*S), Image.Resampling.LANCZOS)
            alpha = Image.new('L', (120,120)); alpha.paste(mask,(x0*S,y0*S))
            high = Image.new('RGBA',(120,120),'white'); high.putalpha(alpha)
            method = 'Orbit vector render fitted to native ink bounds'
        assert high.size == (120,120) and high.getchannel('A').getbbox()
        glyphs[i] = high
        glyphinfo.append({'index':i,'character':char,'source_cell_sha256':sha(cell),'hd_rgba_sha256':sha(high.tobytes()),'method':method})
    sources = {}; provenance = collections.defaultdict(list)
    prior = json.loads((UI/'qa/font_build_v4.json').read_text('utf8'))
    def add(f, origin, expected=None):
        im = Image.open(f).convert('RGBA'); digest = sha(im.tobytes())
        if expected: assert digest == expected, f
        if f.stem in sources: assert sources[f.stem][2] == digest, ('key collision',f)
        sources[f.stem] = (f, im, digest); provenance[f.stem].append(origin)
    for rec in prior['records']: add(Path(rec['source']), 'verified-v4-source', rec['source_rgba_sha256'])
    live = SESSION/'memstick/PSP/TEXTURES/NPUH10126'
    livefiles = sorted((live/'new').glob('00000000851096b*.png'))
    for f in livefiles: add(f,'combined-test-20260924-001005')
    qa=OUT/'qa-session'
    if (qa/'session.json').is_file():
        qa_meta=json.loads((qa/'session.json').read_text('utf-8-sig'))
        assert qa_meta['iso_sha256']=='525b5d2b7d8f4723be25b026e72b69d07d30c2cf84d8a48235577ca3728fc92a'
        assert sha(Path(qa_meta['iso']).read_bytes())==qa_meta['iso_sha256']
        for f in sorted((qa/'memstick/PSP/TEXTURES/NPUH10126/new').glob('00000000851096b*.png')):
            add(f,'verified-original-iso-font-qa')
    (OUT/'font').mkdir(parents=True,exist_ok=True)
    (OUT/'source-caches').mkdir(exist_ok=True)
    records=[]; rejected=[]; repertoire=set(); preserved_ambiguous=[]
    cached={};prev={}
    if (OUT/'manifest.json').is_file():
        prev=json.loads((OUT/'manifest.json').read_text('utf8'))
        if prev.get('glyphs')==glyphinfo:
            cached={r['key']:r for r in prev['records']}
    for key,(f,im,digest) in sorted(sources.items()):
        if key in cached and cached[key]['source_rgba_sha256']==digest:
            old=cached[key]
            if sha(Path(old['file']).read_bytes())==old['output_sha256']:
                records.append({**old,'provenance':provenance[key]})
                repertoire.update(c['font_index'] for c in old['cells'])
                preserved_ambiguous.extend(c for c in prev.get('preserved_ambiguous_dash_cells',[]) if c['key']==key)
                continue
        if len(key)!=24 or im.size not in ((128,128),(256,128)):
            rejected.append({'key':key,'reason':'unexpected size or key'});continue
        high=im.resize((im.width*S,im.height*S),Image.Resampling.NEAREST)
        protect=np.ones((im.height,im.width),dtype=bool);cells=[];errors=[]
        for y in range(0,im.height,16):
            for x in range(0,im.width,16):
                cell=im.crop((x,y,x+15,y+15))
                if not cell.getchannel('A').getbbox():continue
                hits=lookup.get(cell.tobytes(),[])
                if not hits:errors.append([x,y,'unidentified cell']);continue
                replacement_ids=[i for i in hits if i in glyphs]
                if not replacement_ids:continue
                # Ambiguous native shapes must never map to different replacement glyphs.
                if len(hits)!=1:
                    # Native long-vowel/dash/minus marks share exactly the same pixels.
                    # Preserve their source line rather than inventing a semantic identity.
                    if set(hits)=={26,27,28,59}:
                        preserved_ambiguous.append({'key':key,'x':x,'y':y,'indices':hits});continue
                    errors.append([x,y,'ambiguous cell',hits]);continue
                i=hits[0];high.paste(glyphs[i],(x*S,y*S));protect[y:y+15,x:x+15]=False
                cells.append({'x':x,'y':y,'font_index':i});repertoire.add(i)
        if errors:rejected.append({'key':key,'errors':errors});continue
        expected=np.repeat(np.repeat(np.array(im),S,0),S,1)
        mask=np.repeat(np.repeat(protect,S,0),S,1)
        assert np.array_equal(np.array(high)[mask],expected[mask]),key
        dest=OUT/'font'/f'{key}.png'; high.save(dest,compress_level=3)
        shutil.copyfile(f,OUT/'source-caches'/f.name)
        records.append({'key':key,'source_rgba_sha256':digest,'source_size':im.size,'output_size':high.size,'output_sha256':sha(dest.read_bytes()),'output_rgba_sha256':sha(high.tobytes()),'source':str(OUT/'source-caches'/f.name),'file':str(dest),'provenance':provenance[key],'cells':cells,'protected_and_gutter_pass':True})
    if rejected:
        savej(OUT/'rejected.json',rejected)
        raise RuntimeError(f'{len(rejected)} caches rejected; see rejected.json')
    oldkeys={r['key'] for r in prior['records']}
    result={'schema':'brs-font-cache-repair/v1','translator_model':'Codex internal','translation_change':'none','source_iso_sha256':manifest['iso_sha256'],'source_font_sha256':sha((src/'font.lpk').read_bytes()),'font_profile':style.PROFILE,'glyphs':glyphinfo,'records':records,'summary':{'cache_count':len(records),'new_cache_count':len(set(sources)-oldkeys),'live_cache_count':len(livefiles),'authored_hangul':len(aliases),'authored_ascii_punctuation':len(glyphs)-len(aliases),'observed_glyphs':len(repertoire),'rejected':len(rejected)},'runtime_status':'pending','coverage_limit':'Only recorded exact cache contents; no claim of unseen arrangements.'}
    result['preserved_ambiguous_dash_cells']=preserved_ambiguous
    savej(OUT/'manifest.json',result)
    # Genuine source-cache comparison; no simulated game screenshot.
    key=livefiles[-1].stem; before=sources[key][1]; after=Image.open(OUT/'font'/f'{key}.png')
    sheet=Image.new('RGBA',(before.width*S*2, before.height*S),'#263447')
    b=before.resize((before.width*S,before.height*S),Image.Resampling.NEAREST)
    sheet.alpha_composite(b,(0,0));sheet.alpha_composite(after,(before.width*S,0));sheet.convert('RGB').save(OUT/'cache-before-after.png')
    print(json.dumps(result['summary'],ensure_ascii=False))

def install():
    m=json.loads((OUT/'manifest.json').read_text('utf8'))
    live=SESSION/'memstick/PSP/TEXTURES/NPUH10126';ini=live/'textures.ini'
    backup=OUT/'textures-before.ini'
    if not backup.exists():shutil.copyfile(ini,backup)
    text=ini.read_text('utf8'); sections={};section=''
    for line in text.splitlines():
        if line.startswith('['):section=line.strip('[]');sections.setdefault(section,{})
        elif '=' in line and not line.lstrip().startswith('#'):
            k,v=line.split('=',1);sections[section][k.strip()]=v.strip()
    destdir=live/'font-repair-v1';destdir.mkdir(exist_ok=True)
    for rec in m['records']:
        src=Path(rec['file']);assert sha(src.read_bytes())==rec['output_sha256']
        dest=destdir/src.name;shutil.copyfile(src,dest)
        assert sha(dest.read_bytes())==rec['output_sha256']
        sections['hashes'][rec['key']]='font-repair-v1/'+src.name
    staged=ini.with_suffix('.ini.repair-tmp')
    staged.write_text('\n\n'.join('['+s+']\n'+'\n'.join(k+' = '+v for k,v in sorted(vals.items())) for s,vals in sections.items())+'\n','utf8')
    staged.replace(ini)
    savej(OUT/'installation.json',{'session':str(SESSION),'count':len(m['records']),'textures_ini_sha256':sha(ini.read_bytes()),'backup':str(backup),'runtime_verified':False})
    print(json.dumps({'installed_cache_count':len(m['records']),'total_keys':len(sections['hashes'])}))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['build','install']);args=ap.parse_args()
    {'build':build,'install':install}[args.action]()
