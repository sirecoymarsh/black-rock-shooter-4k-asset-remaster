"""Independent persisted-output QA and original/candidate contact sheets."""
from pathlib import Path
import json,hashlib,math,html
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];O=R/'workspace/ui-icons-001';V=R/'outputs/ui-icons-001'
def read(p):return json.loads(p.read_text('utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',16)
small=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',13)
m=read(O/'manifest.json');checks=[];tiles=[]
for r in m['records']:
 fs=r['files'];src=Image.open(fs['source']['path']).convert('RGBA');before=Image.open(fs['before']['path']).convert('RGBA');out=Image.open(fs['candidate']['path']).convert('RGBA');mask=np.array(Image.open(fs['mask']['path']))>0
 a=np.array(before);b=np.array(out);diff=np.any(a!=b,axis=2)
 assert out.size==(src.width*8,src.height*8)
 assert not diff[~mask].any(),r['id']
 assert sha(Path(fs['candidate']['path']))==fs['candidate']['sha256']
 # Every localized baseline pixel remains equal, independent of masks.
 original=np.array(src.resize(before.size,Image.Resampling.NEAREST));ko=np.any(a!=original,axis=2)
 assert not diff[ko].any(),(r['id'],'localized layer changed')
 checks.append(dict(id=r['id'],geometry=True,protected_rgba=True,prior_localization_equal=True,changed_pixels=int(diff.sum()),candidate_sha256=sha(Path(fs['candidate']['path']))))
 boxes=r['boxes'] or [[0,0,*r['logical_size']]]
 if r.get('cells'):
  boxes=[[x,y,x+16,y+16]for y in range(0,240,16)for x in range(0,64,16)]
  boxes=[b for b in boxes if b[1]!=128]+[[0,128,16,144],[16,128,40,144],[40,128,64,144]]
  boxes.sort(key=lambda b:(b[1],b[0]))
 for j,box in enumerate(boxes):
  xy=tuple(v*8 for v in box);aa=before.crop(xy);bb=out.crop(xy)
  # Crop unchanged fully transparent margins only in proof, never in asset.
  union=Image.fromarray(np.maximum(np.array(aa.getchannel('A')),np.array(bb.getchannel('A'))))
  bounds=union.getbbox()
  if not bounds:continue
  aa=aa.crop(bounds);bb=bb.crop(bounds)
  w,h=aa.size;sc=min(1,240/w,206/h);size=(max(1,round(w*sc)),max(1,round(h*sc)))
  tile=Image.new('RGB',(510,255),(40,47,56));d=ImageDraw.Draw(tile)
  d.text((5,2),f"{r['id']}/{j+1} {r['name']}",font=small,fill='white');d.text((6,23),'기존',font=small,fill='#a8b4c7');d.text((261,23),'HD 후보',font=small,fill='#a8b4c7')
  for i,im in enumerate([aa,bb]):
   im=im.resize(size,Image.Resampling.LANCZOS if sc<1 else Image.Resampling.NEAREST);tile.paste(im,(i*255+7,47),im)
  tiles.append(tile)
 # Transparent-boundary proof on dark, gray and light mattes, full atlas.
 if r['id']=='ICO-001':
  im=out.crop((0,0,512,1920));im.save(V/'common-icons-transparent.png')
  sh=Image.new('RGB',(512*3,1920),(0,0,0))
  for i,col in enumerate([(30,35,43),(128,128,128),(235,235,235)]):
   panel=Image.new('RGBA',im.size,(*col,255));panel.alpha_composite(im);sh.paste(panel.convert('RGB'),(512*i,0))
  sh.save(V/'common-icons-mattes.png')
pages=[]
for n in range(math.ceil(len(tiles)/8)):
 subset=tiles[n*8:n*8+8];page=Image.new('RGB',(1020,math.ceil(len(subset)/2)*255),(40,47,56))
 for j,t in enumerate(subset):page.paste(t,(j%2*510,j//2*255))
 p=V/f'comparison-{n+1:02}.png';page.save(p);pages.append(p.name)
report=dict(schema='brs-icons-static-review/v1',asset_checks=checks,check_count=len(checks)*3,comparison_pages=pages,comparison_regions=len(tiles),visual_review='pending',runtime_verified=False,blocked=m['blocked'])
(R/'qa/ui_icons_001_review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8')
body=''.join(f'<section><h2>비교 {n+1}</h2><img loading="lazy" src="{p}"></section>'for n,p in enumerate(pages))
(V/'index.html').write_text('<!doctype html><html lang="ko"><meta charset="utf-8"><title>BRS 원본 계승 아이콘 HD</title><style>body{background:#171d26;color:#eee;font-family:system-ui;max-width:1180px;margin:32px auto}img{max-width:100%}section{margin:40px 0}p{line-height:1.65}a{color:#8be}</style><h1>원본 계승 아이콘 HD 후보</h1><p>왼쪽: 기존 원본 확대 / 오른쪽: 새 후보. 원본 좌표 도형 보정과 로컬 Real-ESRGAN의 원본 마스크 4배 처리 후 8배 출력. 훈장은 Photo 모델로 처리하고 원본 알파를 유지했습니다. 작은 직각 도형·체크무늬·글자·일부 상태 기호는 원본 도형과 색으로 보정했으며, 부드러운 타이틀 빛 효과는 원본 그라데이션을 유지했습니다. 한국어 문구·위치·캔버스 유지. 실게임 검증 전의 비교 자료입니다.</p>'+body,'utf8')
print(json.dumps(dict(assets=len(checks),checks=len(checks)*3,regions=len(tiles),pages=len(pages))))
