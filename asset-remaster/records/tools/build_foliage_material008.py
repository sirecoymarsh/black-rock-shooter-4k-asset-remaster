from pathlib import Path
import sys,json,hashlib,shutil
sys.dont_write_bytecode=True
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from foliage_material008 import build
R=Path(r'P:\AI\Codex\projects\black-rock-shooter-hd-ui-fonts');C=Path(__file__).resolve().parent;O=R/'workspace/local-sr/field-foliage008';P=R/'outputs/field-foliage008';Q=R/'qa/field_foliage008_material_v1.json';assert not Q.exists();O.mkdir(exist_ok=False)
def read(p):return json.loads(Path(p).read_text('utf8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
raw=read(R/'qa/field_foliage008_gpt_raw.json');local=read(R/'qa/field_foliage006_local.json');prep=read(R/'qa/field_foliage008_preparation.json');prog=O/'foliage_material008_v1_frozen.py';shutil.copy2(C/'foliage_material008.py',prog);font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',15)
rep={'schema':'brs-field-foliage008-material/v1','program':str(prog),'program_sha256':sha(prog),'source_preparation_sha256':sha(R/'qa/field_foliage008_preparation.json'),'GPT_raw_report_sha256':sha(R/'qa/field_foliage008_gpt_raw.json'),'files':[],'pages':[],'new_local_passes':0,'new_external_calls':0,'new_unique_originals':0,'runtime_verified':False}
sources={p['group_id']:np.asarray(Image.open(p['source']).convert('RGBA')) for p in prep['files']}
def contrast(a):return float(a[:,:,:3].mean(2)[a[:,:,3]>=128].std())
gain318=float(np.clip(.85*contrast(sources['FM0318'])/contrast(sources['FM0312']),.45,1.05))
for gid,gain in [('FM0301',1.),('FM0312',.85),('FM0318',gain318),('FM0320',.85)]:
    src=next(p for p in prep['files'] if p['group_id']==gid);don=next(p for p in raw['files'] if p['group_id']==('FM0312' if gid=='FM0318' else gid));parent=next(p for p in local['files'] if p['id']==gid+'-photo');donor=np.asarray(Image.open(don['raw_generated_image']).convert('RGBA'));source=sources[gid]
    out,diag=build(source,donor,gain);op=O/(gid+'-source-palette-density-v1-8x.png');Image.fromarray(out).save(op)
    rec={**src,'id':gid+'-source-palette-density-v1','output':str(op),'output_sha256':sha(op),'GPT_donor':don['raw_generated_image'],'GPT_donor_sha256':don['raw_sha256'],'local_comparison':parent['output'],'local_comparison_sha256':parent['output_sha256'],'diagnostics':diag,'source_luma_std':contrast(source),'source312_luma_std':contrast(sources['FM0312']),'review_status':'pending','runtime_verified':False,'release_eligible':False};rep['files'].append(rec)
    detail=(12,8,44,40) if source.shape[1]==64 else (12,12,44,44)
    edge=(0,0,40,30) if source.shape[1]==64 else (75,0,120,30)
    for tag,box in [('whole',None),('detail',detail),('edge',edge)]:
        page=Image.new('RGB',(1050,810),'#25313c');d=ImageDraw.Draw(page)
        for row,(matte,mlabel) in enumerate([('#18222c','어두운 배경'),('#dedede','밝은 배경')]):
            for col,(path,title) in enumerate([(src['source'],'원본 · 단순 확대'),(parent['output'],'로컬 Photo'),(str(op),'재작화 · 색조와 밀도 보정')]):
                pic=Image.open(path).convert('RGBA')
                if box:pic=pic.crop(tuple(round(t*(pic.width/source.shape[1] if i%2==0 else pic.height/source.shape[0])) for i,t in enumerate(box)))
                scale=min(320/pic.width,340/pic.height);pic=pic.resize((round(pic.width*scale),round(pic.height*scale)),Image.Resampling.NEAREST if col==0 else Image.Resampling.LANCZOS);bg=Image.new('RGBA',pic.size,matte);bg.alpha_composite(pic);page.paste(bg.convert('RGB'),(col*350+(350-bg.width)//2,row*405+58+(340-bg.height)//2));d.text((col*350+8,row*405+8),gid+' '+title,font=font,fill='white');d.text((col*350+8,row*405+30),mlabel,font=font,fill='#c7d1da')
        pp=P/(gid+'-material-v1-'+tag+'.png');page.save(pp);rep['pages'].append({'path':str(pp),'sha256':sha(pp),'group_id':gid,'source_box':box,'review_status':'pending'})
    print('BUILT',gid,diag,flush=True)
Q.write_text(json.dumps(rep,ensure_ascii=False,indent=2,allow_nan=False),'utf8')
