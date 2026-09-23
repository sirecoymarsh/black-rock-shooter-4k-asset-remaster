from pathlib import Path
from PIL import Image
import json,hashlib,shutil
R=Path(r'P:\AI\Codex\projects\black-rock-shooter-hd-ui-fonts');C=Path(__file__).resolve().parent
r=json.loads((R/'qa/field_foliage006_local.json').read_text('utf8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
for p in r['prepared_sources']:
 if p['group_id'] not in ['FM0290','FM0314']:continue
 gid=p['group_id'];o=R/'workspace/gpt-trials'/(gid+'-foliage-v1');o.mkdir(exist_ok=False)
 s=Image.open(p['source']).convert('RGBA');s.resize((s.width*8,s.height*8),Image.Resampling.NEAREST).save(o/'source-nearest8x.png');shutil.copy2(C/(gid+'-foliage-prompt.txt'),o/'prompt.txt')
 m={'group_id':gid,'source':p['source'],'source_rgba_sha256':p['source_rgba_sha256'],'reference':str(o/'source-nearest8x.png'),'reference_sha256':sha(o/'source-nearest8x.png'),'prompt':str(o/'prompt.txt'),'prompt_sha256':sha(o/'prompt.txt'),'tool':'built-in image_gen','model_id':'not exposed','status':'prepared','raw_generated_image_preserved':False,'source_protected_alpha':p['alpha'],'source_protected_alpha_sha256':p['alpha_sha256']}
 (o/'provenance.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),'utf8');print(json.dumps(m))
