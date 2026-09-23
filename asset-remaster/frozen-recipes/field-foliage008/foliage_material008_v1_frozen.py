import numpy as np
import cv2
from PIL import Image
from scipy.ndimage import distance_transform_edt,gaussian_filter

def visible_rgb(rgba,threshold):
    visible=rgba[:,:,3]>=threshold
    indices=distance_transform_edt(~visible,return_distances=False,return_indices=True)
    rgb=rgba[:,:,:3].copy();rgb[~visible]=rgb[indices[0][~visible],indices[1][~visible]]
    return rgb

def build(source,donor,gain):
    h,w=source.shape[:2];size=(w*8,h*8)
    mask=donor[:,:,3]>=128
    # A continuous contour offset changes coverage without compositing ghost opacity.
    distance=(distance_transform_edt(mask)-distance_transform_edt(~mask))*.5
    distance=cv2.resize(distance.astype('float32'),size,interpolation=cv2.INTER_LINEAR)*(size[0]/donor.shape[1])
    def alpha_at(offset):return np.rint(np.clip(distance+offset+.5,0,1)*255).astype('uint8')
    target=float(source[:,:,3].mean());lo,hi=-4.,4.
    assert alpha_at(lo).mean()<=target<=alpha_at(hi).mean()
    for _ in range(28):
        middle=(lo+hi)*.5
        if alpha_at(middle).mean()<target:lo=middle
        else:hi=middle
    offset=(lo+hi)*.5;alpha=alpha_at(offset)
    original_rgb=visible_rgb(source,128).astype(float)
    base_small=gaussian_filter(original_rgb,(1.5,1.5,0),mode='reflect')
    base=cv2.resize(base_small,size,interpolation=cv2.INTER_CUBIC)
    donor_rgb=np.asarray(Image.fromarray(visible_rgb(donor,128)).resize(size,Image.Resampling.LANCZOS)).astype(float)
    detail=donor_rgb-gaussian_filter(donor_rgb,(12,12,0),mode='reflect')
    rgb=np.rint(np.clip(base+detail*gain,0,255)).astype('uint8')
    out=np.dstack([rgb,alpha])
    return out,{'source_base_sigma_source_pixels':1.5,'donor_detail_sigma_output_pixels':12,'detail_gain':gain,'donor_opaque_RGB_extension_threshold':128,'alpha_donor_threshold':128,'alpha_AA_width_output_pixels':1.,'alpha_contour_offset_output_pixels':offset,'source_alpha_mean':target,'output_alpha_mean':float(alpha.mean()),'alpha_mass_ratio':float(alpha.mean()/target),'alpha_policy':'Generated fine-leaf contour, constant signed-distance offset fitted to original total alpha. Fine topology is repainted, not source-exact.'}
