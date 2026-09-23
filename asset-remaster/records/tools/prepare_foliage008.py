from pathlib import Path
import json,hashlib,shutil
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(r'P:\AI\Codex\projects\black-rock-shooter-hd-ui-fonts');C=Path(__file__).resolve().parent
def read(p):return json.loads(Path(p).read_text('utf8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
last=read(R/'qa/field_foliage007_review.json');cp=R/'qa/field_sr_catalog.json';gp=R/'qa/architectural_geometry_contract.json'
assert sha(cp)==last['catalog_after_sha256'] and sha(gp)==last['geometry_contract_after_sha256']
local=read(R/'qa/field_foliage006_local.json');O=R/'outputs/field-foliage008';O.mkdir(exist_ok=False)
rep={'schema':'brs-field-foliage008-preparation/v1','previous_goal_turn_classification':'progress: four prior tree holds resolved using source-defined material reconstruction, seven frozen recipes verified','catalog_before_sha256':sha(cp),'geometry_contract_before_sha256':sha(gp),'files':[],'pages':[],'actual_new_local_passes':0,'actual_new_external_calls':0,'runtime_verified':False}
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',15);arrays={}
for gid in ['FM0301','FM0312','FM0318','FM0320']:
    p=next(q for q in local['prepared_sources'] if q['group_id']==gid)
    source=Image.open(p['source']).convert('RGBA');a=np.asarray(source);arrays[gid]=a
    assert hashlib.sha256(a.tobytes()).hexdigest()==p['source_rgba_sha256'] and sha(p['source_ptm'])==p['source_ptm_sha256']
    rec={k:p[k] for k in ['group_id','source','source_ptm','source_ptm_sha256','source_rgba_sha256']}
    rec.update(source_size=list(source.size),source_nonzero_alpha=int((a[:,:,3]>0).sum()),source_alpha_mean=float(a[:,:,3].mean()))
    if gid!='FM0318':
        dest=R/'workspace/gpt-trials'/(gid+'-foliage008-v1');dest.mkdir(exist_ok=False)
        ref=dest/'source-nearest8x.png';source.resize((source.width*8,source.height*8),Image.Resampling.NEAREST).save(ref)
        prompt=dest/'prompt.txt';shutil.copy2(C/(gid+'-foliage008-prompt.txt'),prompt)
        provenance={**rec,'reference':str(ref),'reference_sha256':sha(ref),'prompt':str(prompt),'prompt_sha256':sha(prompt),'source_protected_alpha':p['alpha'],'source_protected_alpha_sha256':p['alpha_sha256'],'tool':'built-in image_gen','model_id':'not exposed','status':'prepared','raw_generated_image_preserved':False}
        (dest/'provenance.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2),'utf8');rec['GPT_preparation']=str(dest/'provenance.json')
    page=Image.new('RGB',(1060,610),'#25313c');d=ImageDraw.Draw(page)
    for col,matte in enumerate(['#18222c','#dedede']):
        im=source.resize((512,round(512*source.height/source.width)),Image.Resampling.NEAREST);bg=Image.new('RGBA',im.size,matte);bg.alpha_composite(im);page.paste(bg.convert('RGB'),(col*530+9,60+(530-bg.height)//2));d.text((col*530+9,12),gid+' 원본 · 단순 확대',fill='white',font=font)
    pp=O/(gid+'-source.png');page.save(pp);rep['pages'].append({'path':str(pp),'sha256':sha(pp),'group_id':gid,'review_status':'pending'});rep['files'].append(rec)
a,b=arrays['FM0312'],arrays['FM0318'];mask=(a[:,:,3]>0)&(b[:,:,3]>0);x=a[:,:,:3][mask].reshape(-1).astype(float);y=b[:,:,:3][mask].reshape(-1).astype(float);slope,intercept=np.polyfit(x,y,1)
rep['312_to318_relationship']={'alpha_exact':bool(np.array_equal(a[:,:,3],b[:,:,3])),'common_opaque_pixels':int(mask.sum()),'RGB_exact_fraction_on_common':float(np.all(a[:,:,:3][mask]==b[:,:,:3][mask],axis=1).mean()),'RGB_scalar_affine_fit':{'slope':float(slope),'intercept':float(intercept),'rms':float(np.sqrt(np.mean((y-(x*slope+intercept))**2)))},'consumer_equivalence_proven':False}
q=R/'qa/field_foliage008_preparation.json';assert not q.exists();q.write_text(json.dumps(rep,ensure_ascii=False,indent=2),'utf8');print(json.dumps({'report':str(q),'source_relationship':rep['312_to318_relationship'],'files':rep['files']},ensure_ascii=False))
