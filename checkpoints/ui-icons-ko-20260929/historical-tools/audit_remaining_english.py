"""Read-only source audit and enlarged proofs for the next Korean UI batch."""
from pathlib import Path
import json,sys,math
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding='utf8')
I=json.loads((R/'qa/ui_inventory_expanded.json').read_text('utf8'))
T={t['id']:t for t in I['textures']}
targets=[
('MUI-01','if::menu::if_rec_info.gz::005','if::menu::if_rec_info.gz::001',1),
('MUI-05','if::menu::if_stage_select.gz::014','if::menu::if_stage_select.gz::030',14),
('RUI-007','system.vol::005_if_rsdsys.lpk::016','system.vol::005_if_rsdsys.lpk::013',1),
('RUI-008','system.vol::005_if_rsdsys.lpk::018::015','system.vol::005_if_rsdsys.lpk::018::000',19),
('RUI-009','system.vol::005_if_rsdsys.lpk::018::016','system.vol::005_if_rsdsys.lpk::018::000',20),
('RUI-010','system.vol::005_if_rsdsys.lpk::019::007','system.vol::005_if_rsdsys.lpk::019::010',1),
('RUI-011','system.vol::005_if_rsdsys.lpk::020',None,None),
('RUI-012','system.vol::005_if_rsdsys.lpk::021::004','system.vol::005_if_rsdsys.lpk::021::000',1),
('BUI-001','system.vol::007_if_btlsys.lpk::006::003','system.vol::007_if_btlsys.lpk::006::000',0),
('BUI-002','system.vol::007_if_btlsys.lpk::006::004','system.vol::007_if_btlsys.lpk::006::000',1),
('BUI-003','system.vol::007_if_btlsys.lpk::011::003','system.vol::007_if_btlsys.lpk::011::000',0),
('MUI-19','system.vol::007_if_btlsys.lpk::003','system.vol::007_if_btlsys.lpk::000',0),
]
O=R/'outputs/ui-english-audit';O.mkdir(parents=True,exist_ok=True)
font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',14)
records=[]
for name,aid,sid,slot in targets:
 t=T[aid];im=Image.open(t['png']).convert('RGBA');scale=min(8,1200//im.width,1500//im.height)
 im=im.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST)
 out=Image.new('RGB',(max(650,im.width+55),im.height+60),'#31445b');d=ImageDraw.Draw(out)
 d.text((3,0),name+' '+aid,font=font,fill='white');out.paste(im,(40,40),im)
 for x in range(0,t['width'],16):d.text((40+x*scale,22),str(x),font=font,fill='#ffff55')
 for y in range(0,t['height'],16):d.text((0,40+y*scale),str(y),font=font,fill='#ffff55')
 out.save(O/(name+'.png'))
 rec={'id':name,'asset_id':aid,'source':t['source'],'source_png':t['png'],'sdo':sid,'slot':slot,'size':[t['padded_width'],t['padded_height']]}
 if sid:
  c=next(c for c in I['containers'] if c['id']==sid)
  rec['consumers']=[]
  for r in c['sdo']['records']:
   if r['texture_slot']==slot and 'uv_normalized' in r:
    uv=[round(v*rec['size'][i%2],3) for i,v in enumerate(r['uv_normalized'])]
    rec['consumers'].append({'id':r['id'],'uv':uv,'xywh':r['layout_xywh'],'vertices':r['vertices']})
 records.append(rec)
(O/'consumers.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),'utf8')
for r in records:
 print(r['id'],r['asset_id'])
 for c in r.get('consumers',[]):print(c['id'],c['uv'],c['xywh'])
