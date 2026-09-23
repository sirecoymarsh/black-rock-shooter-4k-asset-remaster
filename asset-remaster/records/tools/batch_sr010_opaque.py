"""Reviewed region 5/6 material trials. Native CUDA 4x, then Lanczos 2x."""
import sys,json,time,gc
from pathlib import Path
import numpy as np,torch,spandrel
from PIL import Image,ImageDraw,ImageFont
import local_sr as sr
sys.stdout.reconfigure(encoding='utf8');torch.set_num_threads(4)
R=Path(__file__).resolve().parents[1]
O=R/'workspace/local-sr/stage0506-materials-v1';Q=R/'qa/local_sr010_inference.json'
if (R/'qa/local_sr010_review.json').exists():raise SystemExit('Finalized; use a new version.')
O.mkdir(parents=True,exist_ok=True)
cat=json.loads((R/'qa/battle_sr_catalog.json').read_text('utf8'));groups={g['group_id']:g for g in cat['groups']}
numbers=[201,202,203,209,210,211,212,213,215,218,226,227,232,233,236,237,238,239,240,241,243,244,251,253,254,255,256,267,268,279,281]
ids=[f'BM{n:03d}' for n in numbers]
notes={
200:'Four flat dark checker quadrants; protect sharp geometry, inspect repeat/consumer before treatment.',
201:'Dark broken floor with exposed checker patches; inspect square geometry and large cracks.',
202:'Small wall panel with luminous rectangle and lower mechanical details.',
203:'Opaque dark corner and narrow vertical panel over flat gray backing.',
204:'Broken bracket cutout with thin stem and curled ends.',205:'Broken frame cutout with narrow crossbar and detached-looking corner.',
206:'Paired angled beams and separate bottom fragments; alpha cutouts.',207:'Right-angle frame with very thin connecting strut.',208:'Long decorative column cutout with two broad nodes.',
209:'Checker patches and a horizontal checker strip surrounded by dark cracked material.',210:'Very low-contrast rectangular vertical panel bands.',211:'Repeated dark stone blocks and crossbands.',
212:'Broken angular metal panels over dark backing.',213:'Diagonal overlapping metal plates.',214:'Two narrow chains with oval links; preserve holes and link topology.',
215:'Horizontal broken angular strip over opaque black backing.',216:'Broken narrow frame with holes and long tapered stem.',217:'Paired bent strips with narrow interior gap.',
218:'Mechanical broken-panel atlas with thin horizontal grille and small white corner.',219:'Narrow architectural frame and broken lower node.',
220:'Repeated spiked structures above a separate curled strip; alpha-aware split treatment.',221:'Long narrow ornate cutout; small lattice requires protection.',222:'Tall irregular column cutout.',223:'Double-node column with panel divisions.',
224:'Faint diagonal chain with maximum alpha115; weak links must survive.',225:'Thin arch/column cutout with empty lower area.',
226:'Tall opaque atlas with mechanical strips and checker-floor section; native UV consumers unverified.',227:'Dark cracked panel with central opening-like shape.',228:'Multiple purple architectural strips and cutouts.',
229:'Nearly flat pale surface; no texture invention, consumer pending.',230:'Horizontal chain with oval links.',231:'8x8 white swatch; consumer pending, no need to invent texture.',
232:'Two adjacent wall/window blocks; high-contrast broken shapes on right need comparison, not semantic guesses.',233:'Pale rust-speckled wall.',236:'Muted green horizontal background above rubble; avoid invented horizon bands.',
234:'Fine repeated window frame with diagonal braces; cutouts and lines need alpha review.',235:'Small hanging broken structure with thin stems.',
237:'Pale cracked slab.',238:'Two rows of broken window panes; preserve straight dividers and pane remnants.',239:'Broken wall/window atlas with small high-contrast forms.',240:'Brown rubble and scattered debris.',
241:'Thin pale outlines on black geometric panel.',242:'Angular cutout frames.',243:'Opaque angular metal fragments and separate narrow post on dark backing.',244:'Dark floor with checker patches and large cracks.',
245:'Partly opaque rubble/building surface, alpha minimum225.',246:'Narrow tapered debris cutout.',247:'City skyline cutout with many small windows and thin roofs.',248:'Small debris cutouts and narrow dangling pieces.',
249:'Intricate silver mechanical fragment cutouts.',250:'Large silver mechanical/platform fragment atlas with alpha.',251:'Gray clustered rock cracks.',252:'Dithered circular effect with soft bright center and holes; density must be preserved.',
253:'Directional light cracks across gray rock.',254:'Pale vertical surface streaks.',255:'Tiny grayscale rough material; avoid faceting or artificial mesh.',256:'Four visually separated column/panel regions; processing partitions are not proof of native UVs.',
257:'Thin pale frame with broken upper shapes.',258:'Two chains with oval links.',259:'Sparse bright star-like points over opaque dark field; preserve points and density.',260:'Three large chain links in horizontal strip.',
261:'Two floating platform cutouts with semiopaque alpha.',262:'Scattered small rock cutouts.',263:'Broken arch fragments with fine internal holes.',264:'Tiny gray texture with near-opaque alpha minimum230.',
265:'Silver ornamental framework and central upright cutout.',266:'Silver mechanical strip/panel atlas with alpha.',267:'Silver-edged geometric panel atlas on dark backing.',268:'Gold vertical material grain.',
269:'Red/yellow checker surface with constant alpha204; protect square geometry and shading.',270:'Orange/yellow crossed luminous streaks and holes.',271:'Bright diagonal angular lines with soft outer glow.',
272:'Orange angular luminous shape with glow; treat geometry separately.',273:'Flat yellow/orange thin paths with hard cutouts.',274:'Flat angular yellow/orange emblem-like path; meaning unverified.',275:'Luminous chains and narrow lower paths.',
276:'Tiny soft gray near-opaque texture, alpha minimum214.',277:'Blue mottled sphere with circular alpha edge.',278:'Purple detached fragments with alpha.',279:'Dark and pale rocky materials occupy separate left/right halves.',
280:'Thin angular purple frame strip with many gaps.',281:'Pale vertical fractured slab.',282:'Pale broken diagonal wall and very thin horizontal rods.',283:'Small horizontal architectural finial with semitransparent edge.'}
source_review=json.loads((R/'qa/local_sr_stage0506_source_review.json').read_text('utf8'))
assert set(notes)==set(range(200,284)) and len(ids)==31
if source_review['visual_review']=='pending':
    source_review['visual_review']='Codex internal: source-01..10 all directly inspected'
    source_review['classifications']=[{'group_id':gid,'classification':'opaque material for local SR comparison' if gid in ids else 'separate alpha, geometry, or flat-source treatment pending','reason':notes[int(gid[2:])],'source_rgba_sha256':groups[gid]['rgba_sha256']} for gid in source_review['group_ids']]
    source_review['opaque_batch']='qa/local_sr010_inference.json'
    (R/'qa/local_sr_stage0506_source_review.json').write_text(json.dumps(source_review,ensure_ascii=False,indent=2),'utf8')
mr={m['name']:m for m in json.loads((R/'workspace/local-sr/models/models.json').read_text('utf8'))['records']}
def weights(name):
    m=mr[name];assert sr.sha(Path(m['path']).read_bytes())==m['sha256']
    w=torch.load(m['path'],map_location='cpu',weights_only=True);return w.get('params_ema',w.get('params',w))
wg=weights('realesr-general-x4v3.pth');ww=weights('realesr-general-wdn-x4v3.pth')
assert wg.keys()==ww.keys() and torch.cuda.is_available()
report=json.loads(Q.read_text('utf8')) if Q.exists() else {'schema':'brs-sr010-inference/v1','group_ids':ids,'source_review':'qa/local_sr_stage0506_source_review.json','iso_sha256':cat['iso_sha256'],'device':torch.cuda.get_device_name(0),'torch':torch.__version__,'spandrel':spandrel.__version__,'local_inference':True,'image_upload':False,'files':[],'runtime_verified':False,'release_eligible':False,'panel_basis':'Visible source regions only; native UV consumers remain unverified.'}
assert report['group_ids']==ids
done={(r['group_id'],r['denoise_strength']):r for r in report['files']}
splits={'BM256':[(0,0,32,32),(0,32,32,128),(32,0,64,32),(32,32,64,128)],'BM279':[(0,0,64,64),(64,0,128,64)]}
for dn in [0.,.5]:
    model=spandrel.ModelLoader().load_from_state_dict({k:dn*wg[k]+(1-dn)*ww[k] for k in wg}).cuda().eval();assert model.scale==4
    for gid in ids:
        g=groups[gid];src=Image.open(g['representative']['png']).convert('RGBA')
        assert src.getchannel('A').getextrema()==(255,255) and sr.sha(src.tobytes())==g['rgba_sha256']
        if (gid,dn) in done:
            row=done[(gid,dn)];assert row['source_rgba_sha256']==g['rgba_sha256'];assert sr.sha(Path(row['output']).read_bytes())==row['output_sha256'];continue
        assert not g.get('local_sr_attempted'),gid
        start=time.monotonic();out=Image.new('RGBA',(src.width*8,src.height*8));parts=[]
        coverage=np.zeros((src.height,src.width),np.uint8)
        for pi,box in enumerate(splits.get(gid,[(0,0,src.width,src.height)])):
            x0,y0,x1,y1=box;coverage[y0:y1,x0:x1]+=1;part=src.crop(box).convert('RGB')
            ip=O/f'{gid}-dn{dn}-p{pi}-input.png';part.save(ip)
            native=sr.infer_rgb(model,part);npth=O/f'{gid}-dn{dn}-p{pi}-neural4x.png';native.save(npth)
            a=np.asarray(native,dtype=np.float32);offset=np.asarray(part,dtype=np.float32).mean((0,1))-a.mean((0,1))
            v=Image.fromarray(np.rint(np.clip(a+offset,0,255)).astype('uint8')).resize((part.width*8,part.height*8),Image.Resampling.LANCZOS).convert('RGBA');v.putalpha(255);out.paste(v,(x0*8,y0*8))
            parts.append({'source_box':list(box),'input':str(ip),'input_sha256':sr.sha(ip.read_bytes()),'native':str(npth),'native_sha256':sr.sha(npth.read_bytes()),'mean_color_offset_rgb':offset.tolist()})
        assert np.all(coverage==1)
        p=O/f'{gid}-dn{dn}-8x.png';out.save(p)
        row={'group_id':gid,'source':g['representative']['png'],'source_rgba_sha256':g['rgba_sha256'],'denoise_strength':dn,'model_sources':[mr[n] for n in ['realesr-general-x4v3.pth','realesr-general-wdn-x4v3.pth']],'model_weights':[dn,1-dn],'precision':'float32','native_neural_scale':4,'post_scale':'Lanczos2x','parts':parts,'new_neural_passes':len(parts),'output':str(p),'output_sha256':sr.sha(p.read_bytes()),'output_size':list(out.size),'source_scale_metrics':sr.roundtrip_metrics(src,out),'alpha':'Opaque255 exact','seconds':time.monotonic()-start,'visual_review':'pending','runtime_verified':False,'release_eligible':False}
        report['files'].append(row);done[(gid,dn)]=row;Q.write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8');print('INFERRED',gid,dn,flush=True)
    del model;gc.collect();torch.cuda.empty_cache()
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18);directory=R/'outputs/sr010-review';directory.mkdir(exist_ok=True);pages=[]
for start in range(0,len(ids),3):
    batch=ids[start:start+3];s=Image.new('RGB',(1536,len(batch)*430+45),'#293440');d=ImageDraw.Draw(s)
    for j,label in enumerate(['원본 단순 확대','로컬 WDN','로컬 중간 노이즈 제거']):d.text((j*512+10,7),label,font=font,fill='white')
    for i,gid in enumerate(batch):
        src=Image.open(groups[gid]['representative']['png']).convert('RGBA');scale=min(488/src.width,365/src.height,8);size=(round(src.width*scale),round(src.height*scale))
        ims=[src]+[Image.open(done[(gid,dn)]['output']) for dn in [0.,.5]]
        for j,im in enumerate(ims):
            x=j*512+10;y=45+i*430;d.text((x,y),f'{gid} · 표시 {scale:.2f}배',font=font,fill='white')
            s.paste(im.convert('RGB').resize(size,Image.Resampling.NEAREST if j==0 else Image.Resampling.LANCZOS),(x,y+32))
    p=directory/f'review-{start//3+1:02d}.png';s.save(p);pages.append(str(p))
report['comparison_sheets']=pages;report['new_neural_passes']=sum(r['new_neural_passes'] for r in report['files'])
Q.write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8')
print(json.dumps({'originals':len(ids),'outputs':len(report['files']),'passes':report['new_neural_passes'],'pages':len(pages)}),flush=True)
