"""Download official SR weights into this project; never upload game assets."""
import sys, json, hashlib, urllib.request, datetime
from pathlib import Path

sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding='utf8')
R = Path(__file__).resolve().parents[1]
D = R / 'workspace' / 'local-sr' / 'models'
D.mkdir(parents=True, exist_ok=True)
SOURCES = {
    'RealESRGAN_x4plus.pth': 'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth',
    'realesr-general-x4v3.pth': 'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-general-x4v3.pth',
    'realesr-general-wdn-x4v3.pth': 'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-general-wdn-x4v3.pth',
    'LICENSE-Real-ESRGAN.txt': 'https://raw.githubusercontent.com/xinntao/Real-ESRGAN/v0.3.0/LICENSE',
}
records = []
for name, url in SOURCES.items():
    dest = D / name
    if not dest.exists():
        print('Downloading', name, flush=True)
        part = dest.with_suffix(dest.suffix + '.part')
        req = urllib.request.Request(url, headers={'User-Agent': 'BRS-local-SR/1.0'})
        with urllib.request.urlopen(req, timeout=90) as response, part.open('wb') as out:
            while block := response.read(1024 * 1024):
                out.write(block)
        if part.stat().st_size < (100_000 if name.endswith('.pth') else 500):
            raise ValueError('Unexpected download size: ' + name)
        part.replace(dest)
    entry = {'name': name, 'source_url': url, 'path': str(dest),
             'bytes': dest.stat().st_size,
             'sha256': hashlib.sha256(dest.read_bytes()).hexdigest()}
    records.append(entry)
    print(json.dumps(entry), flush=True)
manifest = {'schema': 'brs-local-sr-models/v1', 'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'execution': 'local NVIDIA GPU; no image upload', 'records': records}
(D / 'models.json').write_text(json.dumps(manifest, indent=2), 'utf8')
print('Model preparation complete.', flush=True)
