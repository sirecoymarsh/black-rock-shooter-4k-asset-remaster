"""Commit directly reviewed SR011 choices after provenance and alpha checks."""
import copy,hashlib,json,shutil
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1]
C=Path('C:/Users/CadriacLord/Documents/Codex/2026-09-22/brs-hd-ui-fonts')
FINAL='qa/local_sr011_review.json'
if (R/FINAL).exists():raise SystemExit('Already finalized; use a new revision.')
def read(p):return json.loads((R/p).read_text('utf8'))
def sha(b):return hashlib.sha256(b).hexdigest()
def check(p,h):assert sha(Path(p).read_bytes())==h,str(p)
def write(p,obj):
    p=R/p;t=p.with_suffix(p.suffix+'.staging');t.write_text(json.dumps(obj,ensure_ascii=False,indent=2),'utf8');t.replace(p)
cat=read('qa/battle_sr_catalog.json');groups={g['group_id']:g for g in cat['groups']}
prior={g:copy.deepcopy(r['candidate']) for g,r in groups.items() if r.get('candidate')}
assert len(prior)==188 and len(groups)==284
sky=copy.deepcopy(groups['BM284']);special=copy.deepcopy(cat['source_decode_failures']);assert len(special)==3
q=read('qa/local_sr011_inference.json');retry=read('qa/local_sr011_rework.json');late=read('qa/local_sr011_bm221_rework.json');proposed=read('qa/local_sr011_proposed_review.json')
assert len(q['files'])==84 and len(retry['files'])==9 and len(late['files'])==3
assert len(q['group_ids'])==42 and not any(groups[g].get('local_sr_attempted') for g in q['group_ids'])
chosen=next(r for r in late['files'] if r['id']=='BM221-filtered-guided')
proposed['selected']['BM221']={'output':chosen['output'],'output_sha256':chosen['output_sha256'],'model_id':None,'id':chosen['id']}
selected_paths={g:r['output'] for g,r in proposed['selected'].items()}
reasons={
 'BM204':'WDN retains bracket gaps and long thin stem; stronger seam interpretation in Photo avoided.',
 'BM205':'WDN retains openings, diagonal braces and the narrow crossbar on both mattes.',
 'BM206':'WDN retains paired beams and avoids the stronger added cracks in Photo.',
 'BM207':'Photo retains right-angle frame and very thin connecting bars with less center-corner cracking.',
 'BM208':'Photo retains the column planes and both projecting nodes with less grain.',
 'BM214':'Photo retains repeated link openings and connecting rods. Both matte details inspected at 8x; rounded-corner appearance changes, so geometry is not byte-exact.',
 'BM216':'Photo retains thin lower stem and internal openings with less granular wear.',
 'BM217':'Photo avoids WDN pitting while retaining both long strips.',
 'BM219':'WDN retains the long frame and lower broken node on both mattes.',
 'BM220':'Photo retains repeated spikes and separate curved lower strip with calmer surfaces. Source rows were isolated; native UV partition remains unverified.',
 'BM221':'8x detail inspection rejected both initial models: pink-green checks became an embossed mesh. Filtered-guided retry restores source color checks and reduces invented depth. Softer edges are an explicit tradeoff; both final mattes inspected.',
 'BM222':'Photo retains the pale column silhouette and projecting planes with less granular texture.',
 'BM223':'Photo retains the two nodes and pale outlines with smoother planes.',
 'BM224':'WDN retains the faint diagonal links on both mattes. Photo creates threshold-128 alpha pixels absent from the source and was not selected.',
 'BM225':'Photo retains the very thin upper spike and curved arch. Top 64x64 source crop inspected at 8x on both mattes.',
 'BM228':'Photo retains horizontal channels, lower opening and purple planes with less surface grain.',
 'BM230':'Photo retains seven link openings and connectors. 8x crop and full two-matte review completed; rounded corners are not source-byte-exact.',
 'BM234':'Photo retains the window braces and lattice while reducing rough grain. Full view and 8x upper-left crop inspected on both mattes.',
 'BM235':'WDN retains dangling branches and gaps without the stronger top-surface speckling in Photo.',
 'BM242':'Photo retains large cutouts and angled frame with slightly calmer highlights.',
 'BM245':'Photo retains the dense buildings and scattered fragments with fewer exaggerated small shard divisions.',
 'BM246':'Photo retains the long pointed silhouette and thin links while reducing grain.',
 'BM247':'Photo retains the skyline and window rows with smoother bright rooftops.',
 'BM248':'WDN retains hanging chains and narrow projections with less intensified tiny chrome-like highlights.',
 'BM249':'WDN retains the paired architectural pieces with less white-outline exaggeration than Photo; surface details remain inferred.',
 'BM250':'Photo retains isolated rows and thin lower fragment with calmer stone planes; native UV partition unverified.',
 'BM252':'WDN keeps softer central density than the crackly Photo interpretation. Sparse peripheral alpha pattern remains visible on light and dark mattes.',
 'BM257':'WDN retains thin vertical and crossbars and the small irregular top fragment on both mattes.',
 'BM258':'Photo retains seven link openings and the long connecting rod; 8x detail reviewed on both mattes.',
 'BM260':'Photo retains three openings and connectors; 8x detail reviewed, with mild corner-shape interpretation remaining.',
 'BM261':'WDN retains both slab silhouettes and avoids some of Photo stronger surface grooves. Two source rows were isolated; surface cracks are inferred.',
 'BM262':'Filtered-guided rework reduces artificial bright outlines and polished appearance on small fragments while restoring source color masses.',
 'BM263':'WDN retains small arched cutouts and detached masonry with less bright grain than Photo.',
 'BM264':'Filtered-guided rework suppresses the initial models invented crack network and restores coarse soft source density; both mattes inspected.',
 'BM265':'WDN retains long spike, internal rods and large cutouts on both mattes.',
 'BM266':'Photo retains pale linework and separated architectural shapes with calmer surfaces.',
 'BM276':'WDN retains soft gray density with less coarse grain than Photo.',
 'BM277':'Filtered-guided rework restores blue/white source masses and suppresses invented rough cloud/surface texture. No new geographical detail is treated as original evidence.',
 'BM278':'Photo retains five purple fragments and their gaps with less strong groove interpretation.',
 'BM280':'WDN retains thin purple diagonal braces and large openings on both mattes.',
 'BM282':'Photo retains the spiked silhouette, sparse particles and thin lower frame. Alpha IoU is below 1; all-geometry preservation is not claimed.',
 'BM283':'WDN retains the narrow pointed strip with less grain than Photo. Alpha IoU is below 1; all-geometry preservation is not claimed.'
}
assert set(reasons)==set(q['group_ids'])==set(selected_paths)
selected={};checked=[];models=set();initial={};passes=0
reports=[('qa/local_sr011_inference.json',q),('qa/local_sr011_rework.json',retry),('qa/local_sr011_bm221_rework.json',late)]
for name,report in reports:
    count=0
    for row in report['files']:
        gid=row['group_id'];g=groups[gid];src=Image.open(row['source']).convert('RGBA')
        assert src.size==(g['width'],g['height']) and sha(src.tobytes())==g['rgba_sha256']==row['source_rgba_sha256']
        check(g['representative']['source'],g['representative']['source_sha256'])
        m=row['model'];pair=(m['path'],m['sha256'])
        if pair not in models:check(*pair);models.add(pair)
        check(row['output'],row['output_sha256']);out=Image.open(row['output']).convert('RGBA')
        assert out.size==(src.width*8,src.height*8)==tuple(row['output_size'])
        actual=0
        if report is q:
            ref=Image.new('L',out.size);coverage=np.zeros((src.height,src.width),np.uint8)
            for part in row['parts']:
                x0,y0,x1,y1=part['source_box'];assert 0<=x0<x1<=src.width and 0<=y0<y1<=src.height
                coverage[y0:y1,x0:x1]+=1;wh=(x1-x0,y1-y0)
                for key in ['input_rgb','input_alpha','rgb_native','alpha_native']:
                    if key not in part:continue
                    check(part[key],part[key+'_sha256']);im=Image.open(part[key]);scale=4 if 'native' in key else 1
                    assert im.size==(wh[0]*scale,wh[1]*scale)
                    actual+=int('native' in key)
                ref.paste(src.crop((x0,y0,x1,y1)).getchannel('A').resize((wh[0]*8,wh[1]*8),Image.Resampling.BILINEAR),(x0*8,y0*8))
            assert np.all(coverage==1)
            check(row['reference_alpha'],row['reference_alpha_sha256']);assert ref.tobytes()==Image.open(row['reference_alpha']).convert('L').tobytes()
            a=np.asarray(out.getchannel('A'));lin=np.asarray(ref);original=np.asarray(src.getchannel('A'));down=np.asarray(out.getchannel('A').resize(src.size,Image.Resampling.LANCZOS))
            assert np.all(a[lin==0]==0) and np.all(a[lin==255]==255)
            gt=original>=128;pred=down>=128;union=(gt|pred).sum()
            metric={'mass_ratio':float(a.mean()/original.mean()),'source_threshold128_iou':float((gt&pred).sum()/union) if union else 1.,'source_ge16_reduced_below8':int(((original>=16)&(down<8)).sum()),'outside_panel_bilinear_support':0}
            for k,v in metric.items():assert abs(v-row['alpha_metrics'][k])<1e-12,(gid,k)
            assert metric['source_ge16_reduced_below8']==0
            alpha={'panel_bilinear_reconstructed':True,'zero_and_solid_support_verified':True,**metric,'source_alpha_max':int(original.max()),'downsample_alpha_max':int(down.max())}
            initial[(gid,row['model_id'])]=row
        else:
            for key in ['alpha_parent','parent','input','native']:
                if key in row:check(row[key],row[key+'_sha256'])
            assert row['alpha_parent']==initial[(gid,'wdn')]['output']
            assert out.getchannel('A').tobytes()==Image.open(row['alpha_parent']).convert('RGBA').getchannel('A').tobytes()
            if 'native' in row:
                assert Image.open(row['native']).size==(src.width*4,src.height*4) and Image.open(row['input']).size==src.size
                actual=1
            alpha={'alpha_exact_to_initial_wdn_parent':True,'original_source_alpha_byte_exact':False}
        assert actual==row['new_neural_passes'];count+=actual
        pick=row['output']==selected_paths[gid]
        row['visual_review']={'reviewer':'Codex internal','status':'selected_for_game_review' if pick else 'not_selected','reason':reasons[gid] if pick else 'Alternate not selected. '+reasons[gid],'evidence':report['comparison_sheets']}
        checked.append({'group_id':gid,'output':row['output'],'output_sha256':row['output_sha256'],'source_ptm_and_rgba_verified':True,'model_input_native_parent_hashes_verified':True,'size_8x_verified':True,'alpha_checks':alpha,'new_neural_passes':actual})
        if pick:
            assert gid not in selected
            selected[gid]={'source_report':name,'source_rgba_sha256':g['rgba_sha256'],'output':row['output'],'output_sha256':row['output_sha256'],'reason':reasons[gid],'status':'static_candidate_for_consumer_and_game_review','runtime_verified':False,'release_eligible':False}
    assert count==report['new_neural_passes'];passes+=count
assert len(checked)==96 and passes==184 and len(selected)==42
mapped={g['group_id'] for g in groups.values() if any(b['source_rgba_sha256']==g['rgba_sha256'] and b['size']==[g['width'],g['height']] for b in read('qa/battle_map_runtime_links.json')['bindings'])}
assert not set(q['group_ids'])&mapped
pack=read('qa/local_sr_observed_review_pack_v2.json');packpath=Path(pack['path']);check(packpath/'textures.ini',pack['textures_ini_sha256']);assert len(pack['keys'])==20
assert {p.relative_to(packpath).as_posix() for p in packpath.rglob('*.png')}==set(pack['keys'].values())
population={str(p.relative_to(packpath)):sha(p.read_bytes()) for p in packpath.rglob('*') if p.is_file()}
for b in pack['battle_binding_evidence']:check(packpath/pack['keys'][b['key']],b['output_sha256'])
for gid in q['group_ids']:groups[gid]['local_sr_attempted']=True;groups[gid]['candidate']=selected[gid]
for gid,v in prior.items():assert groups[gid]['candidate']==v
assert groups['BM284']==sky and cat['source_decode_failures']==special
pcount=sum(bool(g.get('local_sr_attempted')) for g in groups.values());ccount=sum(bool(g.get('candidate')) for g in groups.values());assert (pcount,ccount)==(244,230)
summary=cat['processing_summary'];summary.update(battle_groups_locally_processed=244,battle_static_candidates=230,battle_processed_without_accepted_candidate=14,battle_groups_not_yet_processed=40,all_unique_originals_locally_processed=245,latest_rework=FINAL,new_unique_originals_latest_rework=42,checked_output_records_latest_rework=96,new_unique_originals_LOCAL_SR_011=42,neural_passes_LOCAL_SR_011=184)
proposed['review_state']='Model comparisons, 8x detail crops and final light/dark mattes directly inspected; runtime unverified'
proposed['matte_pages'].append(str(R/'outputs/sr011-mattes/BM221-rework-mattes.png'))
proposed['superseded_matte_choices']={'matte-04.png BM221':'Initial Photo rejected after 8x detail inspection; replaced by filtered-guided rework.'}
evidence_paths=sorted(set(sum((r['comparison_sheets'] for _,r in reports),[])+proposed['matte_pages']+proposed['detail_pages']))
evidence=[{'path':p,'sha256':sha(Path(p).read_bytes()),'reviewed_by':'Codex internal'} for p in evidence_paths]
field=read('qa/field_map_inventory.json');fd=read('qa/field_map_sc_diagnostics.json');assert fd['source_inventory_sha256']==sha((R/'qa/field_map_inventory.json').read_bytes())
report={'schema':'brs-local-sr-review/v11','batch':'LOCAL-SR-011','selected':selected,'new_holds':{},'checked_outputs':checked,'new_unique_originals':42,'new_actual_local_neural_passes':184,'prior_candidates_preserved':188,'processing_summary':copy.deepcopy(summary),'review_evidence':evidence,'new_sources_observed_keys':0,'pack_unchanged_keys':20,'pack_file_hashes':population,'local_inference':True,'image_upload_this_batch':False,'runtime_verified':False,'release_eligible':False,'field_inventory_partial':{'report':'qa/field_map_inventory.json','sha256':fd['source_inventory_sha256'],'summary':field['summary'],'verified_container_counts':fd['container_counts'],'failure_diagnoses':fd['diagnosis_counts'],'new_field_sr_candidates':0},'limitations':['Original alpha bytes are not preserved: neural/bilinear alpha is constrained at source-bilinear zero and solid support only.','A zero weak-alpha loss count at one downsample threshold is not proof of every line, geometry, blend mode or game appearance.','Row partition follows visible image separation, not verified native UV consumers.','Source-guided retries combine local neural detail with source color; this postprocessing is not an extra model pass.','284 groups describe battle maps only. Field inventory is partial and excludes no unresolved leaves from the whole-game task.'],'scripts':{p:sha((R/'tools'/p).read_bytes()) for p in ['batch_sr011_alpha.py','rework_sr011.py','rework_sr011_bm221.py','prepare_sr011_mattes.py','review_sr011_bm221.py','finalize_sr011.py','inventory_field_maps.py','diagnose_field_sc.py']}}
# Comparison of the four reworked selections, not a claim of runtime approval.
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18);sheet=Image.new('RGB',(1110,1450),'#293440');d=ImageDraw.Draw(sheet)
for j,label in enumerate(['원본 단순 확대','초기 로컬 AI','재작업 · 게임 검수 전']):d.text((j*370+10,8),label,font=font,fill='white')
for i,gid in enumerate(['BM221','BM262','BM264','BM277']):
    row=initial[(gid,'wdn')];src=Image.open(row['source']).convert('RGBA');ims=[src,Image.open(row['output']).convert('RGBA'),Image.open(selected[gid]['output']).convert('RGBA')]
    box=(0,32,32,96) if gid=='BM221' else (0,0,src.width,src.height);wh0=(box[2]-box[0],box[3]-box[1]);scale=min(348/wh0[0],285/wh0[1],8);wh=(round(wh0[0]*scale),round(wh0[1]*scale))
    for j,im in enumerate(ims):
        x=j*370+10;y=i*350+50;d.text((x,y),gid+f' · 표시 {scale:.2f}배',font=font,fill='white');im=im.crop(box if j==0 else tuple(v*8 for v in box)).resize(wh,Image.Resampling.NEAREST if j==0 else Image.Resampling.LANCZOS);bg=Image.new('RGB',wh,'#eeeeee');bg.paste(im,(0,0),im);sheet.paste(bg,(x,y+32))
output=R/'outputs/local_sr011_rework_selected.png';sheet.save(output);shutil.copyfile(output,C/'outputs/로컬_업스케일_투명재질_재작업.png')
backup=R/'qa/backups/before-sr011-finalize';backup.mkdir(parents=True,exist_ok=False)
to_save=[*reports,('qa/local_sr011_proposed_review.json',proposed),('qa/battle_sr_catalog.json',cat)]
for name,_ in to_save:shutil.copyfile(R/name,backup/Path(name).name)
for name,obj in to_save:write(name,obj)
write(FINAL,report)
note='''# 로컬 업스케일 진행 — LOCAL-SR-011

- 실제 로컬 GPU 추론을 거친 고유 원본 **245종**: 타이틀 1 + 전투재질 244.
- 전투맵 284종 중 정적 검수 후보 **230종**, 처리 후 보류 **14종**, 미처리 **40종**입니다. 게임 전체 완료율이 아닙니다.
- 이번 신규 42종은 두 모델 비교와 재작업을 포함해 **96개 결과·실제 로컬 추론 184회**를 검사했습니다. 비교 14페이지, 밝고 어두운 배경 14페이지, 상세 확대 8페이지, 재작업 4종과 추가 배경 비교를 직접 확인했습니다.
- 체크무늬의 금속 그물화, 파편의 과한 광택, 효과의 균열과 거친 무늬를 발견해 4종을 다시 처리했습니다. 원본 색을 반영한 후처리를 포함하며 일부 결과는 선명함보다 원래 무늬 보존을 우선했습니다.
- 모델 자체는 4배 처리하고 보간으로 2배 더 키워 최종 8배 크기를 만듭니다. 원본 색 혼합과 투명도 보정은 별도 후처리입니다.
- 이번 작업은 로컬 RTX 5080에서 처리했고 외부 이미지 업로드는 없습니다. 이전 GPT BM162 시도 1회는 외부 이미지 편집이었으며 미채택입니다.
- 필드맵 88개에서 테이블에 연결된 텍스처 1,630건 중 1,616건을 해독했습니다. 중복을 합치면 576종이며, 신규 HD 후보는 아직 없습니다. 컨테이너 194건과 특수 텍스처 14건, 미분류 구획 808건은 조사가 남았습니다.
- 새 42종의 정확한 게임 관측키는 아직 없어 기존 20키 검수팩을 유지합니다. 실제 교체 표시, Orbit 한글 폰트와 LOCK ON, 전체 지역·필드·적·효과·컷신 검증은 남았습니다. Windows 검수창 접근 오류 해소는 확인되지 않았으며 최종 배포 ZIP은 없습니다.
- 다음: 남은 전투 40종/보류 14종, 필드맵의 미지원 구획 형식과 원본 분류를 이어갑니다. 에뮬레이터는 고정 실행 파일에 ISO를 직접 지정해 실행합니다.
'''
(C/'outputs/로컬_업스케일_진행.md').write_text(note,'utf8')
with (R/'PROGRESS.md').open('a',encoding='utf8') as f:
    f.write('''

## 2026-09-23 — LOCAL-SR-011: 5·6지역 투명재질42종과 필드맵 부분 추출

- 신규42종 WDN/photo 84출력/실제180 RGB·alpha pass. BM220/250/261은보이는두행을격리,soft4종과thin8종은neural-alpha20%,나머지35%와source-bilinear혼합. zero/255support·평균RGB/alpha보정. native4x+Lanczos2x이며nativeAI8x아님.
- 초기14페이지와matte14페이지·8개8x상세crop직접검토. BM262파편광택/BM264균열/BM277거친밀도에추가3RGB pass·9출력. BM221상세에서체크무늬가금속망으로변한것을확인해추가1pass·3출력,최종두배경/3x·8x검토.4종filtered-guided선택. 후처리8개는새추론으로세지않음. 총96출력/184실제pass/42정적후보. BM221초기matte04Photo는최종재작업으로대체.
- 모든원본PTM·RGBA/모델/input/native/parent/output SHA·4x/8x크기·분할coverage검증. 분할별bilinearalpha재구성일치,zero/solid영역보존,alpha>=16→축소<8손실0. 단일임계검사로전체형상/블렌딩보존주장안함. BM224Photo는원본max115에없는128threshold픽셀생성으로미채택,WDN선택. BM282/283 alphaIoU<1그대로기록. qa/local_sr011_review.json.
- 기존188후보/skyBM284/미해독3건보존. 전투244처리/230후보/14보류/40미처리,타이틀포함고유245. 새42종관측키0,기존20키시험팩바이트보존/미설치. 런타임·최종ZIP미완료,전체목표active. 에뮬실행/새외부업로드없음.
- FLD/MAP88gzip루트원본해시/SC·STCM포인터경계검사. SC363/STCM151개테이블검증,텍스처1630건중1616해독·roundtrip,576고유FM그룹.225그룹은BM크기+RGBA동일일뿐소비자/UV/키동일증거아님. 새필드HD처리0. qa/field_map_inventory.json.557 SC레코드에는실패194개가포함되므로557검증완료주장금지.
- field실패208건=SC분류/테이블194+PTMD14.14는128x4 flag4한건/16x1 flag5열세건. 미분류leaf808개. 194실패의bounded slice를원본88루트해시와재대조: firstoffset가정차88,미지원count79,lastoffset크기차22,SCMP서명겹침5. qa/field_map_sc_diagnostics.json. 첫offset52/56/60이지만SSCR은48부터인variant와zero/sparseoffsetvariant확인;단순header허용완화로강제추출안함.
- 사용자Fate질문: RealESRGAN_x4plus_anime_6B/RTX5080/121기록/native4x+Lanczos최종8x확인. 이전모델부재설명오류정정. Coutputs/로컬_업스케일_투명재질_재작업.png 및진행.md갱신. GUI접근불가로Codex미리보기사용.
- 다음: 남은BM40/보류14,field미지원variant해독과576원본분류·주인공연결제외대조,FLD/적/효과/컷신확장. 접근복구증거확보시고정exe+ISO CLI실게임title/Orbit/LOCK ON·지역검수.
''')
assert population=={str(p.relative_to(packpath)):sha(p.read_bytes()) for p in packpath.rglob('*') if p.is_file()}
assert read('qa/battle_sr_catalog.json')==cat and read(FINAL)==report
print(json.dumps({'outputs_checked':len(checked),'neural_passes':passes,'selected':len(selected),'summary':summary},ensure_ascii=False))
