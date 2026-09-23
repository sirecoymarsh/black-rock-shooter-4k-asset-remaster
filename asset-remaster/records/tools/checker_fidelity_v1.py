"""Protect authored checker geometry; infer only BM221 surrounding material."""
import copy,hashlib,json,shutil,sys,time
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter,distance_transform_edt
from PIL import Image,ImageDraw,ImageFont
import local_sr as sr
sys.stdout.reconfigure(encoding='utf8')
R=Path(__file__).resolve().parents[1];O=R/'workspace/local-sr/checker-fidelity-v1';O.mkdir(parents=True,exist_ok=True)
Q=R/'qa/checker_fidelity_v1.json'
if Q.exists():raise SystemExit('Existing experiment; create a new revision.')
def read(p):return json.loads((R/p).read_text('utf8'))
def sha(b):return hashlib.sha256(b).hexdigest()
cat=read('qa/battle_sr_catalog.json');groups={g['group_id']:g for g in cat['groups']}
backup=R/'qa/backups/before-checker-fidelity-v1';backup.mkdir(parents=True,exist_ok=False)
shutil.copyfile(R/'qa/battle_sr_catalog.json',backup/'battle_sr_catalog.json')
old=copy.deepcopy(groups['BM221']['candidate']);assert old and len([g for g in groups.values() if g.get('candidate')])==230
groups['BM221']['candidate']=None
groups['BM221']['superseded_candidates']=groups['BM221'].get('superseded_candidates',[])+[{'candidate':old,'reason':'User identified checker fidelity as core game design; softening the pattern is not an acceptable substitute for crisp cell preservation.'}]
groups['BM221']['review_hold_reason']='Checker cell count, colors and crisp boundaries must be protected; prior filtered-guided result too soft.'
cat['processing_summary'].update(battle_static_candidates=229,battle_processed_without_accepted_candidate=15)
(R/'qa/battle_sr_catalog.json').write_text(json.dumps(cat,ensure_ascii=False,indent=2),'utf8')
policy={'basis':'User clarified that checkerboard is a core game design element.','protected_features':['cell count','cell positions and phase','cell boundaries','authored colors and shading','clipping geometry and alpha'],'rules':['Do not replace checks with mesh, embossed holes or invented texture.','Do not accept blur as a checker reconstruction.','Separate protected design layers from neural material inference.'],'review_queue':['BM175','BM200','BM201','BM209','BM221','BM226','BM244','BM269']}
(R/'qa/checker_design_contract.json').write_text(json.dumps(policy,ensure_ascii=False,indent=2),'utf8')
report={'schema':'brs-checker-fidelity/v1','review_status':'pending visual review','revoked_candidate':old,'design_contract':policy,'files':[],'runtime_verified':False,'release_eligible':False,'local_image_upload':False}
# Regular flat checker tiles: resample shading independently inside each exact cell.
for gid,pitch in [('BM200',16),('BM269',8)]:
    g=groups[gid];src=Image.open(g['representative']['png']).convert('RGBA');a=np.asarray(src);assert sha(src.tobytes())==g['rgba_sha256']
    yy,xx=np.indices(a.shape[:2]);parity=((xx//pitch+yy//pitch)%2).astype(np.uint8)
    actual=(a[:,:,0]>=70).astype(np.uint8) if gid=='BM200' else (a[:,:,0]!=255).astype(np.uint8)
    assert np.array_equal(actual,parity)
    out=Image.new('RGBA',(src.width*8,src.height*8));cells=[]
    for y in range(0,src.height,pitch):
        for x in range(0,src.width,pitch):
            box=(x,y,x+pitch,y+pitch);part=src.crop(box);tile=part.convert('RGB').resize((pitch*8,pitch*8),Image.Resampling.BILINEAR);tile.putalpha(part.getchannel('A').resize(tile.size,Image.Resampling.NEAREST));out.paste(tile,(x*8,y*8));cells.append({'source_box':box,'output_box':tuple(v*8 for v in box),'parity':int(parity[y,x])})
    b=np.asarray(out);expected=np.repeat(np.repeat(parity,8,0),8,1)
    got=(b[:,:,0]>=70).astype(np.uint8) if gid=='BM200' else (b[:,:,0]!=255).astype(np.uint8)
    assert np.array_equal(got,expected) and out.getchannel('A').tobytes()==src.getchannel('A').resize(out.size,Image.Resampling.NEAREST).tobytes()
    p=O/f'{gid}-cell-preserved8x.png';out.save(p)
    report['files'].append({'id':gid+'-cell-preserved','group_id':gid,'source':g['representative']['png'],'source_rgba_sha256':g['rgba_sha256'],'output':str(p),'output_sha256':sha(p.read_bytes()),'output_size':list(out.size),'method':'Exact cell geometry with independent bilinear shading inside each cell; no neural inference or newly invented texture','new_neural_passes':0,'cell_pitch_source':pitch,'cells':cells,'checker_class_mask_exact_to_source_nearest8x':True,'alpha_exact_to_source_nearest8x':True,'visual_review':'pending','runtime_verified':False,'release_eligible':False})
# BM221: remove checker colors before neural material inference, then restore the authored design exactly.
g=groups['BM221'];src=Image.open(g['representative']['png']).convert('RGBA');a=np.asarray(src);assert sha(src.tobytes())==g['rgba_sha256']
green=np.array([98,125,103,255],np.uint8);pink=np.array([218,177,186,255],np.uint8)
mask=np.all(a==green,2)|np.all(a==pink,2);assert int(mask.sum())==614
mp=O/'BM221-protected-checker-mask.png';Image.fromarray(mask.astype('uint8')*255).save(mp)
clean=a.copy();clean[mask,:3]=[158,151,144]
cp=O/'BM221-checker-removed-input.png';Image.fromarray(clean).save(cp)
w=clean[:,:,3:4].astype(np.float32)/255.;cov=gaussian_filter(w,(.25,.25,0),mode='nearest');rgb=gaussian_filter(clean[:,:,:3].astype(np.float32)*w,(.25,.25,0),mode='nearest')/np.maximum(cov,1e-6);vis=cov[:,:,0]>1e-6
near=distance_transform_edt(~vis,return_distances=False,return_indices=True);rgb[~vis]=rgb[near[0][~vis],near[1][~vis]]
inp=Image.fromarray(np.rint(np.clip(rgb,0,255)).astype('uint8'));ip=O/'BM221-frame-rgb-input.png';inp.save(ip)
nn=src.resize((src.width*8,src.height*8),Image.Resampling.NEAREST);m8=np.repeat(np.repeat(mask,8,0),8,1)
models={m['name']:m for m in read('workspace/local-sr/models/models.json')['records']}
for mid,name in [('wdn','realesr-general-wdn-x4v3.pth'),('photo','RealESRGAN_x4plus.pth')]:
    m=models[name];model=sr.load_model(Path(m['path']),m['sha256']);t=time.monotonic();native=sr.infer_rgb(model,inp);npth=O/f'BM221-frame-{mid}-native4x.png';native.save(npth);out=native.resize(nn.size,Image.Resampling.LANCZOS).convert('RGBA');out.putalpha(src.getchannel('A').resize(nn.size,Image.Resampling.BILINEAR))
    b=np.asarray(out).copy();b[m8]=np.asarray(nn)[m8];out=Image.fromarray(b);p=O/f'BM221-frame-{mid}-protected8x.png';out.save(p)
    assert np.array_equal(b[m8],np.asarray(nn)[m8])
    reference_alpha=np.asarray(src.getchannel('A').resize(nn.size,Image.Resampling.BILINEAR));assert np.all(b[:,:,3][reference_alpha==0]==0)
    report['files'].append({'id':'BM221-'+mid+'-protected','group_id':'BM221','source':g['representative']['png'],'source_rgba_sha256':g['rgba_sha256'],'model':m,'input':str(ip),'input_sha256':sha(ip.read_bytes()),'cleanplate':str(cp),'cleanplate_sha256':sha(cp.read_bytes()),'mask':str(mp),'mask_sha256':sha(mp.read_bytes()),'protected_source_pixels':int(mask.sum()),'protected_output_pixels':int(m8.sum()),'native':str(npth),'native_sha256':sha(npth.read_bytes()),'output':str(p),'output_sha256':sha(p.read_bytes()),'output_size':list(out.size),'new_neural_passes':1,'native_neural_scale':4,'post_scale':'Lanczos2x for frame; nearest8x only for exact protected checker layer','method':'Local neural inference on checker-removed material; protected checker pixels restored byte-exactly; source bilinear alpha with protected core alpha255','protected_rgba_exact_to_source_nearest8x':True,'seconds':time.monotonic()-t,'visual_review':'pending','runtime_verified':False,'release_eligible':False})
    del model
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17);pages=[]
for gid in ['BM200','BM269','BM221']:
    src=Image.open(groups[gid]['representative']['png']).convert('RGBA');rows=[r for r in report['files'] if r['group_id']==gid]
    ims=[(src,'원본 단순 확대')]
    if gid=='BM221':ims.append((Image.open(old['output']).convert('RGBA'),'이전 후보 · 흐림으로 보류'))
    ims += [(Image.open(r['output']).convert('RGBA'),r['id']) for r in rows]
    box=(0,32,32,96) if gid=='BM221' else (0,0,src.width,src.height);scale=8;wh=((box[2]-box[0])*scale,(box[3]-box[1])*scale)
    sheet=Image.new('RGB',(len(ims)*370,1160 if gid=='BM221' else 670),'#293440');d=ImageDraw.Draw(sheet)
    for i,bgcolor in enumerate(['#111111','#eeeeee']):
        for j,(im,label) in enumerate(ims):
            x=j*370+10;y=i*(580 if gid=='BM221' else 335)+8;d.text((x,y),label,font=font,fill='white');im=im.crop(box if j==0 else tuple(v*8 for v in box)).resize(wh,Image.Resampling.NEAREST if j==0 else Image.Resampling.LANCZOS);bg=Image.new('RGB',wh,bgcolor);bg.paste(im,(0,0),im);sheet.paste(bg,(x,y+35))
    p=R/f'outputs/checker_fidelity_{gid}.png';sheet.save(p);pages.append(str(p))
report['comparison_sheets']=pages;report['new_neural_passes']=2
Q.write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8')
with (R/'PROGRESS.md').open('a',encoding='utf8') as f:f.write('\n\n### 체크판 디자인 보존 기준 강화 — 사용자 지적 반영\n- 체크판은게임핵심디자인이며blur로왜곡을가리는것을채택하지않는다. BM221기존filtered-guided후보취소/원본파일보존,현재전투정적후보229/보류15. qa/checker_design_contract.json. BM175/200/201/209/221/226/244/269재검수대상.\n- BM221원본핑크/그린614픽셀은정확RGBA보호층으로분리,체크를제거한바탕에만WDN/Photo2pass. BM200은2x2칸/BM269는4x4칸위치·색군·alpha고정,칸내명암만bilinear확대. 이두건은AI추론으로세지않음. qa/checker_fidelity_v1.json 시각검수대기/미통합.\n- 병행SR012신규12원본24결과46pass완료/미검수·미통합. Field v2는79소형SC확장,기존1630텍스처·576FM그룹보존,새텍스처0. 작은묶음내새미지원구획이추가발견되어실패223/미분류833. 전체목표active.\n')
print(json.dumps({'new_neural_passes':2,'outputs':len(report['files']),'checker_pixels':614,'review':'pending','candidate_revoked':'BM221'}))
