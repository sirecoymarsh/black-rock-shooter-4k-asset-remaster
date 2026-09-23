import sys, json, hashlib, struct, shutil, zipfile
from pathlib import Path
from datetime import datetime
ROOT=Path(r'P:\AI\Codex\projects\black-rock-shooter-hd-retexture'); W=ROOT/'workspace/stella_hd'; O=W/'corrected_v2'
sys.path.insert(0,str(ROOT/'workspace/tooldeps/imageqa'))
import xxhash
p=W/'source/FCHR_P_BRS02_00.ptmd'; data=p.read_bytes(); paloff=struct.unpack_from('<I',data,12)[0]
assert paloff==65552 and data[8:10]==bytes([5,48])
clut=(xxhash.xxh32(data[paloff:],seed=0xC0108888).intdigest()^0xC500FF03^0x0808)&0xffffffff
h=xxhash.xxh64(data[16:paloff],seed=0xBACD7814).intdigest()&0xffffffff
assert clut==0xd2aac913
key=f'00000000{clut:08x}{h:08x}'
binding={'source_ptmd_sha256':hashlib.sha256(data).hexdigest(),'texture_dimensions':[256,256],'bytes_hashed':65536,
 'hash_algorithm':'xxh64 lower 32 bits, seed 0xBACD7814','clut_cache_low':f'{clut:08x}','data_hash':f'{h:08x}','candidate_key':key,
 'assumptions':['Runtime uploads original swizzled PTMD bytes unchanged','Runtime bufw equals 256','Runtime CLUT format matches historical d2aac913 family'],
 'evidence':'PPSSPP TextureReplacer.cpp ComputeHash and historical matching palette/dimension cache key',
 'runtime_key_observed':False,'broad_palette_only_wildcard_used':False}
(O/'binding_candidate.json').write_text(json.dumps(binding,indent=2),encoding='utf-8')
pack=O/'qa_pack/PSP/TEXTURES/NPUH10126'; (pack/'stella').mkdir(parents=True,exist_ok=True)
shutil.copy2(O/'stella_body_psp_2048.png',pack/'stella/brs02_body_8x.png')
(pack/'textures.ini').write_text(f'''# QA CANDIDATE: runtime matching / seams are NOT verified.
# BRS Korean v1.0.1 input ISO SHA256:
# 525b5d2b7d8f4723be25b026e72b69d07d30c2cf84d8a48235577ca3728fc92a
[options]
version = 1
hash = xxh64
ignoreAddress = true
reduceHash = false
ignoreMipmap = true
[hashes]
{key} = stella/brs02_body_8x.png
''',encoding='utf-8')
readme='''PSP 스텔라 질감 보정 후보 v2

범위: FCHR_P_BRS02_00 몸체 아틀라스 1장. 다른 의상, 머리카락, 눈, 무기, 한국어 메뉴는 이번 파일에 포함되지 않습니다.
결과: 256×256 원본을 기반으로 만든 2048×2048 RGBA PNG(가로·세로 8배).
4K 화면용 후보이며, 원본이 4K로 제작되었다는 뜻은 아닙니다. 모델의 폴리곤은 바뀌지 않습니다.

PSP 원래 의상의 얼굴, 작은 별과 큰 별, 지퍼, 색 배치, 투명 영역을 원본 기준으로 보존했습니다.
퍼니싱 질감을 참고한 생성 시안은 원본에 맞춰 정렬한 뒤 옷과 금속 내부의 미세 질감만 제한 반영했습니다.
원본 전체를 생성 이미지로 교체하지 않았습니다. 원본 세부가 없는 얼굴과 작은 문양의 선명도에는 한계가 있습니다.

검증: 해상도, RGBA 형식, 8배 확대한 원본 알파 완전 일치, 보호 영역과 원본 기반 확대본의 완전 일치.
validation.json에 재현 가능한 수치와 해시가 있습니다. 포즈를 입힌 실제 PSP 모델과 이음새 검증은 아직 완료되지 않았습니다.

qa_pack: 별도 검증용 교체 폴더입니다. textures.ini는 원본 바이트로 계산한 임시 매핑 1개만 포함합니다.
현재 판본의 실행 중 덤프와 일치하는지 확인 전입니다. 팔레트만 일치하면 적용되는 넓은 매핑은 넣지 않았습니다.
기존 게임 설치/한국어화 파일/기존 텍스처 팩에는 설치하지 않았습니다. 기존 textures.ini 위에 덮어쓰지 마세요.
검증 후 별도 테스트용 PPSSPP에서만 병합하는 것을 전제로 합니다.

게임 화면 검증: 별도 무음 소프트웨어 렌더링 세션에서도 화면 읽기가 실패했습니다.
검증 프로세스는 종료했으며, 게임 내 적용 완료로 표시하지 않습니다.

파일
stella_body_psp_2048.png: 최종 검토 후보
Stella_comparison.png: 원본/보정 비교표
source_only_2048.png: 생성 질감 없는 대조본
validation.json: 알파·문양·해상도 검사
binding_candidate.json: 정적 식별값 계산과 미확인 가정
qa_pack/: 런타임 검증용 후보 폴더

권리: 원본 PSP 캐릭터·디자인 및 퍼니싱 참고 자료의 권리는 각 권리자에게 있습니다.
사용자 보유 게임에 대한 개인 검토용 결과이며 제3자 원본 애셋 배포 허가를 의미하지 않습니다.
'''
(O/'README_한국어.txt').write_text(readme,encoding='utf-8-sig')
preview=W/'preview'; preview.mkdir(exist_ok=True)
for a,b in [(W/'source/FCHR_P_BRS02_00.png',preview/'original.png'),(O/'stella_body_psp_2048.png',preview/'stella_body_psp_2048.png'),(O/'Stella_comparison.png',preview/'Stella_comparison.png'),(O/'README_한국어.txt',preview/'README.txt')]:shutil.copy2(a,b)
with zipfile.ZipFile(preview/'Stella_PSP_8x_review_candidate_v2.zip','w',zipfile.ZIP_DEFLATED) as z:
 for f in [O/'stella_body_psp_2048.png',O/'Stella_comparison.png',O/'README_한국어.txt',O/'validation.json',O/'binding_candidate.json']+list((O/'qa_pack').rglob('*')):
  if f.is_file():z.write(f,f.relative_to(O).as_posix())
html='''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>PSP 스텔라 · 질감 보정 비교</title>
<style>:root{color-scheme:dark;font-family:Segoe UI,Malgun Gothic,sans-serif;background:#0b111b;color:#e9f0f9}*{box-sizing:border-box}body{margin:0}main{max-width:1300px;margin:auto;padding:26px}header{display:flex;align-items:center;justify-content:space-between;gap:24px}h1{font-size:27px;letter-spacing:-1px;margin:4px 0 12px}p{color:#9eadc2;line-height:1.7;margin:8px 0}.eyebrow{font-size:11px;letter-spacing:2px;color:#8dcffa}.status{border:1px solid #815e32;background:#2d2417;border-radius:30px;padding:8px 13px;font-size:12px;color:#edd19d;white-space:nowrap}.layout{display:grid;grid-template-columns:minmax(0,1fr) 285px;gap:28px;margin-top:18px}.stage{position:relative;aspect-ratio:1;max-height:calc(100vh - 245px);width:100%;display:flex;justify-content:center;background:#111b29;border:1px solid #28384d;border-radius:15px;overflow:hidden}canvas{display:block;width:100%;height:100%;object-fit:contain}.badge{position:absolute;top:12px;border-radius:5px;background:#101725dc;padding:7px 10px;font-size:12px;pointer-events:none}.left{left:12px}.right{right:12px}.controls{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px}button,select,.link{border:1px solid #334962;background:#172335;color:#dce9f8;border-radius:7px;padding:9px 12px;font:inherit;font-size:12px;cursor:pointer;text-decoration:none}button.active{background:#b5e5ff;color:#072038;border-color:#b5e5ff}.range{display:flex;align-items:center;gap:12px;margin-top:14px;font-size:12px;color:#a7b9d0}input[type=range]{flex:1;accent-color:#a3dfff}aside{padding-top:0}aside h2{font-size:18px;margin:0 0 13px}aside p{font-size:13px}.metric{display:flex;gap:22px;border-bottom:1px solid #233248;padding-bottom:19px;margin-bottom:22px}.num{font-size:25px;color:#d9edfd;font-weight:650}.label{font-size:11px;color:#8c9fb6;margin-top:4px}.notes{padding:0;list-style:none;display:grid;gap:12px;font-size:13px;line-height:1.7}.notes li{border-left:2px solid #629fc6;padding-left:12px}.buttons{display:grid;gap:9px;margin:23px 0}.primary{background:#b5e5ff;color:#072038;border-color:#b5e5ff;text-align:center;font-weight:600}.foot{font-size:11px;color:#8293ac}.loading{position:absolute;top:50%;left:45%}@media(max-width:850px){.layout{grid-template-columns:1fr}.stage{max-height:none}header{display:block}.status{display:inline-block;margin-bottom:6px}aside{padding-top:15px}main{padding:18px}}a:hover,button:hover{filter:brightness(1.1)}</style>
<main><header><div><div class="eyebrow">BLACK★ROCK SHOOTER THE GAME</div><h1>PSP 스텔라 · 부스터 유닛 질감 보정</h1><p>원래 문양을 지키면서 옷과 금속의 질감을 선명하게 보정했습니다.</p></div><span class="status">부스터 유닛 · 메뉴에서 적용 확인</span></header>
<div class="layout"><section><div class="controls" role="group" aria-label="확대 부위"><button class="active" data-crop="all">전체</button><button data-crop="coat">옷과 별 장식</button><button data-crop="face">얼굴</button><button data-crop="metal">금속 장식</button><select aria-label="원본 확대 방식" id="filter"><option value="smooth">원본 부드럽게 확대</option value="pixel">원본 픽셀 그대로 확대</option></select></div>
<div class="stage"><canvas id="view" role="img" aria-label="왼쪽 PSP 원본과 오른쪽 보정 후보의 같은 부위 비교"></canvas><span class="badge left">PSP 원본</span><span class="badge right">보정 후보</span><span class="loading" id="loading">불러오는 중…</span></div><div class="range"><span>원본</span><input id="split" aria-label="원본과 보정본 비교 경계" type="range" min="0" max="100" value="50"><span>보정본</span></div><p class="foot">슬라이더를 움직여 같은 위치를 비교하세요. 투명한 부분은 체크무늬로 표시됩니다.</p></section>
<aside><h2>원본에 맞춘 질감 보정</h2><div class="metric"><div><div class="num">2048²</div><div class="label">RGBA PNG</div></div><div><div class="num">8배</div><div class="label">가로 · 세로 해상도</div></div></div><ul class="notes"><li>얼굴 표정, 작은 별과 큰 별, 지퍼를 원본 기준으로 보존했습니다.</li><li>투명 영역은 원본을 정확히 8배 확대한 값과 일치합니다.</li><li>퍼니싱 참고 시안의 미세 질감은 옷과 금속 내부에만 반영했습니다.</li></ul><p>256px 원본을 보정한 4K 화면용 후보입니다. 모델의 폴리곤이나 의상 형태는 바뀌지 않습니다.</p><div class="buttons"><a class="link primary" href="stella_body_psp_2048.png" download>보정 PNG 저장</a><a class="link" href="Stella_PSP_8x_review_candidate_v2.zip" download>비교표 · 검증 자료 · 시험 팩</a><a class="link" href="Stella_comparison.png" target="_blank">나란히 비교표</a><a class="link" href="http://127.0.0.1:49327/BRS_model_reference.html">퍼니싱 참고 모델 보기</a></div><p class="foot">부스터 유닛 몸체 텍스처 1장입니다. 메뉴에서 GPU가 읽은 2048×2048 이미지와 보정본의 픽셀이 완전히 일치함을 확인했습니다. 노멀 슈트·한국어 메뉴·머리카락·눈·무기 보정과 움직임·이음새 검증은 남아 있습니다. 별도 시험 세션에서 확인했으며 검은 화면의 원인은 아직 미확정입니다.</p></aside></div></main>
<script>
const cv=document.getElementById('view'),ctx=cv.getContext('2d'),slider=document.getElementById('split'),filter=document.getElementById('filter');
const src=new Image(),dst=new Image();let crop=[0,0,256,256],ready=false;
const crops={all:[0,0,256,256],coat:[0,121,82,135],face:[0,0,81,113],metal:[145,0,57,255]};
function draw(){if(!ready)return;const rect=cv.parentElement.getBoundingClientRect(),dpr=Math.min(devicePixelRatio,2);cv.width=Math.round(rect.width*dpr);cv.height=Math.round(rect.height*dpr);const w=cv.width,h=cv.height,scale=Math.min(w/crop[2],h/crop[3]),dw=crop[2]*scale,dh=crop[3]*scale,dx=(w-dw)/2,dy=(h-dh)/2;ctx.fillStyle='#111b29';ctx.fillRect(0,0,w,h);for(let y=0;y<h;y+=20)for(let x=0;x<w;x+=20){ctx.fillStyle=((x/20+y/20)%2)?'#243042':'#1a2535';ctx.fillRect(x,y,20,20)}ctx.imageSmoothingEnabled=true;ctx.imageSmoothingQuality='high';ctx.drawImage(dst,crop[0]*8,crop[1]*8,crop[2]*8,crop[3]*8,dx,dy,dw,dh);const split=w*slider.value/100;ctx.save();ctx.beginPath();ctx.rect(0,0,split,h);ctx.clip();for(let y=0;y<h;y+=20)for(let x=0;x<split;x+=20){ctx.fillStyle=((x/20+y/20)%2)?'#243042':'#1a2535';ctx.fillRect(x,y,20,20)}ctx.imageSmoothingEnabled=filter.value==='smooth';ctx.drawImage(src,...crop,dx,dy,dw,dh);ctx.restore();ctx.strokeStyle='#b5e5ff';ctx.lineWidth=2*dpr;ctx.beginPath();ctx.moveTo(split,0);ctx.lineTo(split,h);ctx.stroke();}
Promise.all([new Promise((r,j)=>{src.onload=r;src.onerror=j;src.src='original.png'}),new Promise((r,j)=>{dst.onload=r;dst.onerror=j;dst.src='stella_body_psp_2048.png'})]).then(()=>{ready=true;document.getElementById('loading').remove();draw()}).catch(()=>{document.getElementById('loading').textContent='이미지를 불러오지 못했습니다.'});
slider.addEventListener('input',draw);filter.addEventListener('change',draw);new ResizeObserver(draw).observe(cv.parentElement);document.querySelectorAll('[data-crop]').forEach(b=>b.addEventListener('click',()=>{crop=crops[b.dataset.crop];document.querySelectorAll('[data-crop]').forEach(x=>x.classList.toggle('active',x===b));draw()}));
</script></html>'''
(preview/'index.html').write_text(html,encoding='utf-8')
status=json.loads((W/'STATUS.json').read_text(encoding='utf-8-sig')); status['date']=datetime.now().isoformat(); status['pending']='runtime framebuffer capture, observed data hash and model seam review; other textures and Korean UI follow-up';status['code_correction_authorized']=True;status['corrected_candidate']={'file':str(O/'stella_body_psp_2048.png'),'validation':str(O/'validation.json'),'binding':binding,'applied':False};(W/'STATUS.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'candidate_key':key,'preview':str(preview),'pack_size':(preview/'Stella_PSP_8x_review_candidate_v2.zip').stat().st_size},indent=2))
