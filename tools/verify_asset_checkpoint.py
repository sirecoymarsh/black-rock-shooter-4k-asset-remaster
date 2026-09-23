from pathlib import Path
import json,hashlib,re,subprocess
G=Path(r'P:\AI\Codex\projects\black-rock-shooter-hd-retexture')
manifest=json.loads((G/'asset-remaster/snapshot-manifest.json').read_text('utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for p in manifest['files']:
    target=G/p['path'];assert target.is_file() and target.stat().st_size==p['bytes'] and sha(target)==p['sha256']
paths=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=G).decode('utf8').split('\x00')
forbidden_ext={'.iso','.cso','.chd','.pbp','.elf','.prx','.sav','.ppst','.pth','.safetensors','.exe','.dll','.pem','.key'}
secret=re.compile(rb'gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-proj-[A-Za-z0-9_-]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----')
binary_ext={'.png','.jpg','.jpeg','.webp','.npy','.npz','.zip','.ttf','.otf'}
violations=[]
for rel in paths:
    if not rel:continue
    p=G/rel
    if not p.is_file():continue
    if p.suffix.lower() in forbidden_ext or p.name in {'.env','credentials.json','hosts.yml'}:violations.append({'path':rel,'reason':'excluded source/runtime/model/credential type'})
    if p.stat().st_size>=100*1024**2:violations.append({'path':rel,'reason':'file over100MiB'})
    if p.suffix.lower() not in binary_ext and secret.search(p.read_bytes()):violations.append({'path':rel,'reason':'credential pattern; value not printed'})
assert not violations,violations
print(json.dumps({'snapshot_files_verified':len(manifest['files']),'candidate_counts':manifest['static_candidate_counts'],'pending':manifest['pending_unreviewed_candidates'],'tracked_plus_untracked_files_scanned':len([p for p in paths if p]),'secret_or_large_source_violations':0,'MiB':manifest['tracked_payload_bytes']/1024**2}))
