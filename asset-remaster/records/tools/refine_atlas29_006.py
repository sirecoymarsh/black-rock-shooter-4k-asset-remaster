"""Separate original one-pixel dark rim from the colored frame bevel; restore
small original upper/lower plate straps lost in the first reconstruction."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1];original=R/'tools/rebuild_atlas29_006.py';text=original.read_text('utf8')
text=text.replace('field_geometry006_atlas29_v1.json','field_geometry006_atlas29_v2.json').replace('frame-panel-v1','frame-panel-v2').replace("name+'-v1.png'","name+'-v2.png'")
old="outer=octagon(outerbox,chamfer);inner=octagon(innerbox,max(0,chamfer-.6) if chamfer else 0);poly(outer,[52,36,32],name+'-shadow');ring(outer,inner,base,name);glass.append"
new="outer=octagon(outerbox,chamfer);inner=octagon(innerbox,max(0,chamfer-.6) if chamfer else 0);middle=octagon([outerbox[0]+1,outerbox[1]+1,outerbox[2]-1,outerbox[3]-1],max(0,chamfer-.3) if chamfer else 0);poly(outer,[52,36,32],name+'-shadow');ring(middle,inner,base,name);glass.append"
assert old in text;text=text.replace(old,new)
text=text.replace("dm=np.repeat(np.repeat(detailmask,8,0),8,1)","\nfor a,b,c,d in [[11,45,25,49],[11,60,25,64]]:\n rgb=s[b:d,a:c,:3];valid=np.all(rgb==[172,147,118],axis=2)|np.all(rgb==[123,123,123],axis=2)|np.all(rgb==[152,152,151],axis=2);detailmask[b:d,a:c]|=valid\ndm=np.repeat(np.repeat(detailmask,8,0),8,1)")
frozen=R/'workspace/local-sr/field-geometry006/rebuild_atlas29_v2_frozen.py';frozen.write_text(text,'utf8');exec(compile(text,str(frozen),'exec'),{'__file__':str(original),'__name__':'__main__'})
p=R/'qa/field_geometry006_atlas29_v2.json';d=json.loads(p.read_text('utf8'));d['reconstruction_program']=str(frozen);d['reconstruction_program_sha256']=hashlib.sha256(frozen.read_bytes()).hexdigest();d['parent_report_sha256']=hashlib.sha256((R/'qa/field_geometry006_atlas29_v1.json').read_bytes()).hexdigest();d['refinement']='Outer source dark rim preserved separately from the thinner colored bevel. Original small plate straps restored by source palette; no new generative call.';p.write_text(json.dumps(d,ensure_ascii=False,indent=2),'utf8')
