import numpy as np
from scipy.ndimage import distance_transform_edt
from PIL import Image

def build(source, first, second):
    size=(source.shape[1]*8,source.shape[0]*8)
    drafts=[np.array(Image.fromarray(p).resize(size,Image.Resampling.LANCZOS)) for p in [first,second]]
    signed=[];colors=[]
    for p in drafts:
        mask=p[:,:,3]>=128
        signed.append((distance_transform_edt(mask)-distance_transform_edt(~mask))*.5)
        idx=distance_transform_edt(~mask,return_distances=False,return_indices=True)
        rgb=p[:,:,:3].copy();rgb[~mask]=rgb[idx[0][~mask],idx[1][~mask]]
        colors.append(rgb.astype(float))
    target=source[:,:,3].mean()
    def alpha_at(t):
        return np.rint(np.clip((1-t)*signed[0]+t*signed[1]+.5,0,1)*255).astype('uint8')
    lo=0.;hi=1.
    assert alpha_at(lo).mean()<target<alpha_at(hi).mean()
    for _ in range(24):
        mid=(lo+hi)*.5
        if alpha_at(mid).mean()<target:lo=mid
        else:hi=mid
    t=(lo+hi)*.5;alpha=alpha_at(t)
    rgb=np.rint(np.clip(colors[0]*(1-t)+colors[1]*t,0,255)).astype('uint8')
    out=np.dstack([rgb,alpha])
    return out,{'mix':t,'source_alpha_mean':float(target),'output_alpha_mean':float(alpha.mean()),'alpha_mass_ratio':float(alpha.mean()/target),'RGB_rule':'Linear mix of draft RGB after nearest opaque color extension into each draft transparent pixels. No source RGB generated or inferred again.','alpha_rule':'Interpolate signed distances of two GPT draft masks, one output-pixel antialias; solve mix for source total alpha mass. This is a new authored contour, NOT exact source alpha or source topology.'}
