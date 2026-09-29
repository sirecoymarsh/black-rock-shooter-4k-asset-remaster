"""Read persisted outputs and independently reconstruct the listed SDO consumers."""
from pathlib import Path
import configparser, hashlib, json, sys
import numpy as np
from PIL import Image,ImageDraw,ImageFont
sys.stdout.reconfigure(encoding='utf8')
R=Path(__file__).resolve().parents[1];O=R/'workspace/ui-resident-ko-001';S=8
m=json.loads((O/'manifest.json').read_text('utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
protected={
 'RUI-001':[(0,23,71,32),(71,12,128,32)],
 'RUI-002':[(109,0,128,16),(0,12,109,16)],
 'RUI-003':[(0,34,64,64),(61,0,64,34)],
 'RUI-004':[(0,0,170,32),(170,8,256,32),(216,0,256,8)],
 'RUI-005':[(84,0,128,46),(72,46,128,63),(0,75,128,128)],
 'RUI-006':[(105,0,128,64),(78,23,105,56),(0,56,128,64)],
}
def compose(image,records,dimensions):
    # Affine UV-to-XY reconstruction with point samples at output pixel centers.
    # This uses the SDO vertices themselves, including rotation; no layout guessed
    # from the translated image. It is a static reconstruction, not a screenshot.
    if len(records)>1 and all(r['uv_box']==records[0]['uv_box'] for r in records):records=records[:1]
    bounds=[]
    for r in records:
        v=np.array(r['vertices']);xy=v[:,2:4]+np.array(r['layout_xywh'][:2]);bounds.append((xy.min(0),xy.max(0)))
    left,top=np.min([b[0] for b in bounds],axis=0);right,bottom=np.max([b[1] for b in bounds],axis=0)
    canvas=Image.new('RGBA',(round((right-left)*S),round((bottom-top)*S)))
    arr=np.array(image)
    for r,(lo,hi) in zip(records,bounds):
        v=np.array(r['vertices']);xy=v[:,2:4]+np.array(r['layout_xywh'][:2]);uv=v[:,:2]*np.array(dimensions)
        coeff=np.linalg.lstsq(np.c_[xy,np.ones(len(xy))],uv,rcond=None)[0]
        assert np.max(np.abs(np.c_[xy,np.ones(len(xy))]@coeff-uv))<1e-7
        w,h=np.rint((hi-lo)*S).astype(int);yy,xx=np.mgrid[:h,:w]
        points=np.stack([lo[0]+(xx+.5)/S,lo[1]+(yy+.5)/S,np.ones_like(xx)],-1)@coeff
        pix=np.floor(points*S+1e-7).astype(int)
        assert pix[:,:,0].min()>=0 and pix[:,:,0].max()<image.width and pix[:,:,1].min()>=0 and pix[:,:,1].max()<image.height
        canvas.alpha_composite(Image.fromarray(arr[pix[:,:,1],pix[:,:,0]]),(round((lo[0]-left)*S),round((lo[1]-top)*S)))
    return canvas

checks=[];rows=[];font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',20)
for r in m['records']:
    ims={}
    for role,f in r['files'].items():
        p=Path(f['path']);assert sha(p)==f['sha256'];ims[role]=Image.open(p).copy()
    original=Image.open(r['observed_path']).convert('RGBA')
    assert sha(Path(r['observed_path']))==r['observed_png_sha256']
    expected=original.resize(ims['candidate'].size,Image.Resampling.NEAREST)
    assert expected.tobytes()==ims['source-8x'].tobytes()
    own=np.array(ims['owned-mask'])>0;old=np.array(expected);new=np.array(ims['candidate'])
    assert np.array_equal(old[~own],new[~own])
    source_mask=np.array(ims['source-glyph-mask'])>0
    assert np.all(np.array(ims['clean-plate'])[:,:,3][source_mask]==0)
    reconstructed=ims['clean-plate'].copy();reconstructed.alpha_composite(ims['korean-layer'])
    assert reconstructed.tobytes()==ims['candidate'].tobytes()
    for b in protected[r['id']]:
        box=tuple(x*S for x in b);assert expected.crop(box).tobytes()==ims['candidate'].crop(box).tobytes(),(r['id'],b)
        checks.append(dict(id=r['id'],box=b,rgba_exact=True))
    for label in r['layouts']:
        consumers=label['consumer_records']
        if consumers:
            before=compose(expected,consumers,r['padded_size']);after=compose(ims['candidate'],consumers,r['padded_size'])
            scope='SDO 정적 조립'
        else:
            box=tuple(v*S for v in label['slot']);before=expected.crop(box);after=ims['candidate'].crop(box);scope='아틀라스 영역 · 소비 미확인'
        assert after.getchannel('A').getbbox(),label['uid']
        factor=min(1,670/max(before.width,after.width))
        size=(round(before.width*factor),round(before.height*factor))
        before=before.resize(size,Image.Resampling.NEAREST);after=after.resize(size,Image.Resampling.LANCZOS)
        row=Image.new('RGB',(1420,size[1]+80),'#283746');d=ImageDraw.Draw(row)
        d.text((12,5),label['source']+' → '+label['korean']+'  |  '+scope,font=font,fill='white')
        row.paste(before,(12,40),before);row.paste(after,(728,40),after)
        # A separate native-scale preview makes tiny source slots explicit.
        native=after.resize((max(1,after.width//S),max(1,after.height//S)),Image.Resampling.LANCZOS)
        row.paste(native,(728,44+after.height),native);rows.append(row)
    assert sha(Path(m['pack'])/r['replacement'])==r['output_sha256']

out=R/'outputs/ui-resident-ko-001';pages=[]
for idx,start in enumerate(range(0,len(rows),6),1):
    selected=rows[start:start+6];canvas=Image.new('RGB',(1420,sum(x.height for x in selected)),'#283746');y=0
    for row in selected:canvas.paste(row,(0,y));y+=row.height
    p=out/f'consumed-labels-{idx}.png';canvas.save(p);pages.append(dict(path=str(p),sha256=sha(p)))

c=configparser.ConfigParser(interpolation=None);c.optionxform=str;c.read(Path(m['pack'])/'textures.ini',encoding='utf8')
assert len(c['hashes'])==717
assert len(set(x['key'] for x in m['records']))==6
assert all(len(k)==24 and k.startswith('00000000') for k in c['hashes'])
for path in c['hashes'].values():assert (Path(m['pack'])/path).is_file()
wording=json.loads((O/'translation-map.json').read_text('utf8'))
assert len(wording['entries'])==19 and wording['translator_model']=='Codex internal'
assert len({e['korean'] for e in wording['entries'] if e['source']=='INFORMATION'})==1
report=dict(schema='brs-resident-ko-static-review/v1',manifest_sha256=sha(O/'manifest.json'),asset_count=6,labels=19,protected_regions=checks,protected_region_count=len(checks),outside_owned_pixels='exact',source_mask_erased=True,persisted_composite_exact=True,consumer_pages=pages,source_target_function_exceptions=[{'source':'NEXT','modal':'다음','experience_panel':'다음 레벨','reason':'Different runtime meaning: advance message vs experience threshold'}],static_status='PASS',visual_review='pending',runtime_verified=False,limitation='Point-sampled SDO reconstruction does not verify runtime animation, tint, filtering, or code-generated consumers.')
(R/'qa/ui_resident_ko_001_review.json').write_bytes((json.dumps(report,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
print(json.dumps({'assets':6,'labels':19,'protected_regions':len(checks),'preview_pages':len(pages),'static_checks':'PASS'},ensure_ascii=False))
