"""Finalize the reviewed SR009 batch; no emulator, routing or installation changes."""
import copy
import hashlib
import json
import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

R=Path(__file__).resolve().parents[1]
C=Path('C:/Users/CadriacLord/Documents/Codex/2026-09-22/brs-hd-ui-fonts')
FINAL='qa/local_sr009_review.json'
if (R/FINAL).exists():
    raise SystemExit('Already finalized; create a new revision instead.')

def read(p): return json.loads((R/p).read_text('utf8'))
def sha(b): return hashlib.sha256(b).hexdigest()
def check(p,h):
    assert sha(Path(p).read_bytes())==h, str(p)
def write(p,obj):
    p=R/p;temp=p.with_suffix(p.suffix+'.staging')
    temp.write_text(json.dumps(obj,ensure_ascii=False,indent=2),'utf8');temp.replace(p)

cat=read('qa/battle_sr_catalog.json')
groups={g['group_id']:g for g in cat['groups']}
prior={gid:copy.deepcopy(g['candidate']) for gid,g in groups.items() if g.get('candidate')}
assert len(prior)==137 and len(groups)==284
sky_before=copy.deepcopy(groups['BM284'])
failures_before=copy.deepcopy(cat['source_decode_failures'])
assert len(failures_before)==3
q=read('qa/local_sr009_inference.json')
retry=read('qa/local_sr009_rework.json')
late=read('qa/local_sr009_bm196_rework.json')
proposed=read('qa/local_sr009_proposed_review.json')
assert len(q['files'])==48 and len(retry['files'])==15 and len(late['files'])==3
assert len(set(q['group_ids']))==24
assert not any(groups[g].get('local_sr_attempted') for g in q['group_ids'])
assert not any(g in prior for g in q['group_ids'])
reasons={
 'BM132':'Photo retains broad snow ridges with less gritty texture than WDN.',
 'BM135':'Photo retains spires and cutouts, with calmer snow texture; inferred planes remain subject to game review.',
 'BM136':'WDN retains large cutouts and rods in the panoramic source. Two enlarged crops were inspected; surface cracks are inferred and not original HD evidence.',
 'BM137':'WDN is less heavily outlined than Photo; three source regions were processed separately. This partition is not proof of native UV consumers.',
 'BM138':'Photo reduces exaggerated ground scratches while retaining rods and gaps.',
 'BM139':'Filtered-guided rework restores coarse source color islands and suppresses artificial grooves/grain. Initial WDN and Photo were not selected.',
 'BM140':'WDN retains thin rods and narrow cutouts in the two separately processed source rows.',
 'BM141':'WDN retains continuous thin rods on dark and light mattes; row partition is not native UV proof.',
 'BM142':'WDN retains major folded metal shapes and cutouts; two source halves were isolated during processing.',
 'BM143':'WDN retains the small panel form more closely than Photo, which rounds and simplifies it.',
 'BM145':'All tested conditions round/emboss the black-yellow paint graphic and alter the small central dark chip. Flat graphic reconstruction is still needed; semantic role remains unknown.',
 'BM146':'Filtered-guided rework reduces invented central seams and gloss while retaining the diamond grid and cutouts; softer than initial output.',
 'BM147':'Tiny black-white emblems change or acquire invented strokes. Identify and protect emblem regions before accepting a remaster.',
 'BM153':'WDN retains the snow-covered architectural piece without the stronger crack interpretation in Photo.',
 'BM154':'WDN retains the snow mass, broken opening and underlying structure on both mattes.',
 'BM155':'WDN retains the pointed architectural silhouette and middle collar on both mattes.',
 'BM171':'Photo smooths the gold mesh while retaining visible lattice intersections and gaps on both mattes.',
 'BM172':'Filtered-guided rework removes much of the invented raised/folded metal appearance and retains holes and narrow strips.',
 'BM183':'WDN retains the curved frame and straight window bars on both mattes.',
 'BM195':'Filtered-guided rework suppresses leaf-like texture invented by the initial models and restores diffuse source patches.',
 'BM196':'Final light-matte review rejected initial WDN because it invented branching cracks. Additional filtered-guided local rework suppresses the crack network and restores soft source density; both mattes were inspected.',
 'BM197':'Photo retains soft cloud density with fewer gritty holes than WDN.',
 'BM198':'Photo retains a soft low-contrast wash; WDN adds stronger grain.',
 'BM199':'WDN retains the dark soft gradient without the stronger grain in Photo.'
}
selected_paths={g:v['output'] for g,v in proposed['selected'].items()}
changed=next(x for x in late['files'] if x['id']=='BM196-filtered-guided')
selected_paths['BM196']=changed['output']
assert len(selected_paths)==22 and set(q['group_ids'])-set(selected_paths)=={'BM145','BM147'}
selected={};checked=[];verified_models=set();references={};pass_count=0
reports=[('qa/local_sr009_inference.json',q),('qa/local_sr009_rework.json',retry),('qa/local_sr009_bm196_rework.json',late)]

for report_name,report in reports:
    recorded_passes=0
    for row in report['files']:
        gid=row['group_id'];g=groups[gid]
        src=Image.open(row['source']).convert('RGBA')
        assert src.size==(g['width'],g['height'])
        assert sha(src.tobytes())==g['rgba_sha256']==row['source_rgba_sha256']
        check(g['representative']['source'],g['representative']['source_sha256'])
        m=row['model'];pair=(m['path'],m['sha256'])
        if pair not in verified_models:check(*pair);verified_models.add(pair)
        check(row['output'],row['output_sha256'])
        out=Image.open(row['output']).convert('RGBA')
        assert out.size==(src.width*8,src.height*8)==tuple(row['output_size'])
        a=np.asarray(out.getchannel('A'))
        actual_passes=0
        if report is q:
            coverage=np.zeros((src.height,src.width),np.uint8)
            reference=Image.new('L',out.size)
            for part in row['parts']:
                x0,y0,x1,y1=part['source_box']
                assert 0<=x0<x1<=src.width and 0<=y0<y1<=src.height
                coverage[y0:y1,x0:x1]+=1
                size=(x1-x0,y1-y0);box=(x0,y0,x1,y1)
                for key in ['input_rgb','input_alpha','rgb_native','alpha_native']:
                    if key not in part:continue
                    check(part[key],part[key+'_sha256'])
                    im=Image.open(part[key]);scale=4 if 'native' in key else 1
                    assert im.size==(size[0]*scale,size[1]*scale)
                    if 'native' in key:actual_passes+=1
                reference.paste(src.crop(box).getchannel('A').resize((size[0]*8,size[1]*8),Image.Resampling.BILINEAR),(x0*8,y0*8))
            assert np.all(coverage==1)
            check(row['reference_alpha'],row['reference_alpha_sha256'])
            assert reference.tobytes()==Image.open(row['reference_alpha']).convert('L').tobytes()
            lin=np.asarray(reference)
            assert np.all(a[lin==0]==0) and np.all(a[lin==255]==255)
            references[(gid,row['model_id'])]=row
            original=np.asarray(src.getchannel('A'))
            down=np.asarray(out.getchannel('A').resize(src.size,Image.Resampling.LANCZOS))
            loss=int(((original>=16)&(down<8)).sum())
            gt=original>=128;pred=down>=128;union=(gt|pred).sum()
            metrics={'mass_ratio':float(a.mean()/original.mean()),'source_threshold128_iou':float((gt&pred).sum()/union) if union else 1.,'source_ge16_reduced_below8':loss,'outside_panel_bilinear_support':0}
            for key,val in metrics.items():assert abs(val-row['alpha_metrics'][key])<1e-12,(gid,key)
            assert loss==0
            alpha_evidence={'panel_bilinear_reconstructed':True,'zero_and_solid_support_verified':True,**metrics}
        else:
            for key in ['alpha_parent','parent','input','native']:
                if key in row:check(row[key],row[key+'_sha256'])
            parent=Image.open(row['alpha_parent']).convert('RGBA')
            assert out.getchannel('A').tobytes()==parent.getchannel('A').tobytes()
            if 'native' in row:
                assert Image.open(row['native']).size==(src.width*4,src.height*4)
                assert Image.open(row['input']).size==src.size
                actual_passes=1
            assert row['alpha_parent']==references[(gid,'wdn')]['output']
            alpha_evidence={'alpha_exact_to_initial_wdn_parent':True,'original_source_alpha_byte_exact':False}
        assert actual_passes==row['new_neural_passes']
        recorded_passes+=actual_passes
        pick=row['output']==selected_paths.get(gid)
        reason=reasons[gid]
        if not pick and gid not in {'BM145','BM147'}:reason='Alternate result not selected. '+reason
        evidence=list(report['comparison_sheets'])
        if gid=='BM196':evidence.append(str(R/'outputs/sr009-mattes/BM196-rework-mattes.png'))
        row['visual_review']={'reviewer':'Codex internal','status':'selected_for_game_review' if pick else 'held_rework_required' if gid in {'BM145','BM147'} else 'not_selected','reason':reason,'evidence':evidence}
        checked.append({'group_id':gid,'output':row['output'],'output_sha256':row['output_sha256'],'source_ptm_and_rgba_verified':True,'model_input_native_parent_hashes_verified':True,'size_8x_verified':True,'alpha_checks':alpha_evidence,'new_neural_passes':actual_passes})
        if pick:
            assert gid not in selected
            selected[gid]={'source_report':report_name,'source_rgba_sha256':g['rgba_sha256'],'output':row['output'],'output_sha256':row['output_sha256'],'reason':reasons[gid],'status':'static_candidate_for_consumer_and_game_review','runtime_verified':False,'release_eligible':False}
    assert recorded_passes==report['new_neural_passes']
    pass_count+=recorded_passes
assert len(checked)==66 and pass_count==120 and len(selected)==22

mapped={g['group_id'] for g in groups.values() if any(b['source_rgba_sha256']==g['rgba_sha256'] and b['size']==[g['width'],g['height']] for b in read('qa/battle_map_runtime_links.json')['bindings'])}
assert not set(q['group_ids'])&mapped
pack=read('qa/local_sr_observed_review_pack_v2.json');packpath=Path(pack['path'])
check(packpath/'textures.ini',pack['textures_ini_sha256'])
assert len(pack['keys'])==20
assert {p.relative_to(packpath).as_posix() for p in packpath.rglob('*.png')}==set(pack['keys'].values())
pack_population={str(p.relative_to(packpath)):sha(p.read_bytes()) for p in packpath.rglob('*') if p.is_file()}
for b in pack['battle_binding_evidence']:check(packpath/pack['keys'][b['key']],b['output_sha256'])

for gid in q['group_ids']:
    groups[gid]['local_sr_attempted']=True;groups[gid]['candidate']=selected.get(gid)
    if gid not in selected:groups[gid]['review_hold_reason']=reasons[gid]
for gid,v in prior.items():assert groups[gid]['candidate']==v
assert groups['BM284']==sky_before and cat['source_decode_failures']==failures_before
pcount=sum(bool(g.get('local_sr_attempted')) for g in groups.values())
ccount=sum(bool(g.get('candidate')) for g in groups.values())
assert pcount==171 and ccount==159
summary=cat['processing_summary']
summary.update(battle_groups_locally_processed=pcount,battle_static_candidates=ccount,battle_processed_without_accepted_candidate=pcount-ccount,battle_groups_not_yet_processed=len(groups)-pcount,all_unique_originals_locally_processed=pcount+1,latest_rework=FINAL,new_unique_originals_latest_rework=24,checked_output_records_latest_rework=66,new_unique_originals_LOCAL_SR_009=24,neural_passes_LOCAL_SR_009=120)
proposed['selected']['BM196']={'output':changed['output'],'output_sha256':changed['output_sha256'],'model_id':None,'id':changed['id']}
proposed['review_state']='Final source/model/rework and dark/light matte inspection completed; runtime unverified'
proposed['matte_pages'].append(str(R/'outputs/sr009-mattes/BM196-rework-mattes.png'))
proposed['superseded_matte_choices']={'matte-07.png BM196':'Initial WDN rejected after light-matte inspection; replaced by BM196-filtered-guided.'}
evidence_paths=sorted(set(sum((rep['comparison_sheets'] for _,rep in reports),[])+proposed['matte_pages']))
evidence=[{'path':p,'sha256':sha(Path(p).read_bytes()),'reviewed_by':'Codex internal'} for p in evidence_paths]
source189={'image':str(R/'outputs/BM189_source_inspection.png'),'sha256':sha((R/'outputs/BM189_source_inspection.png').read_bytes()),'review':'Left-side stacked dark markings and right pointed emblem-like outline are visible. No reliable text reading or semantic role established. Protect/identify before remastering. Contrast-adjusted view is diagnostic only.'}
report={'schema':'brs-local-sr-review/v9','batch':'LOCAL-SR-009','selected':selected,'new_holds':{gid:reasons[gid] for gid in ['BM145','BM147']},'checked_outputs':checked,'new_unique_originals':24,'new_actual_local_neural_passes':120,'prior_candidates_preserved':137,'processing_summary':copy.deepcopy(summary),'review_evidence':evidence,'source_BM189_review':source189,'new_sources_observed_keys':0,'pack_unchanged_keys':20,'pack_file_hashes':pack_population,'local_inference':True,'image_upload_this_batch':False,'runtime_verified':False,'release_eligible':False,'limitations':['Bilinear zero/solid alpha support and one downsample threshold test are not proof of all geometry or native blending.','Panel partition is based on visible source separation, not verified native material/UV consumption.','Rework alpha is exact to the initial neural/bilinear trial, not the original source bytes.','Full game includes assets beyond this battle-map denominator.'],'scripts':{p:sha((R/'tools'/p).read_bytes()) for p in ['batch_sr009_alpha.py','rework_sr009.py','rework_sr009_bm196.py','review_sr009_bm196.py','finalize_sr009.py']}}

# Make the user-facing source/candidate plate before persisting the reviewed catalog.
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',20)
sheet=Image.new('RGB',(1080,1590),'#293440');d=ImageDraw.Draw(sheet)
for j,label in enumerate(['원본 단순 확대','로컬 AI 처리 · 게임 검수 전']):d.text((j*540+12,10),label,font=font,fill='white')
for i,gid in enumerate(['BM138','BM171','BM172','BM196']):
    src=Image.open(groups[gid]['representative']['png']).convert('RGBA');out=Image.open(selected[gid]['output']).convert('RGBA')
    scale=min(510/src.width,310/src.height,8);wh=(round(src.width*scale),round(src.height*scale))
    for j,im in enumerate([src,out]):
        x=j*540+12;y=50+i*385;d.text((x,y),gid+f' · 표시 {scale:.2f}배',font=font,fill='white')
        im=im.resize(wh,Image.Resampling.NEAREST if j==0 else Image.Resampling.LANCZOS)
        bg=Image.new('RGB',wh,'#eeeeee');bg.paste(im,(0,0),im);sheet.paste(bg,(x,y+35))
sheet.save(R/'outputs/local_sr009_selected.png')
shutil.copyfile(R/'outputs/local_sr009_selected.png',C/'outputs/로컬_업스케일_투명재질_검수.png')
shutil.copyfile(R/'outputs/sr009-mattes/BM196-rework-mattes.png',C/'outputs/로컬_업스케일_효과_재작업.png')
backup=R/'qa/backups/before-sr009-finalize';backup.mkdir(parents=True,exist_ok=False)
to_save=[*reports,('qa/local_sr009_proposed_review.json',proposed),('qa/battle_sr_catalog.json',cat)]
for name,_ in to_save:shutil.copyfile(R/name,backup/Path(name).name)
for name,obj in to_save:write(name,obj)
write(FINAL,report)
note=f'''# 로컬 업스케일 진행 — LOCAL-SR-009

- 실제 로컬 GPU 추론을 거친 고유 원본 **172종**: 타이틀 1 + 전투재질 171.
- 전투맵 284종 중 정적 검수 후보 **159종**, 처리 후 보류 **12종**, 미처리 **113종**입니다. 게임 전체 완료율은 아닙니다.
- 이번 신규 원본 24종은 두 모델 비교와 재작업을 합쳐 **66개 결과·실제 로컬 추론 120회**를 검사했습니다. 22종을 게임 검수 후보로 골랐고, 작은 검정·노랑 표식과 엠블럼이 변형된 2종은 보류했습니다.
- 밝은 배경에서 발견한 효과의 갈라진 무늬는 추가 로컬 재처리와 원본 명암 반영으로 줄였습니다. 나머지 재작업에서도 과한 홈·광택·입체감·잎 모양을 줄였습니다.
- AI 모델은 본래 4배를 처리하고 보간으로 2배 더 키워 최종 8배 크기를 만듭니다. 원본 명암 혼합과 투명도 보정은 후처리이며 추가 AI 추론으로 세지 않습니다.
- 이번 배치는 로컬 RTX 5080에서 처리했고 외부 이미지 업로드는 없습니다. 이전 GPT BM162 시도 1회는 외부 이미지 편집이었고 미채택입니다.
- 새 원본 24종에는 아직 정확한 게임 관측키 연결이 없어 검수팩은 기존 20키를 유지합니다. {pack['path']}
- 특수 하늘 3건은 관측 원본과 전체 픽셀이 일치하는 배열을 확인해 해독했습니다. 기존 849개 이미지 회귀검사가 통과했습니다. 남은 특수형식 3건은 미해결입니다.
- 실제 교체 표시, Orbit 한글 폰트와 LOCK ON, 전체 지역·필드·적·효과·컷신 검증은 남았습니다. Windows 검수창 접근 오류 해소는 확인되지 않았으며 최종 배포 ZIP은 없습니다.
- 다음: BM189 표식 식별·보호, BM193/BM284 색상 띠의 소비 구조, 미처리 113종과 보류 12종의 작업을 이어갑니다. 화면 접근이 가능해지면 고정된 에뮬 실행 파일에 ISO를 직접 지정해 실게임 검수를 진행합니다.
'''
(C/'outputs/로컬_업스케일_진행.md').write_text(note,'utf8')
with (R/'PROGRESS.md').open('a',encoding='utf8') as f:
    f.write('''

## 2026-09-23 — LOCAL-SR-009: 3·4지역 투명재질24종 검수와 효과 재작업

- 24신규원본 WDN/photo 48출력, 실제114 RGB/alpha pass. 얇은 철골·폐허·격자와 soft effect를 분리하고, BM137/140/141/142는 보이는 구역별 추론. 원본 알파 bilinear와 neural을 혼합, 완전투명/불투명 경계와 평균 명암 보호. 구역 분할은 native UV 증거가 아님.
- 초기비교8페이지·5종재작업5페이지·matte8페이지와BM136상세2crop을 직접검수. BM139/146/172/195 filtered-guided 채택. BM196은 밝은matte에서초기WDN의갈라진무늬를확인해추가1RGB pass/3출력, 재작업비교와양배경확인후filtered-guided로변경. 초기matte-07의BM196은대체됨.
- 총66출력/실제120로컬pass. 22정적후보 선택: WDN BM136/137/140/141/142/143/153/154/155/183/199, photo BM132/135/138/171/197/198, filtered-guided BM139/146/172/195/196. BM145 작은검정·노랑그림의입체화와중앙chip변형, BM147 작은흑백엠블럼변형은보류. 의미나문구를추측하여채택하지않음.
- 모든원본PTM/RGBA·모델·입력·native·parent·출력SHA/8배크기검사. 분할별bilinear알파를재구성해기록과일치, 완전투명0/불투명255support확인. sourcealpha>=16→축소alpha<8 손실0은특정임계검사에한함. 재작업18출력알파는초기WDN과byte-exact이며원본과동일하다는뜻아님. qa/local_sr009_review.json.
- 기존137후보와BM284그룹·미해독3건보존. 전투171처리/159후보/12보류/113미처리,고유원본누계172(타이틀1포함),284는전투맵고유분모. 새24종관측키0이므로20키팩변경/설치없음. 전체목표active,런타임/최종ZIP미완료.
- BM189 원본과진단용대비표를검토: 왼쪽의반복된어두운표식과오른쪽뾰족한엠블럼형태이나정확한문구/역할미확정. 번역없음. 다음 BM189보호·BM193/BM284색띠소비확인,나머지지역·필드·적·효과·컷신범위확장및12보류재작업.
- 사용자Fate질문은모델파일SHA와qa/realesrgan-all.json 121레코드/RTX5080/native4x+Lanczos최종8x로확인. 로컬모델부재라는과거설명을정정. 이번009는외부업로드없음,에뮬실행없음. Windows화면접근문제외부변화증거없어검은창캡처반복안함.
- 사용자출력: 로컬_업스케일_투명재질_검수.png, 로컬_업스케일_효과_재작업.png, 로컬_업스케일_진행.md. GUI접근불가로파일미리보기사용.
''')
assert pack_population=={str(p.relative_to(packpath)):sha(p.read_bytes()) for p in packpath.rglob('*') if p.is_file()}
saved=read('qa/battle_sr_catalog.json')
assert saved==cat and read(FINAL)==report
print(json.dumps({'selected':22,'new_holds':['BM145','BM147'],'output_records':66,'actual_neural_passes':120,'summary':summary},ensure_ascii=False))
