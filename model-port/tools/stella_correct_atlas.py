"""Preserve PSP layout and alpha; transfer only registered, bounded material detail."""
import sys, json, hashlib, math
from pathlib import Path
ROOT=Path(r'P:\AI\Codex\projects\black-rock-shooter-hd-retexture')
sys.path.insert(0,str(ROOT/'workspace/tooldeps/imageqa'))
import cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont
W=ROOT/'workspace/stella_hd'; OUT=W/'corrected_v2'; OUT.mkdir(exist_ok=True)
SCALE=8
src=np.array(Image.open(W/'source/FCHR_P_BRS02_00.png').convert('RGBA'))
orig=src[:,:,:3]; alpha=src[:,:,3]
ai=np.array(Image.open(W/'drafts/stella_body_ai_draft_v1_1254.png').convert('RGB'))
# Source-space registration moves the rejected draft, never the original or its UVs.
gs=cv2.cvtColor(orig,cv2.COLOR_RGB2GRAY)
ga=cv2.cvtColor(cv2.resize(ai,(256,256),interpolation=cv2.INTER_AREA),cv2.COLOR_RGB2GRAY)
flow=cv2.calcOpticalFlowFarneback(gs,ga,None,0.5,5,25,6,7,1.5,0)
back=cv2.calcOpticalFlowFarneback(ga,gs,None,0.5,5,25,6,7,1.5,0)
y,x=np.mgrid[0:256,0:256].astype('float32')
bw=cv2.remap(back,x+flow[:,:,0],y+flow[:,:,1],cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT)
fb=np.linalg.norm(flow+bw,axis=2)
mag=np.linalg.norm(flow,axis=2)
confidence=np.clip(1-fb/2,0,1)*np.clip((12-mag)/6,0,1)
# Strong source borders, alpha borders, and all semantic designs remain source-derived.
dx=cv2.Sobel(orig.astype('float32'),cv2.CV_32F,1,0,ksize=3)/8
dy=cv2.Sobel(orig.astype('float32'),cv2.CV_32F,0,1,ksize=3)/8
grad=np.max(np.sqrt(dx*dx+dy*dy),axis=2)
semantic=np.zeros((256,256),np.uint8)
semantic[0:112,0:78]=1                    # face, ear, expression
semantic[137:185,18:56]=1                 # both original stars
semantic[153:256,35:46]=1                 # central white zipper
skin=(orig[:,:,0].astype(int)>orig[:,:,2].astype(int)+22)&(orig[:,:,0]>90)
semantic[skin]=1                         # original skin markings and shading
protect=(grad>14)|(alpha<255)|(semantic>0)
protect=cv2.dilate(protect.astype('uint8'),np.ones((3,3),np.uint8))
dist=cv2.distanceTransform(1-protect,cv2.DIST_L2,5)
mask=np.clip(dist/2.5,0,1)*confidence
# Reject mismatched material classes even if optical-flow confidence is high.
ai_small=cv2.resize(ai,(256,256),interpolation=cv2.INTER_AREA)
warped_small=cv2.remap(ai_small,x+flow[:,:,0],y+flow[:,:,1],cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT)
color_gap=np.linalg.norm(orig.astype('float32')-warped_small.astype('float32'),axis=2)
mask*=np.clip((85-color_gap)/50,0,1)
size=(256*SCALE,256*SCALE)
base=cv2.resize(orig.astype('float32'),size,interpolation=cv2.INTER_CUBIC)
base=np.clip(base,0,255)
# Small source-derived sharpening improves edges without inventing motif geometry.
base=np.clip(base+np.clip((base-cv2.GaussianBlur(base,(0,0),1.1))*0.35,-3,3),0,255)
flow_hi=cv2.resize(flow,size,interpolation=cv2.INTER_LINEAR)*SCALE
hy,hx=np.mgrid[0:size[1],0:size[0]].astype('float32')
ai_hi=cv2.resize(ai.astype('float32'),size,interpolation=cv2.INTER_CUBIC)
registered=cv2.remap(ai_hi,hx+flow_hi[:,:,0],hy+flow_hi[:,:,1],cv2.INTER_CUBIC,borderMode=cv2.BORDER_REFLECT)
# Removing low frequencies excludes the draft's altered shapes, shading, and color scheme.
residual=registered-cv2.GaussianBlur(registered,(0,0),8)
residual=np.clip(residual,-18,18)
mask_hi=cv2.resize(mask,size,interpolation=cv2.INTER_LINEAR)
protect_hi=cv2.resize(protect,size,interpolation=cv2.INTER_NEAREST)>0
mask_hi[protect_hi]=0
rgb=np.uint8(np.rint(np.clip(base+residual*mask_hi[:,:,None]*1.1,0,255)))
a=cv2.resize(alpha,size,interpolation=cv2.INTER_NEAREST)
result=np.dstack([rgb,a]); baseline=np.dstack([np.uint8(np.rint(base)),a])
Image.fromarray(result).save(OUT/'stella_body_psp_2048.png')
Image.fromarray(baseline).save(OUT/'source_only_2048.png')
Image.fromarray(np.uint8(np.clip(registered,0,255))).resize((1024,1024)).save(OUT/'registration_diagnostic.jpg',quality=93)
Image.fromarray(np.uint8(mask_hi*255)).resize((1024,1024)).save(OUT/'detail_mask.png')
Image.fromarray(src).resize(size,Image.Resampling.NEAREST).save(OUT/'original_nearest_2048.png')
Image.fromarray(protect*255).save(OUT/'protected_source_pixels.png')
# Independent readback assertions against the saved output.
reread=np.array(Image.open(OUT/'stella_body_psp_2048.png'))
assert reread.shape==(2048,2048,4)
assert np.array_equal(reread[:,:,3],np.repeat(np.repeat(alpha,8,0),8,1))
assert np.array_equal(reread[:,:,:3][protect_hi],baseline[:,:,:3][protect_hi])
low=cv2.resize(reread[:,:,:3],(256,256),interpolation=cv2.INTER_AREA).astype(float)
original_hash=hashlib.sha256((W/'source/FCHR_P_BRS02_00.png').read_bytes()).hexdigest()
report={'scope':'FCHR_P_BRS02_00 only; PSP costume and source-coordinate layout preserved',
 'input_sha256':original_hash,'output_sha256':hashlib.sha256((OUT/'stella_body_psp_2048.png').read_bytes()).hexdigest(),
 'dimensions':[2048,2048],'scale':8,'mode':'RGBA','alpha_exact_nearest_8x':True,
 'protected_pixels_match_source_only_baseline':True,'protected_source_pixel_count':int(protect.sum()),
 'detail_applied_fraction':float(np.mean(mask_hi>0.05)),
 'mean_source_scale_RGB_error':float(np.mean(np.abs(low-orig))),
 'max_generated_detail_delta':int(np.abs(rgb.astype(int)-baseline[:,:,:3].astype(int)).max()),
 'registration_forward_backward_error_median':float(np.median(fb)),
 'method':'Source RGB interpolation and bounded sharpening; original alpha exact nearest 8x. Farneback registers AI to source, transfers only masked +/-18 high-frequency material residual. Protect original face, skin, stars, zipper, strong edges and alpha boundaries.',
 'limitations':['No new mesh geometry','Source atlas is 256x256; not native 4K artwork','Runtime UV/seam review and exact hash confirmation pending','Auxiliary eye/hair/weapon textures and other costumes unchanged'],
 'game_applied':False,'runtime_verified':False}
(OUT/'validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
# Deliverable comparison sheet, without changing either comparison source.
font_path=r'C:\Windows\Fonts\malgun.ttf'
font=ImageFont.truetype(font_path,26); small=ImageFont.truetype(font_path,19)
canvas=Image.new('RGB',(1600,982),'#101723'); d=ImageDraw.Draw(canvas)
d.text((30,18),'PSP 스텔라 · 원래 의상과 문양을 보존한 8배 질감 후보',font=font,fill='white')
for j,(name,im) in enumerate([('PSP 원본 256px (확대)',Image.fromarray(src)),('보정 후보 2048px',Image.fromarray(result))]):
 x0=30+790*j; d.text((x0,65),name,font=small,fill='#a8c7df');
 canvas.paste(im.convert('RGB').resize((750,750),Image.Resampling.NEAREST if j==0 else Image.Resampling.LANCZOS),(x0,101))
d.text((30,880),'얼굴 · 작은 별 · 큰 별 · 지퍼 · 투명 영역 보존 / 의상 내부에만 생성 질감 제한 반영',font=small,fill='#d6dfec')
d.text((30,918),'게임 내 적용 검증 전 후보 · 모델이나 의상 교체 없음',font=small,fill='#8ba1bb')
canvas.save(OUT/'Stella_comparison.png')
print(json.dumps(report,ensure_ascii=False,indent=2))
