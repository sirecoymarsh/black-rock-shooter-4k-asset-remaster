"""Stage one exact-key local-SR title candidate; do not install or launch game."""
import sys, json, io, datetime
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import local_sr as sr

sys.stdout.reconfigure(encoding='utf8')
R=Path(__file__).resolve().parents[1]
qa=json.loads((R/'qa/local_sr_title_models_v2.json').read_text('utf8'))
selected=next(r for r in qa['files'] if r['id']=='general-dn0.0')
input_bytes=Path(selected['output']).read_bytes()
assert sr.sha(input_bytes)==selected['output_sha256']
active=Image.open(io.BytesIO(input_bytes)).convert('RGBA')
links=json.loads((R/'qa/ui_expanded_links.json').read_text('utf8'))
matches=links['assets']['title.vol::001_if_title.zzz::000']
assert len(matches)==1
link=matches[0];key=link['key']
assert key=='0000000086ba34d7c28b381c' and link['size']==[512,512]
raw=Path(link['paths'][0]).read_bytes();assert sr.sha(raw)==link['png_sha256']
src=Image.open(io.BytesIO(raw)).convert('RGBA');assert sr.sha(src.tobytes())==link['rgba_sha256']
assert sr.sha(src.crop((0,0,512,280)).tobytes())==link['logical_rgba_sha256']
expected=src.resize((4096,4096),Image.Resampling.NEAREST)
candidate=expected.copy();candidate.paste(active,(0,0))
assert candidate.getchannel('A').tobytes()==expected.getchannel('A').tobytes()
assert candidate.crop((3840,0,4096,4096)).tobytes()==expected.crop((3840,0,4096,4096)).tobytes()
assert candidate.crop((0,2176,4096,4096)).tobytes()==expected.crop((0,2176,4096,4096)).tobytes()
stage=R/'workspace/local-sr/title-review-pack/PSP/TEXTURES/NPUH10126'
(stage/'title').mkdir(parents=True,exist_ok=True)
dest=stage/'title/title-metal-local-sr.png';candidate.save(dest)
(stage/'textures.ini').write_text('[options]\nversion = 1\nhash = xxh64\nignoreAddress = true\nreduceHash = false\n\n[hashes]\n'+key+' = title/title-metal-local-sr.png\n','utf8')

def lines(im):
    a=np.asarray(im.convert('RGB').resize((480,272),Image.Resampling.LANCZOS),dtype=np.float32).mean(axis=2)
    return {'vertical_dark_center_x':int(np.argmin(a[:,232:247].mean(axis=0)))+232,
            'horizontal_dark_center_y':int(np.argmin(a[187:196,30:180].mean(axis=1)))+187}
geometry={'source':lines(src.crop((0,0,480,272))),'candidate':lines(active)}
assert abs(geometry['source']['vertical_dark_center_x']-geometry['candidate']['vertical_dark_center_x'])<=1,geometry
assert geometry['source']['horizontal_dark_center_y']==geometry['candidate']['horizontal_dark_center_y'],geometry
geometry['limit']='Darkest profile sample within one native pixel; this alone does not prove all edges or in-game alignment.'
record={'schema':'brs-local-sr-title-stage/v1','asset_id':'title.vol::001_if_title.zzz::000',
        'selected_trial':selected,'key':key,'source_full_png_sha256':link['png_sha256'],
        'source_full_rgba_sha256':link['rgba_sha256'],'observed_source_paths':link['paths'],
        'output':str(dest),'output_size':list(candidate.size),'output_sha256':sr.sha(dest.read_bytes()),
        'output_rgba_sha256':sr.sha(candidate.tobytes()),'native_neural_scale':4,'post_scale':'Lanczos 2x',
        'alpha_unchanged_from_nearest_source':True,'outside_active_rect_unchanged':True,'geometry':geometry,
        'status':'Selected for isolated game verification; not installed or release eligible',
        'visual_review':'General WDN retains more grain, scratch shape and rivet shading than anime6B. Palette dithering vs authentic high-frequency grain is not fully separable from this source.',
        'runtime_verified':False,'installed':False,'release_eligible':False}
(R/'qa/local_sr_title_stage.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),'utf8')

src_active=src.crop((0,0,480,272)).convert('RGB')
rejected=Image.open(R/'workspace/local-sr/title-trial-v1/title-active-8x.png').convert('RGB')
labels=['원본 단순 확대','첫 로컬 결과 · 미채택','재처리 · 게임 검수 후보']
images=[src_active.resize((3840,2176),Image.Resampling.NEAREST),rejected,active.convert('RGB')]
font=ImageFont.truetype(r'C:\Windows\Fonts\malgun.ttf',20)
sheet=Image.new('RGB',(1800,1070),'#293440');d=ImageDraw.Draw(sheet)
box=(130,140,330,270)
for col,(label,pic) in enumerate(zip(labels,images)):
    x=10+600*col;d.text((x,8),label,font=font,fill='white')
    full=pic.resize((580,329),Image.Resampling.LANCZOS);sheet.paste(full,(x,44))
    crop=pic.crop(tuple(v*8 for v in box)).resize((580,377),Image.Resampling.LANCZOS)
    boost=Image.fromarray(np.minimum(np.asarray(crop,dtype=np.uint16)*3,255).astype(np.uint8))
    sheet.paste(boost,(x,410))
    detail=pic.crop(tuple(v*8 for v in (225,28,263,65))).resize((260,253),Image.Resampling.LANCZOS)
    detail=Image.fromarray(np.minimum(np.asarray(detail,dtype=np.uint16)*3,255).astype(np.uint8))
    sheet.paste(detail,(x,800))
d.text((700,850),'위: 원래 밝기\n아래: 동일하게 밝힌 검수용 확대\nAI 4배 처리 후 2배 보간\n게임 적용 전 후보',font=font,fill='white')
sheet.save(R/'outputs/local_sr_title_review.png')

readme='''# BRS 타이틀 배경 로컬 업스케일 검수 후보

원본 활성 영역 480×272를 Real-ESRGAN general WDN으로 로컬 GPU에서 4배 처리하고, Lanczos로 2배 더 늘려 3840×2176으로 출력했습니다. 실제 교체 텍스처는 관측된 원본 패딩을 유지한 4096×4096입니다. native 8배 AI나 새로 그린 4K 원화가 아닙니다.

첫 anime6B 결과는 금속 표면의 결을 지우고 작은 리벳을 과하게 강조해 미채택했습니다. 다섯 조건을 다시 비교한 뒤 약한 노이즈 제거 모델을 게임 검수 후보로 골랐습니다. 원래 판의 위치, 알파, 표시 영역 밖 패딩을 검사했습니다.

이 폴더는 한 개 배경의 검수 준비물입니다. 설치하지 않았고, 게임 표시·동적 효과와의 합성 검증 및 나머지 텍스처 작업은 남아 있습니다. 기존 폰트/UI의 단순 확대 그림 부분을 AI 업스케일 완료로 계산하지 않습니다.
'''
(R/'workspace/local-sr/title-review-pack/README-ko.md').write_text(readme,'utf8')
print(json.dumps({'stage':str(stage),'geometry':geometry,'sha256':record['output_sha256'],'runtime_verified':False}),flush=True)
