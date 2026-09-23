import sys,json,hashlib,urllib.request,datetime
from pathlib import Path
sys.stdout.reconfigure(encoding='utf8')
R=Path(__file__).resolve().parents[1];folder=R/'workspace/local-sr/models';registry=folder/'models.json';q=json.loads(registry.read_text('utf8'))
items=[('001_classicalSR_DF2K_s64w8_SwinIR-M_x4.pth','https://github.com/JingyunLiang/SwinIR/releases/download/v0.0/001_classicalSR_DF2K_s64w8_SwinIR-M_x4.pth'),('LICENSE-SwinIR.txt','https://raw.githubusercontent.com/JingyunLiang/SwinIR/main/LICENSE')]
for name,url in items:
    p=folder/name;known=next((x for x in q['records'] if x['name']==name),None)
    if known:
        assert p.exists() and hashlib.sha256(p.read_bytes()).hexdigest()==known['sha256'];print('VERIFIED',name,flush=True);continue
    if not p.exists():
        req=urllib.request.Request(url,headers={'User-Agent':'BRS-local-SR-model-setup'})
        with urllib.request.urlopen(req,timeout=60) as response:
            assert response.status==200;data=response.read()
        assert len(data)>40_000_000 if name.endswith('.pth') else b'Apache License' in data
        tmp=p.with_suffix(p.suffix+'.download');tmp.write_bytes(data);tmp.replace(p)
    record={'name':name,'source_url':url,'official_repository':'https://github.com/JingyunLiang/SwinIR','path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'downloaded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'task':'classical_sr x4, DF2K, training patch64 window8' if name.endswith('.pth') else 'Apache-2.0 license'};q['records'].append(record);registry.write_text(json.dumps(q,ensure_ascii=False,indent=2),'utf8');print(json.dumps(record),flush=True)
