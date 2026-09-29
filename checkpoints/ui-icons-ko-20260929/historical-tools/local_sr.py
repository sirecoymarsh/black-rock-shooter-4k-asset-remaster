"""Local Real-ESRGAN inference; source assets and other projects stay read-only."""
import sys, hashlib, time
from pathlib import Path
import numpy as np
import torch, spandrel
from PIL import Image

sys.dont_write_bytecode = True
MODEL = Path(r'P:\AI\Codex\projects\fate-extra-psp-korean\work\hd-texture-pack\codex-hd-v1\references\realesrgan\RealESRGAN_x4plus_anime_6B.pth')
MODEL_SHA = 'f872d837d3c90ed2e05227bed711af5671a6fd1c9f7d7e91c911a61f155e99da'
MODEL_URL = 'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.2.4/RealESRGAN_x4plus_anime_6B.pth'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def load_model(path=MODEL, expected_sha=MODEL_SHA):
    digest = sha(path.read_bytes())
    assert digest == expected_sha, ('Model changed', digest)
    state = torch.load(path, map_location='cpu', weights_only=True)
    model = spandrel.ModelLoader().load_from_state_dict(state.get('params_ema', state.get('params', state)))
    assert isinstance(model, spandrel.ImageModelDescriptor)
    assert model.scale == 4 and model.input_channels == model.output_channels == 3
    assert torch.cuda.is_available(), 'Do not silently fall back to another service.'
    torch.set_num_threads(4)
    return model.cuda().eval()

def infer_rgb(model, image):
    """Model channels are RGB. Input/output retain their original normalized positions."""
    rgb = np.asarray(image.convert('RGB'), dtype=np.float32) / 255
    ten = torch.from_numpy(rgb.copy()).permute(2, 0, 1).unsqueeze(0).cuda()
    with torch.inference_mode():
        pred = model(ten)
        assert torch.isfinite(pred).all(), 'Non-finite model output'
        data = pred[0].clamp(0, 1).permute(1, 2, 0).cpu().numpy()
    out = Image.fromarray(np.rint(data * 255).astype(np.uint8), 'RGB')
    assert out.size == (image.width * 4, image.height * 4)
    return out

def provenance():
    return {'model': MODEL.name, 'model_path': str(MODEL), 'model_sha256': MODEL_SHA,
            'official_source': MODEL_URL, 'model_reused_read_only_from': 'Fate/EXTRA HD project',
            'inference': 'local PyTorch CUDA, float32, RGB, evaluation mode',
            'device': torch.cuda.get_device_name(0), 'torch': torch.__version__,
            'spandrel': spandrel.__version__, 'native_neural_scale': 4,
            'final_canvas_scale': 8, 'post_scale': 'Lanczos 2x after neural inference',
            'external_image_generation': False, 'image_upload': False}

def roundtrip_metrics(src, out):
    a = np.asarray(src.convert('RGB'), dtype=np.float32)
    b = np.asarray(out.convert('RGB').resize(src.size, Image.Resampling.LANCZOS), dtype=np.float32)
    delta = b - a
    return {'rgb_mae_0_255': float(np.abs(delta).mean()),
            'rgb_p99_abs_error_0_255': float(np.quantile(np.abs(delta), .99)),
            'rgb_mean_shift_0_255': [float(v) for v in delta.mean(axis=(0,1))],
            'interpretation': 'Source-scale consistency only; not proof of restored true high-resolution detail or visual acceptance.'}
