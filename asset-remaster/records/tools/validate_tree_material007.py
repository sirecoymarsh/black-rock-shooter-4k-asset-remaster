from pathlib import Path
import sys, json, hashlib, importlib.util, xml.etree.ElementTree as ET
sys.dont_write_bytecode = True
import numpy as np
from PIL import Image
from scipy.ndimage import label

R = Path(r'P:\AI\Codex\projects\black-rock-shooter-hd-ui-fonts')
DEST = Path(__file__).with_name('field_foliage007_validation.json')
def read(p): return json.loads(Path(p).read_text('utf8'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def arr(p): return np.asarray(Image.open(p).convert('RGBA'))
def normalized(v): return json.loads(json.dumps(v))
def topology(mask):
    labels, n = label(mask, np.ones((3,3),int))
    back, k = label(~mask, [[0,1,0],[1,1,1],[0,1,0]])
    edge = set(np.r_[back[0],back[-1],back[:,0],back[:,-1]])
    return {'foreground_8_components':int(n), 'background_4_enclosed_holes':sum(i not in edge for i in range(1,k+1))}

last = read(R/'qa/field_foliage006_review.json')
audit = read(R/'qa/field_foliage007_source_audit.json')
catalog = read(R/'qa/field_sr_catalog.json')
assert sha(R/'qa/field_sr_catalog.json') == last['catalog_after_sha256'] == audit['catalog_before_sha256']
assert sha(R/'qa/architectural_geometry_contract.json') == last['geometry_contract_after_sha256'] == audit['geometry_contract_before_sha256']
for rel, h in last['protected_file_hashes'].items(): assert sha(R/rel) == h
pack = R/'workspace/local-sr/observed-review-pack-v2/PSP/TEXTURES/NPUH10126'
assert {str(p.relative_to(pack)):sha(p) for p in pack.rglob('*') if p.is_file()} == last['pack_hashes']
previous = [g['candidate'] for g in catalog['groups'] if g['candidate']]
assert len(previous) == 109
for c in previous: assert sha(c['path']) == c['sha256']
local = read(R/'qa/field_foliage006_local.json')
assert sha(R/'qa/field_foliage006_local.json') == last['source_reports_sha256']['qa\\field_foliage006_local.json']
model = next(m for m in read(R/'workspace/local-sr/models/models.json')['records'] if m['name']=='RealESRGAN_x4plus.pth')
assert sha(model['path']) == model['sha256']
provenance_path = R/'workspace/gpt-trials/FM0314-foliage-v1/provenance.json'
prov = read(provenance_path)
for key in ['prompt','reference','source_protected_alpha']: assert sha(prov[key]) == prov[key+'_sha256']
assert sha(prov['raw_generated_image']) == prov['raw_sha256']
donor = arr(prov['raw_generated_image'])
for p in audit['files']:
    assert sha(p['source_ptm']) == p['source_ptm_sha256']
    assert hashlib.sha256(arr(p['source']).tobytes()).hexdigest() == p['source_rgba_sha256']
report_paths = [R/'qa'/f'field_foliage007_tree314_v{i}.json' for i in [1,2,3]] + [R/'qa/field_foliage007_trees_v4.json']
reports = [read(p) for p in report_paths]
checked = []
pages = []
for p in audit['pages']:
    assert sha(p['path']) == p['sha256']
    pages.append({**p, 'review_status':'directly_inspected_by_Codex_internal'})
for version, rep in enumerate(reports,1):
    assert sha(rep['program']) == rep['program_sha256']
    assert sha(rep['GPT_donor']) == rep['GPT_donor_sha256'] == prov['raw_sha256']
    spec = importlib.util.spec_from_file_location(f'tree007_v{version}_replay',rep['program'])
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    if version < 4:
        assert sha(rep['vector']) == rep['vector_sha256']
        lines = ET.parse(rep['vector']).getroot().findall('{http://www.w3.org/2000/svg}polyline')
        assert len(lines) == len(mod.TRACKS)
        for line, track in zip(lines,mod.TRACKS):
            nodes = [[float(z) for z in p.split(',')] for p in line.attrib['points'].split()]
            assert nodes == [list(n[:2]) for n in track['nodes']]
    else:
        assert rep['source_audit_sha256'] == sha(R/'qa/field_foliage007_source_audit.json')
        assert normalized(mod.TRACKS) == reports[2]['diagnostics']['tracks']
        assert normalized(mod.CANOPY_BOTTOM) == reports[2]['diagnostics']['canopy_bottom']
        leaf = donor[mod.LEAF_BOX[1]:mod.LEAF_BOX[3],mod.LEAF_BOX[0]:mod.LEAF_BOX[2],3]
        bark = donor[mod.BARK_BOX[1]:mod.BARK_BOX[3],mod.BARK_BOX[0]:mod.BARK_BOX[2],3]
        assert int(leaf.min()) >= 240 and int(bark.min()) >= 240
    for p in rep['pages']:
        assert sha(p['path']) == p['sha256']
        seen = version != 2 or Path(p['path']).stem.endswith(('main-trunk','fork-right'))
        pages.append({**p,'review_status':'directly_inspected_by_Codex_internal' if seen else 'not_inspected_after_v2_material_band_failure'})
    for p in rep.get('files',[rep]):
        for key in ['source_ptm','parent','output','mask']: assert sha(p[key]) == p[key+'_sha256']
        source, parent, output = arr(p['source']), arr(p['parent']), arr(p['output'])
        assert hashlib.sha256(source.tobytes()).hexdigest() == p['source_rgba_sha256']
        parent_rec = next(q for q in local['files'] if q['id']==p['group_id']+'-photo')
        assert p['parent_sha256'] == parent_rec['output_sha256']
        expected, mask, layers, diag = mod.build(source,parent,donor)
        assert np.array_equal(output, expected)
        assert normalized(diag) == p['diagnostics']
        assert np.array_equal(np.asarray(Image.open(p['mask'])),np.rint(mask*255).astype('uint8'))
        assert output.shape == (1024,1024,4) and np.isfinite(mask).all()
        outside = mask == 0
        assert np.array_equal(output[:,:,:3][outside],parent[:,:,:3][outside])
        assert np.array_equal(output[1000:],parent[1000:])
        assert np.array_equal(output[108*8:,:28*8],parent[108*8:,:28*8])
        assert np.array_equal(output[4::8,4::8,3],source[:,:,3])
        yy,xx = np.mgrid[:1024,:1024]
        boundary = np.interp((np.arange(1024)+.5)/8,[z[0] for z in mod.CANOPY_BOTTOM],[z[1] for z in mod.CANOPY_BOTTOM])
        canopy = np.clip((boundary[None,:]-(yy+.5)/8)/2+.5,0,1)
        assert np.array_equal(output[:,:,3][canopy==0],parent[:,:,3][canopy==0])
        rec = {'id':p['id'],'group_id':p['group_id'],'path':p['output'],'sha256':p['output_sha256'],'RGBA_recipe_reproduced':True,'source_center_alpha_exact':True,'outside_float_mask_RGB_exact_parent':True,'below_canopy_alpha_exact_parent':True,'bottom_source_rows125_to127_RGBA_exact_parent':True,'lower_left_source_box_0_108_28_128_RGBA_exact_parent':True,'alpha_mass_ratio':diag['alpha_mass_ratio'],'program':rep['program'],'program_sha256':rep['program_sha256'],'runtime_verified':False,'release_eligible':False}
        if version == 4:
            alpha = output[:,:,3]
            coarse = np.asarray(Image.fromarray(alpha).resize((128,128),Image.Resampling.BOX)) >= 128
            sm = source[:,:,3] >= 128
            rec['source_scale_alpha_IoU_at128'] = float((coarse&sm).sum()/(coarse|sm).sum())
            rec['source_scale_alpha_mask_disagreements'] = int((coarse!=sm).sum())
            rec['source_topology'] = topology(sm)
            rec['output_topology_by_threshold'] = {str(t):topology(alpha>=t) for t in [1,64,128,192,254,255]}
            labels,n = label(alpha>=128,np.ones((3,3),int))
            represented = set(labels[4::8,4::8][sm])
            counts = np.bincount(labels.ravel())
            extra = [int(counts[i]) for i in range(1,n+1) if i not in represented]
            rec['alpha128_components_without_source_center'] = {'count':len(extra),'max_output_pixels':max(extra,default=0),'total_output_pixels':sum(extra)}
            rec['diagnostics'] = diag
            rec['decision'] = 'static_candidate_pending_final_review'
        else:
            rec['decision'] = 'not_selected'
        checked.append(rec)
        print('VERIFIED',p['id'],flush=True)
assert len(checked)==7 and len(pages)==45 and sum(p['review_status']=='directly_inspected_by_Codex_internal' for p in pages)==41
# Verify each palette's own source class rather than claiming all related textures are identical.
v4 = reports[3]
base = next(p for p in v4['files'] if p['group_id']=='FM0314')
a = arr(base['source']); ac = a[:,:,:3].mean(2) >= base['diagnostics']['source_wood_luma_threshold']
for comparison in v4['source_wood_classes']:
    p = next(p for p in v4['files'] if p['group_id']==comparison['other'])
    b = arr(p['source']); bc = b[:,:,:3].mean(2) >= p['diagnostics']['source_wood_luma_threshold']
    yy,xx = np.mgrid[:128,:128]; region = (a[:,:,3]>0)&(b[:,:,3]>0)&(yy>=82)&(yy<125)&(xx>=45)
    assert int(region.sum()) == comparison['compared_pixels']
    assert int(((ac!=bc)&region).sum()) == comparison['classification_disagreements']
result = {'schema':'brs-field-foliage007-validation/v1','catalog_before_sha256':sha(R/'qa/field_sr_catalog.json'),'geometry_contract_before_sha256':sha(R/'qa/architectural_geometry_contract.json'),'source_reports_sha256':{str(p.relative_to(R)):sha(p) for p in [R/'qa/field_foliage007_source_audit.json',*report_paths]},'GPT_provenance_path':str(provenance_path),'GPT_provenance_sha256':sha(provenance_path),'local_parent_model':model,'checked_outputs':checked,'source_and_comparison_pages':pages,'directly_inspected_pages':41,'protected_file_hashes':last['protected_file_hashes'],'pack_hashes':last['pack_hashes'],'previous109_field_candidate_hashes_verified':True,'source_wood_classes':v4['source_wood_classes'],'classification_limit_correction':'316/317 differ in19 jointly opaque lower-source classes each;325 differs in0. Controls are reused only after own-source review, and each output uses its own source RGB, material gate and alpha. This does not establish shared consumers.','actual_new_local_passes':0,'actual_new_external_calls':0,'new_unique_originals':0,'runtime_verified':False}
DEST.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False),'utf8')
print(json.dumps({'validation':str(DEST),'final_diagnostics':[{k:p[k] for k in ['id','alpha_mass_ratio','source_scale_alpha_IoU_at128','source_scale_alpha_mask_disagreements','source_topology','output_topology_by_threshold','alpha128_components_without_source_center']} for p in checked if p['id'].endswith('v4')]}),flush=True)
