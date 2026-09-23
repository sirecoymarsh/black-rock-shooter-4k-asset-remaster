"""Catalog observed PPSSPP textures without inferring runtime keys from source assets."""
from pathlib import Path
from collections import defaultdict, Counter
import hashlib, json, re, struct, datetime, html
from PIL import Image, ImageDraw
ROOT = Path(__file__).resolve().parents[1]
ARC = Path(r'P:\AI\Codex\work_archive\2026-07-25\new-chat-2\work')
OUT = ROOT / 'workspace/inventory'
KEY = re.compile(r'^([0-9a-fA-F]{8})([0-9a-fA-F]{8})([0-9a-fA-F]{8})(?:_(\d+))?$')
ISO = ARC / 'release_build/runtime_fix_iso_20260823_test_v2/BRS_Korean_v1.0.iso'
EXPECTED_ISO = '525b5d2b7d8f4723be25b026e72b69d07d30c2cf84d8a48235577ca3728fc92a'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(4*1024*1024),b''): h.update(block)
    return h.hexdigest()
def save(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True)
    tmp=p.with_suffix(p.suffix+'.tmp')
    tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    tmp.replace(p)
def png_info(p):
    with Image.open(p) as im:
        im.verify()
    with Image.open(p) as im:
        mode=im.mode; im=im.convert('RGBA'); w,h=im.size
        pixels=im.tobytes(); hist=im.getchannel('A').histogram()
        return dict(width=w,height=h,png_mode=mode,rgba_sha256=hashlib.sha256(struct.pack('>II',w,h)+pixels).hexdigest(),
                    alpha_min=next(i for i,v in enumerate(hist) if v),alpha_max=max(i for i,v in enumerate(hist) if v),
                    alpha_zero_pixels=hist[0],alpha_partial_pixels=sum(hist[1:255]),alpha_opaque_pixels=hist[255])
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    iso_sha=sha(ISO)
    if iso_sha != EXPECTED_ISO: raise RuntimeError('ISO differs from v1.0.1 release')
    registry_path=OUT/'asset_ids.json'
    registry=json.loads(registry_path.read_text('utf-8')) if registry_path.exists() else {}
    next_id=max([int(x[4:]) for x in registry.values()]+[0])+1
    texture_root=ARC/'tools/ppsspp/portable/memstick/PSP/TEXTURES/NPUH10126'
    sources=[dict(id='LEGACY-NEW',path=texture_root/'new',hash_algorithm='quick',revision='unknown-mixed',kind='archived_runtime_dump'),
             dict(id='LEGACY-DONE',path=texture_root/'done',hash_algorithm='quick',revision='unknown-mixed',kind='archived_texture_files_unverified_role')]
    for session in sorted((ROOT/'workspace/sessions').iterdir()):
        if not session.is_dir(): continue
        p=session/'memstick/PSP/TEXTURES/NPUH10126/new'
        if p.exists():
            meta=json.loads((session/'session.json').read_text('utf-8-sig'))
            if meta['iso_sha256']!=iso_sha: raise RuntimeError('Session belongs to a different ISO: '+session.name)
            if sha(session/'ppsspp.initial.ini')!=meta['ppsspp_ini_sha256']: raise RuntimeError('Initial config changed: '+session.name)
            if sha(session/'textures.initial.ini')!=meta['textures_ini_sha256']: raise RuntimeError('Initial texture policy changed: '+session.name)
            sources.append(dict(id=session.name,path=p,hash_algorithm='xxh64',revision=iso_sha,kind='current_runtime_dump'))
    annotations_path=OUT/'annotations.json'
    annotations=json.loads(annotations_path.read_text('utf-8')) if annotations_path.exists() else {}
    observations=[]; errors=[]; asset_observations=defaultdict(list)
    for source in sources:
        for p in sorted(source['path'].rglob('*.png')):
            match=KEY.fullmatch(p.stem)
            if not match:
                errors.append(dict(path=str(p),error='not_ppsspp_dump_filename'));continue
            try: meta=png_info(p)
            except Exception as e:
                errors.append(dict(path=str(p),error=str(e)));continue
            pixel=meta['rgba_sha256']
            if pixel not in registry:
                registry[pixel]=f'TEX-{next_id:06d}';next_id+=1
            row=dict(observation_id=source['id']+':'+p.relative_to(source['path']).as_posix(),asset_id=registry[pixel],
                     source_id=source['id'],path=str(p),dump_filename=p.name,ppsspp_key=p.stem.lower(),address=match[1].lower(),
                     clut_dimension_key=match[2].lower(),data_hash=match[3].lower(),mip_level=int(match[4] or 0),
                     hash_algorithm=source['hash_algorithm'],revision=source['revision'],source_kind=source['kind'],
                     png_sha256=sha(p),byte_size=p.stat().st_size,**meta)
            asset_observations[row['asset_id']].append(len(observations));observations.append(row)
    save(registry_path,registry)
    baseline=ROOT/'workspace/baseline_hd_ui_pack/PSP/TEXTURES/NPUH10126'
    manifest=json.loads((ROOT/'workspace/baseline_hd_ui_pack/MANIFEST.json').read_text('utf-8-sig'))
    bindings=[]; section=''
    for lineno,line in enumerate((baseline/'textures.ini').read_text('utf-8-sig').splitlines(),1):
        line=line.strip()
        if line.startswith('['): section=line
        elif section=='[hashes]' and '=' in line and not line.startswith(('#',';')):
            key,target=(s.strip() for s in line.split('=',1))
            bindings.append(dict(key=key.lower(),target=target,line=lineno))
    groups=defaultdict(list)
    for b in bindings: groups[b['key']].append(b)
    replacement_meta={}
    for a in manifest['assets']:
        p=baseline/a['replacement']; info=png_info(p)
        actual=sha(p)
        if actual != a['replacement_sha256']: raise RuntimeError('Baseline hash mismatch: '+str(p))
        replacement_meta[a['replacement']]=dict(**info,png_sha256=actual,source_relative=a['relative'],declared_scale=8)
    duplicates=[]
    for key,bs in groups.items():
        if len(bs)>1:
            same=len({replacement_meta[b['target']]['rgba_sha256'] for b in bs})==1
            duplicates.append(dict(key=key,bindings=bs,pixels_identical=same,status='duplicate_identical_pixels' if same else 'conflicting_replacements'))
    # A wildcard match is a search lead only. Never promote it to an accepted mapping.
    candidates=[]
    for b in bindings:
        m=KEY.fullmatch(b['key'])
        if not m: raise RuntimeError('Bad baseline key '+b['key'])
        specificity='exact' if all(x!='00000000' for x in m.groups()[:3]) else ('address_wildcard' if m[2]!='00000000' and m[3]!='00000000' else 'broad_wildcard')
        for o in observations:
            if o['hash_algorithm']!='quick': continue
            parts=[o['address'],o['clut_dimension_key'],o['data_hash']]
            if all(a=='00000000' or a==v for a,v in zip(m.groups()[:3],parts)) and int(m[4] or 0)==o['mip_level']:
                curr=[observations[i]['observation_id'] for i in asset_observations[o['asset_id']] if observations[i]['source_kind']=='current_runtime_dump']
                candidates.append(dict(binding_line=b['line'],legacy_key=b['key'],legacy_observation=o['observation_id'],asset_id=o['asset_id'],replacement=b['target'],match_type=specificity,current_pixel_equivalent_observations=curr,status='candidate_requires_uv_scene_review'))
    assets=[]
    for aid,indices in sorted(asset_observations.items()):
        sample=observations[indices[0]]
        assets.append(dict(asset_id=aid,rgba_sha256=sample['rgba_sha256'],width=sample['width'],height=sample['height'],
                           alpha_min=sample['alpha_min'],alpha_max=sample['alpha_max'],observation_indices=indices,
                           lane='unclassified',tiling='unknown',uv_region='unknown',consumer_screens=[],mission=None,state=None,
                           output_width=None,output_height=None,scale=None,production_method=None,manual_edit_scope=None,
                           candidate_png_sha256=None,runtime_verification='not_verified',release_eligible=False))
    for asset in assets:
        if asset['asset_id'] in annotations:
            asset['annotation']=annotations[asset['asset_id']]
            asset['lane']=annotations[asset['asset_id']]['lane']
    # Same PPSSPP key and algorithm must not hide differing decoded pixels.
    collisions=[]; keygroups=defaultdict(list)
    for o in observations:keygroups[(o['source_id'],o['ppsspp_key'])].append(o)
    for (sid,key),os in keygroups.items():
        if len({o['rgba_sha256'] for o in os})>1:collisions.append(dict(source_id=sid,key=key,observation_ids=[o['observation_id'] for o in os]))
    current=[o for o in observations if o['source_kind']=='current_runtime_dump']
    legacy_pixel={o['rgba_sha256'] for o in observations if o['hash_algorithm']=='quick'}
    crosswalk=[]
    for o in current:
        matches=[observations[i] for i in asset_observations[o['asset_id']] if observations[i]['hash_algorithm']=='quick']
        crosswalk.append(dict(current_observation=o['observation_id'],current_key=o['ppsspp_key'],asset_id=o['asset_id'],
                              rgba_sha256=o['rgba_sha256'],legacy_observations=[m['observation_id'] for m in matches],legacy_keys=sorted({m['ppsspp_key'] for m in matches}),status='pixel_exact' if matches else 'new_pixels'))
    summary=dict(schema='brs-hd-inventory-summary/v1',generated_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        product_id='NPUH10126',iso_sha256=iso_sha,total_observations=len(observations),unique_pixel_assets=len(assets),
        observations_by_source=dict(Counter(o['source_id'] for o in observations)),current_unique_keys=len({o['ppsspp_key'] for o in current}),
        current_unique_pixel_assets=len({o['asset_id'] for o in current}),current_pixel_assets_matching_legacy=len({o['asset_id'] for o in current if o['rgba_sha256'] in legacy_pixel}),
        baseline_assets=len(manifest['assets']),baseline_bindings=len(bindings),baseline_duplicate_keys=len(duplicates),
        baseline_conflicting_duplicate_keys=sum(not d['pixels_identical'] for d in duplicates),
        baseline_candidate_assets=len({c['replacement'] for c in candidates}),baseline_current_candidate_assets=len({c['replacement'] for c in candidates if c['current_pixel_equivalent_observations']}),
        baseline_broad_wildcard_bindings=sum(KEY.fullmatch(b['key'])[3]=='00000000' for b in bindings),
        errors=len(errors),same_source_key_pixel_collisions=len(collisions),accepted_replacements=0,
        completion_claim='Initial collection and inventory infrastructure only. Full-game coverage unresolved.',
        population_denominator='unknown; observed files are a lower bound, not a full-game total')
    save(OUT/'observations.json',observations);save(OUT/'assets.json',assets);save(OUT/'crosswalk.json',crosswalk)
    save(OUT/'baseline_mapping_audit.json',dict(duplicates=duplicates,bindings=bindings,candidates=candidates,replacements=replacement_meta))
    cross_source=defaultdict(set)
    for o in observations:cross_source[(o['hash_algorithm'],o['ppsspp_key'])].add(o['rgba_sha256'])
    variants=[dict(hash_algorithm=k[0],key=k[1],pixel_hashes=sorted(v),status='revision_or_role_difference_unresolved') for k,v in cross_source.items() if len(v)>1]
    summary['cross_source_key_pixel_variants']=len(variants)
    save(OUT/'errors.json',dict(errors=errors,collisions=collisions,cross_source_variants=variants));save(OUT/'sources.json',[{**s,'path':str(s['path'])} for s in sources])
    save(ROOT/'qa/evidence/inventory_summary.json',summary)
    # A review index, not a reconstructed in-game screenshot.
    current_ids=sorted({o['asset_id'] for o in current})
    sheet=Image.new('RGB',(800,max(1,(len(current_ids)+4)//5)*200),(28,31,38));d=ImageDraw.Draw(sheet)
    for n,aid in enumerate(current_ids):
        o=observations[asset_observations[aid][0]]; im=Image.open(o['path']).convert('RGBA');im.thumbnail((144,150),Image.Resampling.NEAREST)
        x=(n%5)*160+8;y=(n//5)*200+8;sheet.paste(im,(x,y),im);d.text((x,y+153),aid,fill='white');d.text((x,y+169),f"{o['width']}x{o['height']}",fill='white')
    sheet.save(OUT/'current_contact_sheet.png')
    data=[]
    for a in assets:
        os=[observations[i] for i in a['observation_indices']]
        o=next((o for o in os if o['source_kind']=='current_runtime_dump'),os[0])
        data.append(dict(id=a['asset_id'],size=f"{a['width']}x{a['height']}",alpha=f"{a['alpha_min']}..{a['alpha_max']}",
                         current=any(o['source_kind']=='current_runtime_dump' for o in os),url=Path(o['path']).as_uri(),
                         keys=sorted({o['ppsspp_key'] for o in os}),sources=sorted({o['source_id'] for o in os})))
    payload=json.dumps(data,ensure_ascii=False).replace('</','<\\/')
    page='''<!doctype html><meta charset="utf-8"><title>BRS 텍스처 인벤토리</title><style>body{background:#11151c;color:#eef2fa;font:15px system-ui;margin:28px}input,select,button{padding:10px;margin:5px;background:#242d3a;color:white;border:1px solid #59667d}#grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(235px,1fr));gap:15px}.card{background:#202733;padding:12px;overflow-wrap:anywhere}.card img{width:100%;height:160px;object-fit:contain;image-rendering:pixelated;background:repeating-conic-gradient(#333 0% 25%,#222 0% 50%) 50%/16px 16px}small{color:#b6c6d9}h1{margin-bottom:6px}</style><h1>BRS 전체 HD Retexture · 수집 인벤토리</h1><p>관측 파일의 목록입니다. 전체 게임 수집률과 교체팩 완성도를 의미하지 않습니다. 원본 픽셀 동일 그룹만 묶었습니다.</p><input id="q" placeholder="TEX ID / 해시 / 크기"><select id="scope"><option value="current">현재 v1.0.1 덤프</option value="all">과거 자료 포함 전체</option value="legacy">과거 자료만</option></select><button id="prev">이전</button><button id="next">다음</button><p id="count"></p><div id="grid"></div><script>const data=PAYLOAD;let p=0;function draw(){let q=document.querySelector('#q').value.toLowerCase(),s=document.querySelector('#scope').value;let a=data.filter(x=>(s==='all'||(s==='current'?x.current:!x.current))&&JSON.stringify(x).toLowerCase().includes(q));p=Math.max(0,Math.min(p,Math.ceil(a.length/60)-1));document.querySelector('#count').textContent=a.length+' 픽셀 그룹 · '+(p+1)+' 페이지';const g=document.querySelector('#grid');g.replaceChildren();for(const x of a.slice(p*60,(p+1)*60)){const c=document.createElement('div');c.className='card';const img=document.createElement('img');img.loading='lazy';img.src=x.url;c.append(img);const h=document.createElement('h3');h.textContent=x.id+' · '+x.size;c.append(h);const t=document.createElement('small');t.textContent='알파 '+x.alpha+' / '+x.sources.join(', ')+' / '+x.keys.join(', ');c.append(t);g.append(c)}}document.querySelector('#q').oninput=()=>{p=0;draw()};document.querySelector('#scope').onchange=()=>{p=0;draw()};document.querySelector('#prev').onclick=()=>{p--;draw()};document.querySelector('#next').onclick=()=>{p++;draw()};draw();</script>'''.replace('PAYLOAD',payload)
    (OUT/'index.html').write_text(page,encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
