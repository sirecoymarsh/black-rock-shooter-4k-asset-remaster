"""Source-owned icon regions. Exclusive native-pixel boxes; no text rewrite."""
P='system.vol::005_if_rsdsys.lpk::'
F='system.vol::006_if_fldsys.lpk::'
B='system.vol::007_if_btlsys.lpk::'
M='if::menu::'
SPECS=[]
def add(asset,name,boxes=None,method='neural',**kw):
 SPECS.append(dict(id=f'ICO-{len(SPECS)+1:03}',asset=asset,name=name,boxes=boxes,method=method,**kw))
add(P+'020','공통 버튼·장비·상태 아이콘',[[0,0,64,240]],cells=[16,16])
add(M+'menu_custom.gz::006','커스터마이즈 불꽃',[[0,28,64,64]],'trace')
add(M+'menu_custom.gz::007','무기·패시브 아이콘',[[157,0,214,30]])
add(M+'menu_custom.gz::009','회복·블레이드·열쇠·메뉴 화살표',[[0,28,87,56],[87,4,125,24],[93,48,105,61]])
add(M+'menu_item.gz::006','아이템 상자',[[68,84,100,123]])
add(M+'menu_option.gz::007','설정 도구',[[0,0,60,48]],'trace')
add(M+'if_rec_info.gz::010','트로피',[[0,0,44,48]],'trace')
for n in range(12,32):add(M+f'if_rec_info.gz::{n:03}','훈장 '+str(n-11)+(' 잠금' if n>=22 else ' 획득'))
add(M+'if_rec_info.gz::005','스테이지 배지·L/R·체크·화살표',[[0,0,87,46],[0,30,57,58],[70,35,87,46],[97,35,120,46],[0,59,8,95]])
add(M+'if_rec_info.gz::007','미확인 아이콘',[[0,0,94,48]],'trace')
add(M+'if_stage_select.gz::018','임무 선택 별·알림·선택 링',[[230,0,256,32],[168,34,214,54],[0,32,32,72],[194,53,212,72],[134,32,162,63],[5,2,14,11]])
add(M+'if_stage_select.gz::019','스테이지 큰 별·작은 별',[[0,0,189,187],[214,160,242,200]],'trace')
add(M+'if_stage_select.gz::021','스테이지 링·표식·문장',[[0,0,64,64],[63,11,101,59],[105,0,128,180],[0,64,64,84],[0,84,104,183]],'trace')
add(P+'000::004','공통 대화 X 버튼',[[0,24,16,48]])
add(P+'004','공통 원·별',None,'trace')
add(P+'017','공통 작은 버튼',None)
add(P+'018::004','황색 체크무늬 표식',None,'trace')
add(P+'018::005','조준 원',None,'trace')
add(P+'018::006','조준 링·별·X',None,'trace')
add(P+'018::007','조준 방향',None,'trace')
add(P+'018::010','조준 상태·X 버튼',None)
add(P+'018::011','작은 조준 링',None,'trace')
add(P+'018::013','상승 표시',None)
add(P+'018::016','상태 사각·원·삼각',[[0,0,128,37]],'trace')
add(P+'019::003','메뉴 별',[[72,0,128,43]],'trace')
add(P+'019::004','메뉴 도구·하향 화살표',[[104,0,128,51]],'trace')
add(F+'000::005','필드 R/L/X 버튼',[[85,0,106,37]])
add(F+'004','필드 작은 별',None,'trace')
add(F+'011','필드 미확인 아이콘',[[0,38,11,50]],'trace')
add(F+'015','필드 미니맵 링',[[0,0,104,104]],'trace')
add(F+'019','필드 별·원',None,'trace')
add(F+'020','필드 분할 링',None,'trace')
add(F+'022','필드 큰 별',None,'trace')
add(B+'003','전투 미확인 표식',[[240,22,256,40]],'trace')
add(B+'004','전투 버튼 표식',[[49,0,64,51]])
add(B+'010','전투 조준 링·방향 표식',[[0,0,82,245],[0,245,40,334]],'trace')
add(B+'011::003','아이템 L 버튼·화살표',[[0,0,25,11],[0,16,9,23]])
add('if::evt::mini_map_stage01.gz::000::006','미니맵 공통 표식·포탈',None,'trace')
add('if::evt::mini_map_stage01.gz::000::004','미니맵 닫기 버튼',[[0,0,9,16]])
add('title.vol::001_if_title.zzz::004','타이틀 선택 표식 5상태',[[140,1,162,21],[163,1,185,21],[186,1,208,21],[163,127,185,147],[140,127,162,147]],'trace')
add(M+'menu_gallery.gz::009','갤러리 그림·음악·영상·화살표',[[0,0,88,30],[100,16,113,35],[0,30,8,48],[72,30,81,47],[72,48,85,58]],'trace')
add(M+'menu_gallery.gz::010','갤러리 액자',[[0,0,35,34]],'trace')
# Flat geometry must not acquire inferred brushwork, beveled digits or new
# texture. Neural processing is reserved for the actual chest/relief medals.
for spec in SPECS:
 if spec['id']!='ICO-005' and not 8<=int(spec['id'][4:])<=27:spec['method']='palette_trace'
