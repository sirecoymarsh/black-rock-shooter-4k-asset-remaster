from pathlib import Path
import json,hashlib,shutil
from PIL import Image
R=Path(__file__).resolve().parents[1];P=R/'qa/field_source_review04.json';d=json.loads(P.read_text('utf8'));B=R/'qa/backups/before-field-source04-classification';assert not B.exists()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
# Source appearance is routing evidence, never proof of native material/consumer.
raw='''365|alpha_particles|Brown scattered flecks/vertical dirt spray; sparse alpha support.
366|flat_gradient|Thin pale cream/olive horizontal color strip; no invented material.
387|alpha_mechanical|Dark stepped mechanical beam with thin connectors and alpha openings.
388|alpha_mechanical|Two long tapered angular metal fragments; silhouette and bright seams protected.
389|mechanical_atlas|Complex dark machine atlas, rails, plates and small circular emblem-like part; graphic identity unresolved.
390|alpha_folded_structure|Folded angular dark sheet/beam with thin right border; intended diagonal facets.
391|opaque_folded_material|Dark faceted/crumpled sheet with straight seams; trial material only until facet checks.
392|protected_frame|Large right triangular frame and two narrow strips; alpha/straight edges protected.
393|structured_panel|Horizontal bands and fine diagonal lattice engraving; repeat/layout protected.
394|protected_checker|Distorted bordered checker design on damaged ornamental surface; dedicated checker contract.
395|mechanical_atlas|Outlined polygon plates and flat white rectangular mark; no invented text.
396|opaque_folded_material|Soft dark folded diagonal ridges and horizontal lower edge; preserve original bends.
397|protected_curved_frame|Rounded rectangular metal ring with open center; preserve intentional curved corners.
398|alpha_mechanical|Long horizontal part and segmented angular cutout grille with thin connectors.
399|alpha_mechanical|Dark elongated tapered handle/column, alpha max254; weak tip support must survive.
400|alpha_folded_structure|Diagonal bent metal bracket on straight horizontal/vertical frame; preserve facets.
401|alpha_folded_structure|Two narrow upper rods and twisted pointed hanging sheet.
402|nearopaque_structured|Dark outlined polygon plates and white label-like rectangle; alpha239..255, graphic protected.
403|alpha_folded_structure|Vertical rail joined to knotted/tapered jagged fragment.
404|alpha_folded_structure|Folded diagonal bar turning down to a broad triangular base.
405|alpha_folded_structure|Forked angular folded dark structure with broad arms and notches.
406|protected_frame|Disconnected top crossbar, paired diagonal plates and bottom zigzag ring; alpha counts protected.
407|opaque_structured_material|Dark plane with seams, rectangular recessed inset and right vertical partition.
408|alpha_mechanical|Upper ribbed rectangular fixture and lower angular hexagonal frame.
409|alpha_mechanical|Very long slender bent dark-purple rail with thin side strips.
410|alpha_mechanical|Large curved segmented purple mechanical arc; do not straighten intentional curve.
411|architecture|Pale ornate facade with paired arched dark windows; arches and joints protected.
412|architecture|Pale facade with short left pair and tall right pair of rectangular windows.
413|architecture|Pale facade with two groups of mullioned rectangular windows.
414|alpha_ornament|Suspended gray ornate tapered tower/finial with many thin cutouts.
415|protected_frame|Tan upright with multiple X-braces, diagonal perspective beams and weak alpha max253.
416|alpha_natural_faceted|Purple jagged rock/crystal ridge with bright planar edges; alpha silhouette protected.
418|alpha_mechanical|Purple variant of ribbed fixture/angular frame; distinct RGBA, not assumed interchangeable.
424|opaque_masonry|Tan irregular stone blocks with roughly horizontal courses; mortar alignment needs review.
430|protected_checker|Dark ornamental surface containing three checker islands and fine decorative border.
431|city_illustration|Dark aerial city/rubble texture with tiny distinct building/window graphics.
432|alpha_mechanical|Long upright strip and separate bent zigzag tube; intended angular bends and thin links.
433|alpha_ornament|Dark tapering suspended architectural ornament with sharp tips and cutouts.
434|alpha_city_illustration|Pale aerial ruined-city strip with a tall central tower; building shapes protected.
435|alpha_ornament|Separate ornate finials/chains, hanging links and radial mechanical shapes.
436|architecture|Thin pale facade strip with several different rectangular window groups.
437|alpha_folded_structure|Thin green-black curved strip with bright jagged seams.
438|city_illustration|Dark aerial city/buildings; distinct source from431, window identity protected.
439|alpha_ornament|Gray hanging pointed ornament with weak stippled edge detail.
440|alpha_ornament|Dark complex symmetric hanging structure with narrow wires and curled lower point.
441|alpha_ornament|Thin vertical strip with many jagged projecting spikes.
442|alpha_mechanical|Several separated skinny rods/spines and two wing-like angular parts.
443|alpha_ornament|Tall high-detail green-black hanging filigree structure with fragile connectors.
444|protected_checker|Faded gray checker islands within decorative field; source design cannot be blurred away.
445|alpha_city_illustration|Faded green aerial ruined-city strip; thin skyscraper windows and building outline.
446|alpha_ornament|Tall pale stippled ornament with narrow lower point and many small alpha gaps.
447|alpha_mechanical|Very dark red irregular body fragment with several sharp internal openings.
448|city_illustration|Dense dark city/rubble tile with several upright skyscraper shapes.
449|alpha_ornament|Tall dark ornate tower with ringed body, sharp lower point and delicate hanging strands.
450|alpha_ornament|Bright gray tapered hanging finial, partially shaded top and fragile lower tip.
451|alpha_ornament|Faded pale vertical jagged spike strip, not an opaque material tile.
452|city_illustration|Faded green aerial city tile with rectangular building/window motifs.
454|architecture_ornament|Gothic pointed facade with circular rose-window design and lower arch.
455|architecture_ornament|Gothic paired tall lancet windows and dense carved masonry border.
456|opaque_masonry|High-contrast irregular pale stone/block material with coarse dark divisions.
457|architecture_ornament|Dense horizontal louver/step pattern beside tall carved recessed panel.
458|alpha_ornament|Narrow pointed gothic finial/pinnacle silhouette with internal engraved design.
459|protected_lattice|Multiple X-brace/grille strips and large curved rail; thin alpha intersections.
460|protected_lattice|Three large diamond/X braces inside tall parallel uprights; alpha grid topology.
462|protected_ornament|Symmetric multi-point star/cross carving and border; preserve motif topology.
465|opaque_masonry|Pale mottled wall with staggered dark courses; structured mortar must not bend.
466|opaque_natural|Pale mottled stone/plaster surface without a regular grid.
467|protected_rails|Four narrow vertical gray strips with transparent gaps and unequal shading.
472|architecture_ornament|Carved tower with narrow upper slit and large rounded lower arch cutout.
473|opaque_veined_material|Coarse gray stone-like field with broad dark diagonal veins; do not invent regular tiles.
474|architecture_ornament|Carved stone wall and a pointed recessed window, dense trim on left.
475|alpha_architecture|Partial ornate arch/window with right broken edge and narrow tower fragment.
476|opaque_natural|Heavily striated gray stone/wood-like surface; horizontal strata irregular by design.
477|figurative_ornament|Gray sculpted head/bust relief in lower-right area; identity/form protected.
480|nearopaque_natural|Gray cracked stone-like surface alpha225..255; preserve source alpha separately.
481|structured_material_atlas|Stone slabs, narrow channels and distinct rectangular atlas partitions.
482|nearopaque_mechanical|Tall silver/black plate-and-rod atlas, alpha1..255; preserve sharp outlined parts.
483|alpha_mechanical|Tall segmented curved silver-black blade/rail with small hooked lower tip.
486|opaque_natural|Gray irregular cracked stone; source cracks meaningful but not architectural grid.
487|protected_ornament|Small high-contrast geometric star/cross symbol; cannot treat as natural grain.
489|protected_checker_flat|Exact4x4 yellow/gray checker; nonuniform alpha64..255 is source data.
490|protected_graphic|Yellow/orange branching orthogonal lightning/circuit-like graphic; retain paths and angles.
493|alpha_mechanical|Several separate curved angular machine pieces and ribbed rectangular strip.
494|nearopaque_natural|Pale coarse stone with horizontal vein and fine grain, alpha239..255.
495|opaque_masonry|Pale block wall with clearly staggered mortar rows; straight grout geometry protected.
496|opaque_structured_material|Wide gray stone cornice/bands above rectangular slab face; no arbitrary line warping.
497|nearopaque_structured|Gray stone strip with a dark horizontal seam, alpha210..255; seam/alpha protected.
498|protected_checker|Four broad alternating dark/light textured quadrants; exact cross boundary protected.
499|opaque_natural|Soft pale cloud/mottled gray shapes; do not sharpen into invented cracks.
500|structured_ornament|Green horizontal panel with pointed rounded inset and long rectangular inset.
501|nearopaque_mechanical|Large stone/metal outlined atlas with thin rails and rectangular sections, alpha254..255.
502|opaque_structured_material|Long gray flat stippled strip with thin bright top/bottom borders.
503|alpha_sphere_illustration|Blue-white swirling sphere/planet with intricate original painted surface and circular alpha.
506|nearopaque_natural|Cracked gray stone alpha225..255; related to480 but distinct source not assumed equivalent.
508|protected_chain|Seven ring-like links on one narrow horizontal line; count and thin alpha protected.
509|structured_material_atlas|Tall silver cracked/faceted structure with long narrow straight/angled seams and blocks.
510|alpha_ornament|Large ornate silver panel fragment with broken edge and a separate curved rail corner.
511|alpha_ornament|Tall purple pointed ornamental column with small top crosspiece; intentional curves.
512|alpha_mechanical|Huge dark-purple jagged spiked body/arch fragments with many alpha gaps.
513|alpha_mechanical|Curved spiked skeletal/mechanical fragment plus small ring-link array on right.
514|structured_panel|Dark upper gradient and lower outlined polygon plates with horizontal seam rows.
515|alpha_mechanical|Small curved pointed blade and separate straight pointed part; preserve distinct forms.
516|protected_frame|Tall post with two projecting horizontal arms and thin tapered brackets.
517|text_instrument_atlas|Detailed instrument/console atlas with tiny labels, dials, numerical marks and small icons; no semantic repaint.
518|opaque_soft_material|Soft silver-gray shading atlas with broad highlights; preserve smooth gradients and region boundaries.
519|mechanical_atlas|Tall silver panel with long outlined angular channels and narrow parallel rails.
520|mechanical_atlas|Large silver-gray panel atlas with rectangles, bevels and distinct narrow stripe regions.
521|mechanical_atlas|Silver panel atlas with central X-shaped fixture and angular seams; straight forms protected.
522|mechanical_atlas|Dark device/rail atlas with repeated horizontal lines and small circular details.
523|protected_binary_mask|Small white rectangle with transparency; consumer meaning unknown, retain exact source.
524|alpha_cloud|Bright white cloud field with continuous alpha8..254; no binary alpha replacement.
525|opaque_pattern_material|Brown ornamental carpet with floral border and repeating center motifs; pattern fidelity required.
526|flat_geometry_atlas|Cream sliding-door/panel with straight channels, small rivet dots and dark side strip.
527|flat_geometry|Cream horizontal panel bands with thin straight highlight/shadow lines.
528|flat_geometry|Cream inset rectangular panel with subtle border; flat design needs no invented grain.
529|flat_geometry|Flat gray horizontal band with narrow cream top/bottom edges.
530|mechanical_atlas|Gray X-braced panel, right small inset and tan coarse side material; separate atlas regions.
531|structured_panel|Pale gray strip with horizontal seam and rivet row; exact counts/diagonal lower lighting.
532|alpha_ornament|Cream curled bracket, round clock face and separate straight trim strips; clock markings protected.
533|opaque_pattern_material|Salmon-colored vertical drape/column with white curled ornament at lower edge.
534|alpha_pattern|Torn salmon pennant with diamond ornament and several pale decorative shapes; preserve design/tear.
535|text_illustration_identity|Hanging noticeboard covered with small illustrated/text paper scraps; semantic typography protected.
536|furniture_atlas|Brown carved furniture panels and four repeated silver handles; counts, relief and wood material protected.
537|furniture_atlas|Carved dark furniture, two drawer handles and separate scrolling side pattern.
538|furniture_atlas|Tall carved wooden door/panel and narrow scrollwork strip; intentional curved inset preserved.
539|portrait_illustration|Painted older light-haired man portrait below decorative cream cornice; identity/style protected.
540|protected_graphic|Narrow colored stained-glass-like decoration with white floral islands; alpha/graphic protected.
541|furniture_material_atlas|Two curved carved dark panel plates and pale fabric inset; partitions/ornaments protected.
542|alpha_ornament|Thin curled dark scroll bracket and partial left connector; preserve intentional arcs.
543|mechanical_atlas|Dark device panels, buttons, circular openings and striped vent sections.
544|alpha_ornament|Silver/white carved arch fragment with irregular broken top, thin supports and linework.
545|mechanical_atlas|Dark purple console/panel atlas with cyan indicator; straight inset/stripe geometry.
552|protected_lattice|Two separate dark rectangular grilles with fine crossing alpha; inspect count/phase.
561|protected_rails|Four narrow vertical blue-gray bars; exact spacing and alpha support.
576|alpha_landscape_fx|Large pale blue-white horizon/cloud/ice band with separate thin lower strip; partition-aware alpha work.'''
notes={int(line.split('|',2)[0]):line.split('|',2)[1:] for line in raw.splitlines()}
assert len(notes)==135 and {f'FM{i:04d}' for i in notes}=={v['group_id'] for v in d['files']}
selected=[391,396,407,424,456,465,466,473,476,480,486,494,495,496,499,502,506,518,525,533]
B.mkdir(exist_ok=False);shutil.copy2(P,B/P.name)
for v in d['files']:
 im=Image.open(v['source']).convert('RGBA');assert hashlib.sha256(im.tobytes()).hexdigest()==v['source_rgba_sha256'];assert sha(v['source_ptm'])==v['source_ptm_sha256'];cl,note=notes[int(v['group_id'][2:])];v.update(classification=cl,source_visual_note=note,source_review='directly_inspected_by_Codex_internal',selected_for_field_sr005=int(v['group_id'][2:]) in selected)
for p in d['pages']:assert sha(p['path'])==p['sha256'];p['review_status']='directly_inspected_by_Codex_internal'
d['classification_summary']={cl:sum(v['classification']==cl for v in d['files']) for cl in sorted({n[0] for n in notes.values()})};d['selected_for_local_comparison']=[f'FM{i:04d}' for i in selected];d['complete_novel_decoded_field_source_routing_count']=351;d['routing_limit']='Only source appearance of351 novel decoded field groups, not battle-equivalent225 consumer validation, undecoded assets or full game denominator.';P.write_text(json.dumps(d,ensure_ascii=False,indent=2),'utf8');print(json.dumps({'classified':len(notes),'total_novel_routed':351,'local_comparison':len(selected)}))
