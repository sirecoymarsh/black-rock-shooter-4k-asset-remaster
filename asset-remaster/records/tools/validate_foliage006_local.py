from pathlib import Path
import sys,json,hashlib,importlib.util
sys.dont_write_bytecode=True
import numpy as np
from PIL import Image,ImageFilter
R=Path(r'P:\AI\Codex\projects\black-rock-shooter-hd-ui-fonts');Q=R/'qa/field_foliage006_local_validation.json';assert not Q.exists()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text('utf8'))
paths=[R/'qa'/n for n in ['field_foliage006_local.json','field_foliage006_matte.json','field_foliage006_priors.json']]
base,matte,priors=[read(p) for p in paths]
assert matte['prior_report_sha256']==sha(paths[0]);assert priors['matte_report_sha256']==sha(paths[1])
assert sha(base['alpha_program'])==base['alpha_program_sha256']
spec=importlib.util.spec_from_file_location('foliage006_frozen_validation',base['alpha_program']);helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
preps={p['group_id']:p for p in base['prepared_sources']};alpha_checks={};arrays={}
for gid,p in preps.items():
 a=np.asarray(Image.open(p['source']).convert('RGBA'));arrays[gid]=a
 assert hashlib.sha256(a.tobytes()).hexdigest()==p['source_rgba_sha256'];assert sha(p['source_ptm'])==p['source_ptm_sha256']
 aa,unpatched,junctions=helper.make_alpha(a[:,:,3]);assert np.array_equal(aa,np.asarray(Image.open(p['alpha']))) and np.array_equal(unpatched,np.asarray(Image.open(p['alpha_unrepaired']))) and junctions==p['diagonal_junctions']
 assert np.array_equal(aa[4::8,4::8],a[:,:,3]);want=helper.topology(a[:,:,3]>0);thresholds=sorted({1,255}|{int(t)+1 for t in np.unique(aa) if 0<int(t)<255});obs={str(t):helper.topology(aa>=t) for t in thresholds};assert obs==p['threshold_topology'] and all(z==want for z in obs.values())
 nearest=np.repeat(np.repeat(a[:,:,3],8,axis=0),8,axis=1);changed=aa!=unpatched;assert np.all(nearest[changed]==255);ratio=float(aa.sum()/64/a[:,:,3].sum());assert abs(ratio-p['alpha_mass_ratio'])<1e-12 and .98<ratio<1.02
 for key in ['input','alpha','alpha_unrepaired']:assert sha(p[key])==p[key+'_sha256']
 inp=Image.fromarray(helper.prepare_rgb(a)).filter(ImageFilter.GaussianBlur(.25));inp=np.pad(np.asarray(inp),((8,8),(8,8),(0,0)),mode='reflect');assert np.array_equal(inp,np.asarray(Image.open(p['input'])))
 alpha_checks[gid]={'source_topology':want,'all_integer_thresholds_covered':True,'distinct_masks_tested':len(thresholds),'source_centers_exact':True,'mass_ratio':ratio,'junctions':len(junctions),'changed_pixels_from_unpatched_SDF':int(changed.sum()),'junction_changes_inside_source_nearest_foreground':True,'alpha_reproduced_exactly':True}
for p in matte['inputs']:
 a=arrays[p['group_id']];inp=Image.fromarray(a[:,:,:3]).filter(ImageFilter.GaussianBlur(.25));inp=np.pad(np.asarray(inp),((8,8),(8,8),(0,0)),mode='reflect');assert np.array_equal(inp,np.asarray(Image.open(p['input']))) and sha(p['input'])==p['input_sha256']
models={};checked=[];pages=[]
for rep,path in zip([base,matte,priors],paths):
 for z in rep['files']:
  for k in ['input','alpha','native_full','native','output']:assert sha(z[k])==z[k+'_sha256']
  m=z['model'];models.setdefault(m['path'],sha(m['path']));assert models[m['path']]==m['sha256']
  s=arrays[z['group_id']];h,w=s.shape[:2];full=Image.open(z['native_full']).convert('RGB');native=Image.open(z['native']).convert('RGB');o=Image.open(z['output']).convert('RGBA');assert full.size==((w+16)*4,(h+16)*4) and native.size==(w*4,h*4) and o.size==(w*8,h*8)
  assert np.array_equal(np.asarray(full.crop((32,32,(w+8)*4,(h+8)*4))),np.asarray(native));expected=native.resize(o.size,Image.Resampling.LANCZOS).convert('RGBA');expected.putalpha(Image.open(z['alpha']));assert np.array_equal(np.asarray(expected),np.asarray(o))
  checked.append({'id':z['id'],'group_id':z['group_id'],'path':z['output'],'sha256':z['output_sha256'],'source_input_model_native_output_verified':True,'saved_native_crop_resize_alpha_exactly_replayed':True,'inference_repeated':False,'decision':'not_selected_needs_rework','runtime_verified':False})
 for p in rep['pages']:
  assert sha(p['path'])==p['sha256']
  seen=path==paths[0] or Path(p['path']).stem.endswith('-whole')
  pages.append({**p,'review_status':'directly_inspected_by_Codex_internal' if seen else 'not_inspected_after_whole_view_material_failure'})
last=read(R/'qa/field_geometry010_review.json')
assert sha(R/'qa/field_sr_catalog.json')==last['catalog_after_sha256'];assert sha(R/'qa/architectural_geometry_contract.json')==last['geometry_contract_after_sha256']
for rel,h in last['protected_file_hashes'].items():assert sha(R/rel)==h
pack=R/'workspace/local-sr/observed-review-pack-v2/PSP/TEXTURES/NPUH10126';assert {str(p.relative_to(pack)):sha(p) for p in pack.rglob('*') if p.is_file()}==last['pack_hashes']
assert len(checked)==26 and len(pages)==38 and sum(p['review_status']=='directly_inspected_by_Codex_internal' for p in pages)==26
report={'schema':'brs-field-foliage006-local-validation/v1','previous_goal_turn':'progress: all18 base comparison pages inspected; quality defects changed next action to authored-matte ablation','this_goal_turn':'progress: tested authored RGB matte and two different installed local priors, verified26 local outputs; material failures persist and representative GPT repaint started','reports_sha256':{str(p.relative_to(R)):sha(p) for p in paths},'actual_RGB_passes':26,'new_local_unique_originals':9,'alpha_neural_passes':0,'selected_local_outputs':[],'alpha_checks':alpha_checks,'checked_outputs':checked,'pages':pages,'pages_directly_inspected':26,'pages_not_inspected_after_whole_failure':12,'matte_ablation_conclusion':'Changes some tip sharpness/edge colors but does not remove melted foliage or cracked-plane canopy interpretation. Hidden-RGB fill is not established as the sole cause.','alternative_prior_conclusion':'SwinIR adds obvious ringing/pixel-grid artifacts. Anime6B flattens plant/tree surfaces. Neither resolves the representative2 source material failures. Do not continue a blind local-prior or grain-strength sweep.','protected_file_hashes':last['protected_file_hashes'],'pack_hashes':last['pack_hashes'],'catalog_before_sha256':last['catalog_after_sha256'],'geometry_contract_before_sha256':last['geometry_contract_after_sha256'],'limits':['Topology preservation and source-center alpha are mathematical checks only; source mass changes by at most1.14percent, and runtime alpha testing remains unverified.','All26 RGB outputs were produced by actual local inference. Postprocessing is neural4x then Lanczos2x, not native neural8x.','No local candidate is selected from these attempts. New unique9 originals are not yet reflected in final catalog; defer catalog change to complete batch review.'],'runtime_verified':False,'release_eligible':False}
Q.write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False),'utf8');print(json.dumps({'outputs_verified':26,'source_alpha_recipes_replayed':9,'pages_seen':26,'selected':0}))
