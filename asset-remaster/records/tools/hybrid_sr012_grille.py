"""Keep useful local metal work; replace failed grid/fastener with authored vectors."""
import json,hashlib
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];Q=R/'qa/local_sr012_manual_hybrid.json'
if Q.exists():raise SystemExit('Existing manual hybrid; use a new revision.')
def sha(b):return hashlib.sha256(b).hexdigest()
q=json.loads((R/'qa/local_sr012_inference.json').read_text('utf8'));r=next(r for r in q['files'] if r['group_id']=='BM110' and r['model_id']=='wdn');v=json.loads((R/'qa/local_sr012_manual_grille.json').read_text('utf8'))['files'][0]
src=Image.open(r['source']).convert('RGBA');ai=Image.open(r['output']).convert('RGBA');manual=Image.open(v['raw_render']).convert('RGBA');assert sha(Path(r['output']).read_bytes())==r['output_sha256'] and sha(Path(v['raw_render']).read_bytes())==v['raw_render_sha256']
out=np.asarray(ai).copy();paint=np.asarray(manual);yy,xx=np.indices(out.shape[:2]);sx=(xx+.5)/8;sy=(yy+.5)/8
grid=(sx>=6)&(sx<32)&(sy>=6)&(sy<26);out[grid,:3]=paint[grid,:3]
# Preserve the authored central cross and the two original lower holes.
dist=np.hypot(sx-48,sy-15.7);center=np.clip((4.65-dist)/.35,0,1);center[dist<4.3]=1
out[:,:,:3]=np.rint(out[:,:,:3]*(1-center[:,:,None])+paint[:,:,:3]*center[:,:,None]).astype('uint8');assert np.array_equal(out[:,:,3],np.asarray(ai)[:,:,3]);assert np.array_equal(out[grid,:3],paint[grid,:3])
O=R/'workspace/manual-redraw/sr012';p=O/'BM110-codex-grid-and-fastener-v2.png';Image.fromarray(out).save(p);mask=O/'BM110-codex-redraw-mask-v2.png';Image.fromarray(np.rint(np.maximum(grid,center)*255).astype('uint8')).save(mask)
record={'id':'BM110-codex-grid-and-fastener-v2','group_id':'BM110','source':r['source'],'source_rgba_sha256':r['source_rgba_sha256'],'parent':r['output'],'parent_sha256':r['output_sha256'],'alpha_parent':r['output'],'alpha_parent_sha256':r['output_sha256'],'manual_parent':v['raw_render'],'manual_parent_sha256':v['raw_render_sha256'],'vector':v['vector'],'vector_sha256':v['vector_sha256'],'mask':str(mask),'mask_sha256':sha(mask.read_bytes()),'output':str(p),'output_sha256':sha(p.read_bytes()),'output_size':list(ai.size),'method':'Codex-authored vector grille interior and source-shaped central fastener over previously inferred local frame/outer circle; alpha exact to WDN parent','new_neural_passes':0,'visual_review':'pending','runtime_verified':False,'release_eligible':False,'grid_source_box':[6,6,32,26],'horizontal_slat_rows':v['horizontal_slat_source_rows'],'vertical_slat_columns':v['vertical_slat_source_columns'],'center_source_xy':[48,15.7],'center_radius_full':4.3,'center_radius_zero':4.65,'exterior_not_manual_redraw':True}
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18);s=Image.new('RGB',(1596,660),'#293440');d=ImageDraw.Draw(s)
for i,bgc in enumerate(['#111111','#eeeeee']):
    for j,(im,label) in enumerate([(src,'원본 단순 확대'),(ai,'초기 로컬 AI'),(Image.fromarray(out),'격자·중심부 직접 재구성')]):
        x=j*532+8;y=i*330+8;d.text((x,y),label,font=font,fill='white');im=im.resize((512,256),Image.Resampling.NEAREST if j==0 else Image.Resampling.LANCZOS);bg=Image.new('RGB',im.size,bgc);bg.paste(im,(0,0),im);s.paste(bg,(x,y+34))
sheet=R/'outputs/sr012_manual_hybrid_BM110.png';s.save(sheet)
Q.write_text(json.dumps({'schema':'brs-sr012-manual-hybrid/v1','files':[record],'comparison_sheets':[str(sheet)],'new_neural_passes':0,'runtime_verified':False,'release_eligible':False},ensure_ascii=False,indent=2),'utf8')
# Full source facades for the next independently authored redraw.
b=next(f for f in q['files'] if f['group_id']=='BM087');bs=Image.open(b['source']).convert('RGBA').crop((0,0,128,76)).resize((1024,608),Image.Resampling.NEAREST);bg=Image.new('RGB',bs.size,'#72808b');bg.paste(bs,(0,0),bs);bp=R/'outputs/sr012_BM087_facade_source.png';bg.save(bp)
print(json.dumps({'manual_hybrid':str(p),'next_source':str(bp)}))
