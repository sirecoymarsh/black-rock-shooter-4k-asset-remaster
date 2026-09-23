"""Create a separately named build from the frozen, verified UI geometry builder."""
from pathlib import Path
R=Path(r'P:\AI\Codex\projects\black-rock-shooter-hd-ui-fonts')
s=(R/'tools/build_ui_v3.py').read_text('utf8')
s=s.replace('import ui_geometry_v3 as geometry','import ui_geometry_v3 as geometry\nimport font_heritage as heritage')
s=s.replace("if geometry.patch(a['index'],im,sys.modules[__name__]):pass", "if a['index']==19:\n  active['geometry_review']='Original status abbreviations retained pixel-exact to preserve Latin letterforms; no new HD letterform claim'\n elif geometry.patch(a['index'],im,sys.modules[__name__]):pass")
s=s.replace("FONT=Path(r'C:\\Windows\\Fonts\\NotoSansKR-VF.ttf')",'FONT=heritage.FONT')
start=s.index('@lru_cache(None)\ndef font(size):');end=s.index('\ndef mark(box):',start)
s=s[:start]+s[end:]
start=s.index('def make_text(');end=s.index('\ndef draw_box(',start)
s=s[:start]+'make_text=heritage.make_text\n'+s[end:]
s=s.replace('Korean labels rerasterized from Noto Sans KR Bold','Korean labels rerasterized from Orbit Regular using the documented original-design rendering profile')
s=s.replace("'font':str(FONT)","'font_profile':heritage.PROFILE,'font':str(FONT)")
s=s.replace('sorted(geometry.CORRECTED_IDS)','sorted(geometry.CORRECTED_IDS-{19})').replace('sorted(geometry.REVIEWED_LEGACY_IDS)','sorted(geometry.REVIEWED_LEGACY_IDS|{19})')
for a,b in [('build-v3/','build-v4/'),('ui_candidates_v3','ui_candidates_v4'),('ui_bindings_v3.json','ui_bindings_v4.json'),('ui_build_v3.json','ui_build_v4.json'),('brs-hd-ui/v3','brs-hd-ui/v4'),('ui_comparison_v3_','ui_comparison_v4_')]:s=s.replace(a,b)
(R/'tools/build_ui_v4.py').write_text(s,'utf8')
for source,target in [('review_ui_v3.py','review_ui_v4.py'),('review_remaining_ui.py','review_remaining_ui_v4.py')]:
 s=(R/'tools'/source).read_text('utf8').replace('ui_candidates_v3','ui_candidates_v4').replace('ui_build_v3.json','ui_build_v4.json').replace('ui_v3_','ui_v4_').replace('lock_on_before_after.png','lock_on_heritage.png').replace('ui_remaining_review.json','ui_remaining_review_v4.json').replace('ui_menu_geometry_final.png','ui_menu_heritage.png').replace('ui_hud_geometry_final.png','ui_hud_heritage.png')
 if source=='review_remaining_ui.py':
  s=s.replace('ims={};checks=[];issues=[];ink=[]', "# UI-19 has no translated label: retain its original Latin abbreviation atlas.\nprotected[19]=[(0,0,256,48)]\nold_text[19]=[]\nims={};checks=[];issues=[];ink=[]")
 (R/'tools'/target).write_text(s,'utf8')
