import json,hashlib
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1]
a=R/'workspace/sessions/UIF-Q001-font-baseline/captures/font-baseline-window.png'
b=R/'workspace/sessions/UIF-Q002-font-preview/captures/font-preview-window.png'
aa=np.array(Image.open(a).convert('RGB'));bb=np.array(Image.open(b).convert('RGB'));assert aa.shape==bb.shape
boxes={'korean_row1':[614,89,750,127],'korean_row2':[614,131,750,169],'digits_row1':[753,89,807,127],'digits_row2':[753,131,807,169],'plus_icons':[579,91,612,166],'counts':[936,93,978,163]}
metrics={}
for name,(x0,y0,x1,y1) in boxes.items():
 d=np.abs(aa[y0:y1,x0:x1].astype(int)-bb[y0:y1,x0:x1].astype(int));metrics[name]={'changed_pixels':int((d>0).any(2).sum()),'mean_abs_error':float(d.mean()),'max_abs_error':int(d.max())}
crop=(575,86,989,170);out=Image.new('RGB',(840,220),'#152138');dr=ImageDraw.Draw(out);f=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',20)
for y,label,img in [(0,'원본',Image.open(a)),(110,'8배 재렌더링',Image.open(b))]:
 dr.text((5,y+5),label,font=f,fill='white');out.paste(img.crop(crop).resize((828,168),Image.Resampling.NEAREST).crop((0,0,828,82)),(5,y+31))
# Full two-row crops, original pixels; enlargement is not called new detail.
out=Image.new('RGB',(828,400),'#152138');dr=ImageDraw.Draw(out)
for y,label,img in [(0,'원본',Image.open(a)),(200,'8배 재렌더링',Image.open(b))]:
 dr.text((5,y+3),label,font=f,fill='white');out.paste(img.crop(crop).resize((828,168),Image.Resampling.NEAREST),(0,y+30))
out.save(R/'outputs/font_runtime_before_after.png')
report={'scene':'Battle results; 리페어 200 / 리페어 500','baseline':str(a),'preview':str(b),'baseline_sha256':hashlib.sha256(a.read_bytes()).hexdigest(),'preview_sha256':hashlib.sha256(b.read_bytes()).hexdigest(),'roi_metrics':metrics,'visual_review':'Korean is rerasterized and visible in original slots; digits and item icons remain original. Readable on both item rows. This scene is not full repertoire or transition coverage.','gpu_download':'CPU stepping output download failed; CPU resumed; GE frame dump separately captured. No claim of byte-identical GPU replacement yet.'}
(R/'qa/font_runtime_comparison.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(metrics))
