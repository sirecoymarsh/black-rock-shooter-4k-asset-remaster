"""Create a static, texture-mapped reference viewer; never substitutes PGR game shaders."""
import json,struct,base64,hashlib,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'workspace/pgr_reference';OUT=R/'viewer'
manifest=json.loads((R/'extraction_manifest.json').read_text('utf-8'))

def parse_obj(p):
 vs=[];ns=[];uv=[];ind=[];verts=[];norms=[];tex=[];seen={}
 for line in p.read_text('utf-8').splitlines():
  a=line.split()
  if not a:continue
  if a[0]=='v':vs.append(list(map(float,a[1:4])))
  elif a[0]=='vn':ns.append(list(map(float,a[1:4])))
  elif a[0]=='vt':uv.append(list(map(float,a[1:3])))
  elif a[0]=='f':
   for token in a[1:]:
    if token not in seen:
     t=list(map(int,token.split('/')));v=vs[t[0]-1];n=ns[t[2]-1];u=uv[t[1]-1]
     seen[token]=len(seen);verts.extend([v[0],v[2],-v[1]]);norms.extend([n[0],n[2],-n[1]]);tex.extend(u)
    ind.append(seen[token])
 return {'positions':verts,'normals':norms,'uvs':tex,'indices':ind}

def make_model(code,label,parts):
 folder=R/'extracted/role/body'/code.lower();meshes=[]
 for meshname,matname in parts:
  p=folder/'vc'/(meshname+'VC.obj');g=parse_obj(p)
  mat=json.loads((folder/(matname+'.material.json')).read_text('utf-8'))
  tid=next(v['m_Texture']['m_PathID'] for k,v in mat['m_SavedProperties']['m_TexEnvs'] if k=='_MainTex')
  texobj=next(o for b in manifest['selected'] if b['bundle_name'].endswith('/'+code.lower()+'.ab') for o in b['objects'] if o['path_id']==tid)
  tex=Path(texobj['export']).read_bytes();g.update(name=meshname,texture='data:image/png;base64,'+base64.b64encode(tex).decode(),texture_bytes=tex)
  meshes.append(g)
 return {'name':label,'id':code,'meshes':meshes}
base='R2BlackrockMd010011';alt='R2BlackrockMd019031'
models=[make_model(base,'기본 의상',[(base+n,base+n) for n in ['Body','Cloth','Hair','Face','Eye','Zipper']]),make_model(alt,'추가 의상',[(alt+n,alt+n) for n in ['Body','Upper','Down']]+[(base+n,base+n) for n in ['Hair','Face','Eye']])]

def glb(model):
 doc={'asset':{'version':'2.0','generator':'Codex PGR local reference; static mesh, original diffuse maps; no PGR shader/rig/animation recreation'},'scene':0,'scenes':[{'nodes':[]}],'nodes':[],'meshes':[],'materials':[],'textures':[],'images':[],'samplers':[{'magFilter':9729,'minFilter':9729,'wrapS':10497,'wrapT':10497}],'accessors':[],'bufferViews':[],'buffers':[],'extensionsUsed':['KHR_materials_unlit']};buf=bytearray()
 def view(data,target=None):
  while len(buf)%4:buf.append(0)
  v={'buffer':0,'byteOffset':len(buf),'byteLength':len(data)}
  if target:v['target']=target
  i=len(doc['bufferViews']);doc['bufferViews'].append(v);buf.extend(data);return i
 def acc(vals,components,typ,target):
  fmt='f' if typ==5126 else 'I';vi=view(struct.pack('<'+fmt*len(vals),*vals),target);a={'bufferView':vi,'componentType':typ,'count':len(vals)//components,'type':{1:'SCALAR',2:'VEC2',3:'VEC3'}[components]}
  if components==3:a.update(min=[min(vals[i::3]) for i in range(3)],max=[max(vals[i::3]) for i in range(3)])
  ix=len(doc['accessors']);doc['accessors'].append(a);return ix
 for g in model['meshes']:
  pos=acc(g['positions'],3,5126,34962);nor=acc(g['normals'],3,5126,34962);uv=acc([u if i%2==0 else 1-u for i,u in enumerate(g['uvs'])],2,5126,34962);idx=acc(g['indices'],1,5125,34963)
  im=view(g['texture_bytes']);j=len(doc['meshes']);doc['images'].append({'bufferView':im,'mimeType':'image/png'});doc['textures'].append({'sampler':0,'source':j});doc['materials'].append({'name':g['name'],'doubleSided':True,'alphaMode':'MASK','alphaCutoff':0.15,'pbrMetallicRoughness':{'baseColorTexture':{'index':j},'metallicFactor':0,'roughnessFactor':1},'extensions':{'KHR_materials_unlit':{}}});doc['meshes'].append({'name':g['name'],'primitives':[{'attributes':{'POSITION':pos,'NORMAL':nor,'TEXCOORD_0':uv},'indices':idx,'material':j}]});doc['nodes'].append({'mesh':j,'name':g['name']});doc['scenes'][0]['nodes'].append(j)
 doc['buffers']=[{'byteLength':len(buf)}];s=json.dumps(doc,separators=(',',':')).encode();s+=b' '*((-len(s))%4);buf.extend(b'\0'*((-len(buf))%4));data=struct.pack('<III',0x46546c67,2,12+8+len(s)+8+len(buf))+struct.pack('<II',len(s),0x4e4f534a)+s+struct.pack('<II',len(buf),0x004e4942)+buf
 (OUT/(model['id']+'_static_reference.glb')).write_bytes(data)
 return {'path':str(OUT/(model['id']+'_static_reference.glb')),'sha256':hashlib.sha256(data).hexdigest(),'meshes':len(model['meshes']),'vertices':sum(len(g['positions'])//3 for g in model['meshes']),'triangles':sum(len(g['indices'])//3 for g in model['meshes'])}
summary=[glb(m) for m in models]
for m in models:
 for g in m['meshes']:del g['texture_bytes']
html='''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>블랙 록 슈터 · 로컬 모델 참고</title><style>*{box-sizing:border-box}body{margin:0;background:#111821;color:#e5edf5;font:15px "Segoe UI","Malgun Gothic",sans-serif}header{padding:20px 26px;border-bottom:1px solid #304153;display:flex;flex-wrap:wrap;gap:12px;align-items:center}h1{font-size:20px;margin:0 auto 0 0}button,select,a{color:#deecf5;background:#24384a;border:1px solid #466477;border-radius:7px;padding:9px 12px;text-decoration:none}button:hover{background:#325875}#view{height:calc(100vh - 185px);min-height:400px;position:relative}canvas{width:100%;height:100%;display:block;touch-action:none}#status{position:absolute;top:16px;left:24px;color:#95bcd5}footer{padding:15px 26px;border-top:1px solid #304153;line-height:1.7;color:#b7c8d7}small{color:#8ca7bc}b{color:white}</style><header><h1>블랙 록 슈터 · 모델 참고</h1><select id="model"><option value="0">기본 의상</option><option value="1">추가 의상</option></select><button id="front">앞</button><button id="back">뒤</button><button id="wire">와이어프레임</button><button id="spin">자동 회전</button></header><div id="view"><div id="status">모델 준비 중…</div></div><footer><b>설치된 퍼니싱 데이터에서 추출한 실제 메시·텍스처</b> · 드래그: 회전 · 휠: 확대<br>정적 참고용입니다. 원작의 조명·툰 셰이더·표정·애니메이션은 재현하지 않았습니다.<br><small>캐릭터 텍스처 최대 1024×1024. 4K 원본이나 PSP용 교체 파일이 아닙니다.</small></footer><script>'''
html+=(OUT/'three.min.js').read_text('utf-8')+'\n</script><script>const models='+json.dumps(models,separators=(',',':'))+';\n'
html+='''const host=document.querySelector('#view'),status=document.querySelector('#status');const renderer=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.setClearColor(0x18232e);host.appendChild(renderer.domElement);const scene=new THREE.Scene(),cam=new THREE.PerspectiveCamera(32,1,.001,100);let group,angle=0,elev=.08,radius=3.5,target=new THREE.Vector3(),auto=false,wire=false;const loader=new THREE.TextureLoader();function loadModel(n){if(group)scene.remove(group);group=new THREE.Group();const m=models[n];for(const part of m.meshes){let g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(part.positions,3));g.setAttribute('normal',new THREE.Float32BufferAttribute(part.normals,3));g.setAttribute('uv',new THREE.Float32BufferAttribute(part.uvs,2));g.setIndex(part.indices);let t=loader.load(part.texture);t.colorSpace=THREE.SRGBColorSpace;t.wrapS=t.wrapT=THREE.RepeatWrapping;const mat=new THREE.MeshBasicMaterial({map:t,side:THREE.DoubleSide,alphaTest:.15,wireframe:wire});group.add(new THREE.Mesh(g,mat));}scene.add(group);let box=new THREE.Box3().setFromObject(group),size=box.getSize(new THREE.Vector3());box.getCenter(target);radius=size.y*2.2;angle=0;elev=.03;status.textContent=m.name+' · '+m.meshes.reduce((a,g)=>a+g.indices.length/3,0).toLocaleString()+' 삼각형 · 정적 참고';}function resize(){renderer.setSize(host.clientWidth,host.clientHeight);cam.aspect=host.clientWidth/host.clientHeight;cam.updateProjectionMatrix()}addEventListener('resize',resize);resize();loadModel(0);document.querySelector('#model').onchange=e=>loadModel(+e.target.value);document.querySelector('#front').onclick=()=>{angle=0;elev=.03};document.querySelector('#back').onclick=()=>{angle=Math.PI;elev=.03};document.querySelector('#wire').onclick=()=>{wire=!wire;group.children.forEach(x=>x.material.wireframe=wire)};document.querySelector('#spin').onclick=()=>auto=!auto;let drag=false,lastX,lastY;const c=renderer.domElement;c.onpointerdown=e=>{drag=true;lastX=e.clientX;lastY=e.clientY;c.setPointerCapture(e.pointerId)};c.onpointermove=e=>{if(!drag)return;angle-=(e.clientX-lastX)*.008;elev=Math.max(-1.3,Math.min(1.3,elev+(e.clientY-lastY)*.005));lastX=e.clientX;lastY=e.clientY};c.onpointerup=()=>drag=false;c.onwheel=e=>{e.preventDefault();radius=Math.max(.25,Math.min(12,radius*Math.exp(e.deltaY*.001))) };function frame(){requestAnimationFrame(frame);if(auto)angle+=.004;cam.position.set(target.x+radius*Math.sin(angle)*Math.cos(elev),target.y+radius*Math.sin(elev),target.z+radius*Math.cos(angle)*Math.cos(elev));cam.lookAt(target);renderer.render(scene,cam)}frame();</script></html>'''
(OUT/'BRS_model_reference.html').write_text(html,encoding='utf-8');(OUT/'viewer_manifest.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');print(json.dumps(summary,indent=2))
