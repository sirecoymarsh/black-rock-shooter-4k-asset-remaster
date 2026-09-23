"""Changed material premise: faint fine glass texture plus planar reflection,
not enlarged material cracks. FM0364 pane bounds include source top fragments."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1]
original=R/'tools/rebuild_facades006.py';text=original.read_text('utf8')
text=text.replace('field_geometry006_facades_v1.json','field_geometry006_facades_v2.json').replace('source-alpha-v1','source-alpha-v2').replace('source-frame-glass-v1','source-frame-glass-v2').replace("name+'-v1.png'","name+'-v2.png'").replace('glass-material-donor.png','glass-material-donor-v2.png')
text=text.replace("glassbox=[46,45,49,52]","glassbox=[46,45,49,52]")
text=text.replace("glasspath=R/", "spec['FM0364']['panes']=[[6,4,20,23],[25,4,40,23],[44,4,65,23],[70,5,90,23],[94,5,106,23],[112,4,122,23],[5,42,36,59],[49,42,66,63],[68,42,85,63],[99,42,122,59]]\nglasspath=R/",1)
text=text.replace("fine=patch-gaussian_filter(patch,(8,8,0),mode='nearest')","fine=patch-gaussian_filter(patch,(1.2,1.2,0),mode='nearest')")
text=text.replace("gray=mean+5*np.tanh(fine*.5/5)","gray=mean+2*np.tanh(fine*.25/2);gray+=np.linspace(-3,3,c-a)[None,:,None]+np.linspace(5,-5,d-b)[:,None,None]")
text=text.replace("rgb[edge]+=np.array([9,10,11])","rgb[edge]+=np.array([16,18,20])")
text=text.replace("'new_local_inference_passes':0,'new_external_calls':1", "'new_local_inference_passes':0,'new_external_calls':0")
text=text.replace("'external_generative_calls':3", "'external_generative_calls':0,'reuses_external_generations':3")
text=text.replace("'new_local_inference_passes':0,'external_generative_calls':0", "'material_refinement':'Large material crack pattern removed by fine residual extraction; mild planar glass reflection and source-bound fracture edge facets. FM0364 top fragments included in pane rectangles.','new_local_inference_passes':0,'external_generative_calls':0")
generated=R/'workspace/local-sr/field-geometry006/rebuild_facades006_v2_frozen.py';generated.write_text(text,'utf8');exec(compile(text,str(generated),'exec'),{'__file__':str(original),'__name__':'__main__'})
p=R/'qa/field_geometry006_facades_v2.json';d=json.loads(p.read_text('utf8'));d['reconstruction_program']=str(generated);d['reconstruction_program_sha256']=hashlib.sha256(generated.read_bytes()).hexdigest();d['parent_report_sha256']=hashlib.sha256((R/'qa/field_geometry006_facades_v1.json').read_bytes()).hexdigest();p.write_text(json.dumps(d,ensure_ascii=False,indent=2),'utf8')
