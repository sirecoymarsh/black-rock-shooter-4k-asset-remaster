from pathlib import Path
import sys,json,hashlib,shutil
sys.dont_write_bytecode=True
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from tree_material007 import build,TRACKS,CANOPY_BOTTOM
R=Path(r'P:\AI\Codex\projects\black-rock-shooter-hd-ui-fonts');C=Path(__file__).resolve().parent;O=R/'workspace/local-sr/field-foliage007';P=R/'outputs/field-foliage007';Q=R/'qa/field_foliage007_tree314_v3.json';assert not Q.exists()
def read(p):return json.loads(Path(p).read_text('utf8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
r=read(R/'qa/field_foliage006_local.json');p=next(z for z in r['files'] if z['id']=='FM0314-photo');d=read(R/'workspace/gpt-trials/FM0314-foliage-v1/provenance.json');source=Image.open(p['source']).convert('RGBA');parent=Image.open(p['output']).convert('RGBA');donor=Image.open(d['raw_generated_image']).convert('RGBA');out,mask,layers,diag=build(np.asarray(source),np.asarray(parent),np.asarray(donor));op=O/'FM0314-source-material-v3-8x.png';Image.fromarray(out).save(op);mp=O/'FM0314-source-material-v3-mask.png';Image.fromarray(np.rint(mask*255).astype('uint8')).save(mp);prog=O/'tree_material007_v3_frozen.py';shutil.copy2(C/'tree_material007.py',prog)
guide=Image.new('RGB',(1024,1024),'#18222c');src=source.resize((1024,1024),Image.Resampling.NEAREST);guide.paste(src,(0,0),src);draw=ImageDraw.Draw(guide);font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',15);colors=['#ff7575','#6fea95','#bfff7f','#67cfff','#e18bff','#ffb76b'];svglines=[]
for track,col,layer in zip(TRACKS,colors,layers):
 points=[(x*8,y*8) for x,y,w in track['nodes']];draw.line(points,fill=col,width=2);cont=np.asarray(layer['coverage'])>.5
 from skimage.measure import find_contours
 for contour in find_contours(cont.astype(float),.5):draw.line([(float(x),float(y)) for y,x in contour],fill=col,width=1)
 for x,y,w in track['nodes']:draw.ellipse((x*8-2,y*8-2,x*8+2,y*8+2),fill=col)
 draw.text(points[-1],track['name'],font=font,fill=col)
 svglines.append('<polyline points="'+' '.join(f'{x},{y}' for x,y,w in track['nodes'])+'" fill="none" stroke="'+col+'" stroke-width="0.25"/>')
draw.line([(x*8,y*8) for x,y in CANOPY_BOTTOM],fill='#fff176',width=2);gp=P/'FM0314-source-material-v3-guide.png';guide.save(gp);svg=O/'FM0314-source-material-v3-guide.svg';svg.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128">'+''.join(svglines)+'</svg>','utf8')
rep={'schema':'brs-field-foliage007-tree314/v3','id':'FM0314-source-material-v3','group_id':'FM0314','source':p['source'],'source_ptm':p['source_ptm'],'source_ptm_sha256':p['source_ptm_sha256'],'source_rgba_sha256':p['source_rgba_sha256'],'parent':p['output'],'parent_sha256':p['output_sha256'],'GPT_donor':d['raw_generated_image'],'GPT_donor_sha256':d['raw_sha256'],'output':str(op),'output_sha256':sha(op),'mask':str(mp),'mask_sha256':sha(mp),'program':str(prog),'program_sha256':sha(prog),'vector':str(svg),'vector_sha256':sha(svg),'diagnostics':diag,'new_local_passes':0,'new_external_calls':0,'runtime_verified':False,'release_eligible':False,'pages':[{'path':str(gp),'sha256':sha(gp),'kind':'source-coordinate-geometry-guide','review_status':'pending'}]}
for tag,box in [('whole',None),('canopy',(28,20,68,60)),('main-trunk',(38,80,70,128)),('fork-right',(72,86,112,126)),('lower-left',(0,92,48,128))]:
 can=Image.new('RGB',(1050,810),'#25313c');dr=ImageDraw.Draw(can)
 for row,(matte,mlabel) in enumerate([('#18222c','어두운 배경'),('#dedede','밝은 배경')]):
  for col,(path,title) in enumerate([(p['source'],'원본 · 단순 확대'),(p['output'],'로컬 Photo'),(str(op),'원본 구조 + 잎·나무껍질')]):
   im=Image.open(path).convert('RGBA')
   if box:im=im.crop(box if col==0 else tuple(t*8 for t in box))
   scale=min(320/im.width,340/im.height);im=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.NEAREST if col==0 else Image.Resampling.LANCZOS);bg=Image.new('RGBA',im.size,matte);bg.alpha_composite(im);dr.text((col*350+8,row*405+8),title,font=font,fill='white');dr.text((col*350+8,row*405+30),mlabel,font=font,fill='#c7d1da');can.paste(bg.convert('RGB'),(col*350+(350-bg.width)//2,row*405+58+(340-bg.height)//2))
  pp=P/('FM0314-source-material-v3-'+tag+'.png')
 can.save(pp);rep['pages'].append({'path':str(pp),'sha256':sha(pp),'source_box':box,'review_status':'pending'})
Q.write_text(json.dumps(rep,ensure_ascii=False,indent=2,allow_nan=False),'utf8');print(json.dumps({'diagnostics':diag,'pages':len(rep['pages'])}))



