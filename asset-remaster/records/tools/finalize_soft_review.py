"""Commit Codex visual decisions and verify exact source/output provenance."""
import json,hashlib,shutil,datetime
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path('P:/AI/Codex/projects/black-rock-shooter-hd-ui-fonts');C=Path('C:/Users/CadriacLord/Documents/Codex/2026-09-22/brs-hd-ui-fonts')
def read(n):return json.loads((R/n).read_text('utf8'))
def write(n,v):(R/n).write_text(json.dumps(v,ensure_ascii=False,indent=2),'utf8')
def sha(b):return hashlib.sha256(b).hexdigest()
cat=read('qa/battle_sr_catalog.json');groups={q['group_id']:q for q in cat['groups']}
v3=read('qa/local_sr_soft_alpha_v3.json');v4=read('qa/local_sr_linear_foliage_v4.json');p=read('qa/local_sr_soft_review_proposal_v4.json')
checked=[]
for row in v3['files']+v4['files']:
    src=Image.open(row['source']).convert('RGBA');assert sha(src.tobytes())==row['source_rgba_sha256']
    out=Path(row['output']);assert sha(out.read_bytes())==row['output_sha256'];im=Image.open(out).convert('RGBA');assert im.size==(src.width*8,src.height*8)
    if 'parent_neural' in row:assert sha(Path(row['parent_neural']).read_bytes())==row['parent_neural_sha256']
    for part in row.get('parts',[]):
        for key in ['input_rgb','input_alpha','rgb_native','alpha_native']:assert sha(Path(part[key]).read_bytes())==part[key+'_sha256']
    original=np.asarray(src);actual=np.asarray(im);support=np.asarray(src.getchannel('A').resize(im.size,Image.Resampling.BILINEAR))
    outside=int(np.count_nonzero(actual[:,:,3][support==0]))
    if row['group_id']!='BM039':assert outside==0
    checked.append({'group_id':row['group_id'],'output':row['output'],'sha256':row['output_sha256'],'size':list(im.size),'alpha_nonzero_outside_source_bilinear_support':outside,'geometry_exception':'Straight-edge source fit; alpha silhouette intentionally reconstructed. Source-scale IoU and residuals separately recorded.' if row['group_id']=='BM039' else None})
for row in v3['files']:
    gid=row['group_id'];pick=gid=='BM027' and row['model_id']=='photo' and row['prefilter_sigma']==1.
    parent=gid=='BM057' and row['model_id']=='photo' and row['prefilter_sigma']==.4
    reason=('Cloud facets reduced while keeping source cloud placement and density; selected after dark/light matte and 2x review.' if pick else
            'Foliage has suitable shapes but requires lower high-frequency contrast and independent WDN bark; used only as rework parent.' if parent else
            'Residual facets/gloss or excess softness; a better reviewed condition exists in this batch.')
    row['visual_review']={'reviewer':'Codex internal','status':'selected_for_game_review' if pick else 'rework_parent_only' if parent else 'not_selected','reason':reason,'evidence':[f'outputs/local_sr_{gid}_soft_v3.png','outputs/local_sr_soft_matte_review_v4.png']}
for row in v4['files']:
    pick=row['group_id']=='BM039';parent=row.get('detail_weight')==.6
    row['visual_review']={'reviewer':'Codex internal','status':'selected_for_game_review' if pick else 'rework_parent_only' if parent else 'not_selected','reason':'Straight source-fitted stripe edges remove waviness; source-scale mask IoU 0.9597, largest measured edge residual 1.2975 source pixels; runtime and repeat boundary still pending.' if pick else '60% residual detail retains more leaf texture; use with earlier WDN bark.' if parent else '35% residual detail is too soft for the selected candidate.','evidence':f"outputs/local_sr_{row['group_id']}_rework_v4.png"}
reasons={
 'BM027':'Premultiplied RGBA prefilter + local photo Real-ESRGAN RGB/alpha inference; source opacity restored. Cloud facets reduced. Dark/light matte and 2x display reviewed.',
 'BM039':'Source stripe geometry fitted independently per edge and antialiased; actual neural RGB reused. No new neural inference in geometric postprocessing.',
 'BM057':'Local photo foliage inference with 60% residual RGB detail; original separate bark atlas region uses prior WDN result. Alpha and atlas split preserved to their recorded parents.'}
for gid,out in p['proposed'].items():
    src=Image.open(groups[gid]['representative']['png']).convert('RGBA');im=Image.open(out).convert('RGBA');assert im.size==(src.width*8,src.height*8)
    if gid=='BM057':
        assert sha(Path(out).read_bytes())==p['tree_composite_sha256'];assert sha(Path(p['tree_bark_parent']).read_bytes())==p['tree_bark_parent_sha256']
        bark=Image.open(p['tree_bark_parent']).convert('RGBA');leaf=Image.open(p['tree_parent']['output']).convert('RGBA')
        assert np.array_equal(np.asarray(im)[:,384:],np.asarray(bark)[:,384:])
        assert np.array_equal(np.asarray(im)[:,:384],np.asarray(leaf)[:,:384])
        checked.append({'group_id':gid,'output':out,'sha256':sha(Path(out).read_bytes()),'size':list(im.size),'exact_parent_regions':{'leaf':[0,0,384,512],'bark':[384,0,512,512]}})
    previous=groups[gid].get('candidate');assert previous is None or previous.get('source_report')=='qa/local_sr_soft_review_v4.json'
    groups[gid]['candidate']={'source_report':'qa/local_sr_soft_review_v4.json','source_rgba_sha256':groups[gid]['rgba_sha256'],'output':out,'output_sha256':sha(Path(out).read_bytes()),'reason':reasons[gid],'status':'static_candidate_for_consumer_and_game_review','runtime_verified':False,'release_eligible':False}
summary=cat['processing_summary'];summary['battle_static_candidates']=sum(bool(g.get('candidate')) for g in cat['groups']);summary['battle_processed_without_accepted_candidate']=sum(g.get('local_sr_attempted',False) and not g.get('candidate') for g in cat['groups']);summary['latest_rework']='qa/local_sr_soft_review_v4.json'
summary['new_unique_originals_latest_rework']=0
assert summary['all_unique_originals_locally_processed']==54 and summary['battle_static_candidates']==50
p['visual_review']={'reviewer':'Codex internal','status':'static_candidates_only','evidence':['outputs/local_sr_soft_matte_review_v4.png','outputs/local_sr_BM039_rework_v4.png'],'runtime_verified':False}
report={'schema':'brs-soft-review/v4','reviewer':'Codex internal','selected':{gid:groups[gid]['candidate'] for gid in p['proposed']},'checked_outputs':checked,'new_neural_inference_passes':v3['new_neural_inference_passes'],'new_unique_originals':0,'processing_summary':summary,'remaining_processed_holds':[g['group_id'] for g in cat['groups'] if g.get('local_sr_attempted') and not g.get('candidate')],'limitations':['No runtime, UV, moving-alpha or tile-wrap acceptance.','BM039 alpha geometry is reconstructed, not source-pixel-identical; per-edge fits, clipped-edge extrapolations and mask IoU are in local_sr_linear_foliage_v4.json.','Source-scale consistency does not establish recovered true detail.','No user installation or final ZIP.']}
write('qa/local_sr_soft_alpha_v3.json',v3);write('qa/local_sr_linear_foliage_v4.json',v4);write('qa/local_sr_soft_review_proposal_v4.json',p);write('qa/local_sr_soft_review_v4.json',report);write('qa/battle_sr_catalog.json',cat)
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',21)
sheet=Image.new('RGB',(1060,1390),'#293440');d=ImageDraw.Draw(sheet)
d.text((14,8),'이전 로컬 결과 · 미채택',font=font,fill='white');d.text((544,8),'재작업 · 실제 게임 검수 후보',font=font,fill='white')
old=read('qa/local_sr_stage01_alpha_v1.json');old={q['group_id']:q for q in old['files'] if q['alpha_model_id']=='general-wdn'}
y=50
for gid,title in [('BM027','구름 · 각진 얼룩 완화'),('BM039','대각선 표식 · 직선 복원'),('BM057','나무 · 광택 완화')]:
    wh=(512,256 if gid!='BM057' else 512)
    for col,path in enumerate([old[gid]['output'],p['proposed'][gid]]):
        x=col*530+14;d.text((x,y),title,font=font,fill='white');im=Image.open(path).convert('RGBA').resize(wh,Image.Resampling.LANCZOS);bg=Image.new('RGB',wh,'#a7b4bc');bg.paste(im,(0,0),im);sheet.paste(bg,(x,y+38))
    y+=wh[1]+85
sheet=sheet.crop((0,0,1060,y));out=C/'outputs/로컬_업스케일_구름_나무_표식_재작업.png';sheet.save(out);shutil.copyfile(out,R/'outputs/local_sr_soft_before_after_v4.png')
shutil.copyfile(R/'outputs/local_sr_soft_matte_review_v4.png',C/'outputs/로컬_업스케일_투명도_검수.png')
note=C/'outputs/로컬_업스케일_진행.md';body=note.read_text('utf8');marker='## 2026-09-23 재작업 추가'
if marker not in body:body+='\n\n'+marker+'\n\n- 구름·나무 원본 2종에 실제 로컬 RGB/알파 추론 24회, 8개 조건을 비교했습니다. 같은 원본의 재작업이므로 고유 원본 누계는 54종입니다.\n- 구름·나무·대각선 표식 3종을 개선해 전투 정적 후보가 47종에서 50종으로 늘었습니다. 보류된 처리 원본은 BM019/BM036/BM056 3종입니다.\n- 대각선은 원본에서 경계를 측정해 복원한 것이며, 추가 AI 추론으로 세지 않습니다.\n- 검수창은 ISO 경로를 직접 전달해 실행했습니다. 창 캡처가 검게 나오고 화면 앞에 표시하려는 요청에 Windows 접근 거부가 발생해 실제 표시 검증은 보류했습니다. 별도 검수 프로세스는 종료하고 경로 설정을 복구했습니다.\n- 전체 게임 검증·다른 지역/적/이펙트·미관측 해시·폰트/조준 고정·최종 ZIP은 계속 남아 있습니다.\n'
note.write_text(body,'utf8')
print(json.dumps({'checked_outputs':len(checked),'summary':summary,'holds':report['remaining_processed_holds'],'comparison':str(out)},ensure_ascii=False))
