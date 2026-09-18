from pathlib import Path
from pptx import Presentation
from pptx.chart.data import ChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

OUT = Path('Documentation/GBC_MARKET_X_Guia_Filtros_Editable.pptx')
G=RGBColor(0,107,84); DG=RGBColor(24,48,40); M=RGBColor(217,238,232)
LG=RGBColor(239,247,244); R=RGBColor(198,40,40); LR=RGBColor(252,232,232)
A=RGBColor(233,139,22); LA=RGBColor(255,243,220); C=RGBColor(36,41,39)
MG=RGBColor(103,112,108); GR=RGBColor(217,221,219); LGR=RGBColor(243,245,244)
W=RGBColor(255,255,255)

def text(s,t,x,y,w,h,z=18,c=C,b=False,a=PP_ALIGN.LEFT):
    q=s.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h)); f=q.text_frame
    f.clear(); f.margin_left=f.margin_right=Inches(.04); f.margin_top=f.margin_bottom=Inches(.03); f.vertical_anchor=MSO_ANCHOR.MIDDLE
    p=f.paragraphs[0]; p.alignment=a; r=p.add_run(); r.text=t; r.font.name='Aptos'; r.font.size=Pt(z); r.font.bold=b; r.font.color.rgb=c
    return q

def rect(s,x,y,w,h,fill=W,line=GR,round=False,lw=1):
    k=MSO_SHAPE.ROUNDED_RECTANGLE if round else MSO_SHAPE.RECTANGLE
    q=s.shapes.add_shape(k,Inches(x),Inches(y),Inches(w),Inches(h)); q.fill.solid(); q.fill.fore_color.rgb=fill; q.line.color.rgb=line; q.line.width=Pt(lw); return q

def head(s,section='GUIA DE FILTROS'):
    text(s,'GBC',.28,.1,.95,.34,18,G,True); text(s,'MARKET X',1.18,.1,1.5,.34,11,MG)
    text(s,section,9.3,.1,3.7,.34,9,MG,False,PP_ALIGN.RIGHT); rect(s,.28,.51,12.72,.035,G,G)

def foot(s,note,n):
    rect(s,.28,6.87,12.72,.42,LGR,LGR); text(s,'NOTA',.42,6.93,.58,.25,8,G,True)
    text(s,note,1,6.9,11.35,.31,8,MG); text(s,str(n),12.45,6.92,.35,.25,8,MG,False,PP_ALIGN.RIGHT)

def slide(prs,title,sub='',section='GUIA DE FILTROS'):
    s=prs.slides.add_slide(prs.slide_layouts[6]); s.background.fill.solid(); s.background.fill.fore_color.rgb=W; head(s,section)
    text(s,title,.45,.67,12.35,.45,25,DG,True,PP_ALIGN.CENTER)
    if sub:text(s,sub,.6,1.1,12.05,.31,10,MG,False,PP_ALIGN.CENTER)
    return s

def cell(c,t,z=9,col=C,b=False,fill=W):
    c.fill.solid(); c.fill.fore_color.rgb=fill; c.margin_left=c.margin_right=Inches(.04); c.margin_top=c.margin_bottom=Inches(.03)
    f=c.text_frame; f.clear(); f.vertical_anchor=MSO_ANCHOR.MIDDLE; p=f.paragraphs[0]; p.alignment=PP_ALIGN.CENTER
    r=p.add_run(); r.text=str(t); r.font.name='Aptos'; r.font.size=Pt(z); r.font.bold=b; r.font.color.rgb=col

def table(s,headers,rows,x,y,w,h,widths=None,status=None,z=9):
    q=s.shapes.add_table(len(rows)+1,len(headers),Inches(x),Inches(y),Inches(w),Inches(h)); tb=q.table
    if widths:
        for i,v in enumerate(widths):tb.columns[i].width=Inches(v)
    for j,v in enumerate(headers):cell(tb.cell(0,j),v,z,W,True,DG)
    for i,row in enumerate(rows,1):
        for j,v in enumerate(row):
            bg=W if i%2 else LGR; co=C; bo=False
            if status is not None and j==status:
                u=str(v).upper()
                if any(k in u for k in ('INCL','PASA','MANTIENE')):bg,co,bo=M,G,True
                elif 'ANOM' in u:bg,co,bo=LA,A,True
                elif any(k in u for k in ('EXCL','OMITE','REMUEVE')):bg,co,bo=LR,R,True
            cell(tb.cell(i,j),v,z,co,bo,bg)
    return q

def badge(s,t,x,y,w,col=G,pale=M):
    rect(s,x,y,w,.38,pale,col,True); text(s,t,x+.08,y+.03,w-.16,.3,10,col,True,PP_ALIGN.CENTER)

def metric(s,label,value,x,y,w=2.65,bad=False):
    co,bg=(R,LR) if bad else (G,W); rect(s,x,y,w,1.03,bg,co,True,1.2)
    text(s,label,x+.08,y+.1,w-.16,.26,10,MG,False,PP_ALIGN.CENTER); text(s,value,x+.08,y+.4,w-.16,.43,22,co,True,PP_ALIGN.CENTER)

def card(s,name,imps,kpi,kind,kba,x,y,w,ok=True,why=''):
    co,bg=(G,W) if ok else (R,LR); rect(s,x,y,w,3.45,bg,co,True,1.4); rect(s,x,y,w,.48,co,co,True)
    text(s,name,x+.04,y+.05,w-.08,.33,11,W,True,PP_ALIGN.CENTER); yy=y+.62
    for lab,val in [('Impresiones',imps),('KPI',kpi),('Tipo KPI',kind),('Total KBAs',kba)]:
        text(s,lab,x+.08,yy,w-.16,.2,8,MG,False,PP_ALIGN.CENTER); text(s,val,x+.08,yy+.2,w-.16,.34,15,co if lab=='KPI' else C,lab=='KPI',PP_ALIGN.CENTER); yy+=.66
    if not ok:text(s,'EXCLUIDA',x+.1,y+2.98,w-.2,.25,11,R,True,PP_ALIGN.CENTER); text(s,why,x+.1,y+3.2,w-.2,.18,7,R,False,PP_ALIGN.CENTER)

def chart(s,cats,vals,x,y,w,h,title):
    d=ChartData(); d.categories=cats; d.add_series('Valor',vals); f=s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED,Inches(x),Inches(y),Inches(w),Inches(h),d); ch=f.chart
    ch.has_title=True; ch.chart_title.text_frame.text=title; ch.chart_title.text_frame.paragraphs[0].runs[0].font.size=Pt(12); ch.has_legend=False
    ch.value_axis.has_major_gridlines=True; ch.value_axis.tick_labels.number_format='#,##0'; ch.value_axis.tick_labels.font.size=Pt(8); ch.category_axis.tick_labels.font.size=Pt(9)
    ch.series[0].format.fill.solid(); ch.series[0].format.fill.fore_color.rgb=G; ch.series[0].format.line.color.rgb=G

def build():
    prs=Presentation(); prs.slide_width=Inches(13.333); prs.slide_height=Inches(7.5)
    s=prs.slides.add_slide(prs.slide_layouts[6]); s.background.fill.solid(); s.background.fill.fore_color.rgb=LG; rect(s,0,0,4.25,7.5,DG,DG)
    text(s,'GBC',.55,.52,1.5,.55,28,W,True); text(s,'DIGITAL MONTHLY',.55,1.22,3.05,.38,12,M,True)
    text(s,'Guia editable de filtros',4.75,1.58,7.55,.72,32,DG,True); text(s,'MARKET X  |  Junio 2026',4.78,2.38,6.8,.42,18,G,True)
    text(s,'Ejemplo ficticio para reconciliar Executive Summary, tactic slides, historicos y YTD.',4.78,3.02,7.55,.72,16)
    badge(s,'UMBRAL CONFIGURADO: $50.00',4.78,4.15,3.55); badge(s,'$50 PASA  $49.99 NO PASA',8.55,4.15,3.75,A,LA)
    text(s,'Todos los nombres, costos y metricas son ficticios.',4.78,6.45,7.3,.3,9,MG)

    s=slide(prs,'Dataset ficticio y resultado esperado','El costo se agrega por Tactica efectiva + Site agrupado + Audiencia antes de compararse con $50.')
    rows=[['FEP','ALPHA','GEN','$200.00','Si','Incluye','Incluye'],['FEP','BETA','GEN','$25.00','Si','Excluye','Mantiene + anomalia'],['YouTube','ALPHA','GEN','$50.00','Si','Incluye','Incluye'],['InMarket Display','GAMMA','GEN','$49.99','Si','Excluye','Mantiene + anomalia'],['Search','DELTA','GEN','$40.00','No','Excluye','Omite'],['Audio','ALPHA','GEN','$75.00','Si','Incluye','Incluye'],['PreRoll','ALPHA','GEN','$180.00','Si','Incluye','Incluye']]
    table(s,['Tactica','Site','Aud.','Costo agregado','Performance','Summary','Tactic slide'],rows,.45,1.6,12.42,3.85,[2.2,1.4,.75,1.8,1.4,1.7,3.17],5,9)
    rect(s,.6,5.67,12.1,.88,LA,A,True); text(s,'Clave: el Summary excluye toda combinacion bajo $50. La tactic slide conserva una combinacion bajo $50 unicamente cuando existe performance, y la registra como anomalia.',.83,5.82,11.65,.52,12,C,True,PP_ALIGN.CENTER); foot(s,'Summary y tactic slide pueden diferir intencionalmente.',2)

    s=slide(prs,'Junio 2026 | MARKET X | GEN','Executive Summary: solo contribuyen combinaciones con costo agregado >= $50.','EXECUTIVE SUMMARY')
    cards=[('FEP','150,000','97%','VCR','30'),('YouTube','60,000','$0.025','CPCV','8'),('PreRoll','110,000','70%','VCR','12'),('Audio','80,000','93%','ACR','0')]
    for i,v in enumerate(cards):card(s,*v,.48+i*2.48,1.62,2.27,True)
    card(s,'Display','90,000','$0.50','CPA','100',10.4,1.62,2.27,False,'$49.99 < $50')
    rect(s,.62,5.34,12,1.08,LG,G,True); text(s,'Reconciliacion FEP: el card contiene solo ALPHA (150,000 impresiones / 30 KBAs). BETA tiene performance, pero su costo agregado de $25 no contribuye al Summary.',.88,5.54,11.5,.63,13,DG,True,PP_ALIGN.CENTER); foot(s,'Si dos sites FEP superan $50, el card suma ambos y no coincide con una sola tactic slide.',3)
    s=slide(prs,'FEP - ALPHA - GEN','Tactic slide incluida: costo agregado del mes actual = $200.00.','TACTIC SLIDE')
    metric(s,'Impresiones','150,000',.55,1.55); metric(s,'Video Completes','140,000',3.42,1.55); metric(s,'VCR','97%',6.29,1.55); metric(s,'Total KBAs','30',9.16,1.55)
    hr=[['Ene','$40','30,000','Remueve'],['Feb','$50','35,000','Pasa'],['Mar','$80','45,000','Pasa'],['Abr','$0','20,000','Remueve'],['May','$120','90,000','Pasa'],['Jun','$200','150,000','Pasa']]
    table(s,['Mes','Costo','Impresiones','Historico'],hr,.55,2.88,4.5,3.4,[.8,1,1.35,1.35],3,8)
    chart(s,['Feb','Mar','May','Jun'],[33000,42000,86000,140000],5.3,2.9,7.25,3.38,'Video Completes - meses que pasan el filtro historico')
    foot(s,'El historico usa solo costo mensual: Ene ($40) y Abr ($0) se remueven aunque tengan performance; Feb ($50) permanece.',4)

    s=slide(prs,'FEP - BETA - GEN','Caso deliberado de discrepancia: costo agregado $25.00 con performance.','TACTIC SLIDE - ANOMALIA')
    metric(s,'Impresiones','20,000',.75,1.65,2.75); metric(s,'Video Completes','19,000',3.75,1.65,2.75); metric(s,'VCR','95%',6.75,1.65,2.75); metric(s,'Total KBAs','5',9.75,1.65,2.75)
    rect(s,.75,3.1,5.75,2.65,LA,A,True,1.5); text(s,'TACTIC SLIDE',1,3.38,5.25,.35,15,A,True,PP_ALIGN.CENTER); text(s,'Se conserva porque si tiene performance.\nSe registra una anomalia de bajo spend.',1.05,3.92,5.15,1.15,19,C,True,PP_ALIGN.CENTER)
    rect(s,6.82,3.1,5.75,2.65,LR,R,True,1.5); text(s,'EXECUTIVE SUMMARY',7.07,3.38,5.25,.35,15,R,True,PP_ALIGN.CENTER); text(s,'No contribuye al card FEP.\n$25.00 es menor que $50.00.',7.12,3.92,5.15,1.15,19,C,True,PP_ALIGN.CENTER)
    foot(s,'Esta diferencia reproduce la logica historica: bajo spend con performance se ve en detalle, pero no en el Summary.',5)

    s=slide(prs,'YouTube - ALPHA - GEN','Caso de frontera: costo agregado exactamente igual al umbral.','TACTIC SLIDE')
    metric(s,'Costo agregado','$50.00',1.05,1.65,3.15); metric(s,'Impresiones','60,000',5.08,1.65,3.15); metric(s,'CPCV','$0.025',9.1,1.65,3.15)
    rect(s,1.05,3.28,11.2,1.55,M,G,True,1.5); text(s,'$50.00 >= $50.00  ->  INCLUIR',1.35,3.57,10.6,.5,25,G,True,PP_ALIGN.CENTER); text(s,'La condicion es costo < umbral. El valor exacto del umbral si pasa.',1.35,4.18,10.6,.35,13,DG,False,PP_ALIGN.CENTER)
    badge(s,'Summary: incluye',3.05,5.35,3.1); badge(s,'Tactic slide: incluye',7.1,5.35,3.2); foot(s,'Ejemplo de frontera: la regla es menor que $50, no menor o igual.',6)

    s=slide(prs,'Search - DELTA - GEN','Representacion educativa de una slide que no se generaria.','TACTIC SLIDE - OMITIDA')
    metric(s,'Costo agregado','$40.00',1.15,1.7,3.1,True); metric(s,'Impresiones','0',5.1,1.7,3.1,True); metric(s,'Clicks','0',9.05,1.7,3.1,True)
    rect(s,1.15,3.45,11,2.08,LR,R,True,2); text(s,'NO SE GENERA EN EL DECK REAL',1.45,3.8,10.4,.55,25,R,True,PP_ALIGN.CENTER); text(s,'$40 < $50 y no existe performance. Tambien queda fuera del Executive Summary.',1.65,4.5,10,.48,15,C,True,PP_ALIGN.CENTER)
    foot(s,'Esta pagina existe solo en la guia para documentar por que faltaria una tactic slide.',7)

    s=slide(prs,'Display: normalizacion y agregacion antes del umbral','Las filas se consolidan primero; el filtro no se aplica fila por fila.','REGLA DE COMBINACION')
    raw=[['Display','InMarket','GAMMA','GEN','$30.00','40,000'],['Display','BT','GAMMA','GEN','$19.99','50,000']]
    table(s,['Raw tactic','Strategy','Site','Aud.','Costo','Impresiones'],raw,.6,1.62,6.15,1.62,[1.15,1.15,.9,.65,1,1.3],None,9)
    text(s,'+',6.88,1.98,.45,.55,28,G,True,PP_ALIGN.CENTER); rect(s,7.45,1.62,5.2,1.62,LG,G,True); text(s,'InMarket Display + GAMMA + GEN',7.7,1.83,4.7,.3,13,DG,True,PP_ALIGN.CENTER); text(s,'$49.99  |  90,000 impresiones',7.7,2.3,4.7,.4,19,C,True,PP_ALIGN.CENTER)
    text(s,'AGREGAR PRIMERO',1,3.75,3.25,.38,15,G,True,PP_ALIGN.CENTER); text(s,'->',4.45,3.69,.7,.5,28,MG,True,PP_ALIGN.CENTER); text(s,'COMPARAR CON $50',5.25,3.75,3.25,.38,15,A,True,PP_ALIGN.CENTER); text(s,'->',8.7,3.69,.7,.5,28,MG,True,PP_ALIGN.CENTER); text(s,'APLICAR REGLA',9.5,3.75,2.8,.38,15,R,True,PP_ALIGN.CENTER)
    rect(s,1,4.55,11.3,1.35,LA,A,True); text(s,'Resultado: $49.99 < $50. El Summary excluye la combinacion. La tactic slide se conserva porque tiene 90,000 impresiones y registra anomalia.',1.3,4.84,10.7,.72,15,C,True,PP_ALIGN.CENTER)
    foot(s,'Las reglas de normalizacion de tactica, site y audiencia permanecen sin cambios.',8)
    s=slide(prs,'YTD KBA Breakdown','El filtro YTD usa resultados, no Total Cost. Minimo ficticio: 100 outcomes por mes.','YTD')
    yr=[['Ene','80','Remueve'],['Feb','100','Pasa'],['Mar','130','Pasa'],['Abr','0','Remueve'],['May','140','Pasa'],['Jun','150','Pasa']]
    table(s,['Mes','Total outcomes','Resultado'],yr,.65,1.62,4.1,3.65,[1.05,1.55,1.5],2,9); chart(s,['Feb','Mar','May','Jun'],[100,130,140,150],5.05,1.62,7.45,3.65,'Meses incluidos - YTD Outcomes')
    rect(s,.8,5.55,11.7,.75,LG,G,True); text(s,'El spend de las tacticas no decide este grafico. Febrero pasa exactamente en 100.',1.05,5.73,11.2,.34,13,DG,True,PP_ALIGN.CENTER); foot(s,'El bloque YTD tiene configuracion visual independiente en la UI.',9)

    s=slide(prs,'YTD Impressions by Vehicle','El filtro YTD usa impresiones. Minimo ficticio: 1,000 impresiones por mes.','YTD')
    ir=[['Ene','900','Remueve'],['Feb','1,000','Pasa'],['Mar','1,250','Pasa'],['Abr','800','Remueve'],['May','1,400','Pasa'],['Jun','1,600','Pasa']]
    table(s,['Mes','Impresiones','Resultado'],ir,.65,1.62,4.1,3.65,[1.05,1.55,1.5],2,9); chart(s,['Feb','Mar','May','Jun'],[1000,1250,1400,1600],5.05,1.62,7.45,3.65,'Meses incluidos - YTD Impressions')
    rect(s,.8,5.55,11.7,.75,LG,G,True); text(s,'El minimo de impresiones es independiente del minimo de outcomes y del spend de $50.',1.05,5.73,11.2,.34,13,DG,True,PP_ALIGN.CENTER); foot(s,'No se agrego un maximo YTD porque las reglas vigentes definen unicamente minimos.',10)

    s=slide(prs,'Data Anomalies & Validation Errors','Las combinaciones bajo el umbral con performance permanecen visibles como anomalias.','ERROR SUMMARY')
    er=[['FEP','BETA','$25.00','20,000 imps / 19,000 completes','Bajo spend con performance'],['InMarket Display','GAMMA','$49.99','90,000 imps / 100 KBAs','Bajo spend con performance']]
    table(s,['Tactica','Site','Spend','Performance','Anomalia'],er,.55,1.65,12.25,2.15,[2.05,1.25,1.2,3.25,4.5],4,9)
    rect(s,.8,4.3,5.72,1.62,LA,A,True); text(s,'Por que aparecen?',1.05,4.52,5.2,.35,15,A,True,PP_ALIGN.CENTER); text(s,'La tactic slide se conserva para no ocultar performance sin spend suficiente.',1.1,4.98,5.1,.58,13,C,True,PP_ALIGN.CENTER)
    rect(s,6.82,4.3,5.72,1.62,LR,R,True); text(s,'Por que no estan en Summary?',7.07,4.52,5.2,.35,15,R,True,PP_ALIGN.CENTER); text(s,'El Summary excluye toda combinacion cuyo spend agregado sea menor a $50.',7.12,4.98,5.1,.58,13,C,True,PP_ALIGN.CENTER)
    foot(s,'El Error Summary explica discrepancias intencionales entre las vistas agregada y detallada.',11)

    s=slide(prs,'Mapa de reconciliacion del deck','Use este flujo para explicar cualquier diferencia entre slides.','GLOSARIO Y CONTROL')
    steps=[('1','Normalizar','Tactica, Strategy, Site y Audience'),('2','Agregar','Costo y metricas por combinacion'),('3','Comparar','Costo agregado contra $50'),('4','Aplicar vista','Summary, tactic, historico o YTD')]
    for i,(n,ti,de) in enumerate(steps):
        x=.58+i*3.15; rect(s,x,1.55,2.72,1.35,LG,G,True); text(s,n,x+.12,1.8,.48,.52,24,G,True,PP_ALIGN.CENTER); text(s,ti,x+.62,1.68,1.9,.32,14,DG,True); text(s,de,x+.62,2.04,1.9,.55,10,C)
    fr=[['Executive Summary','Costo agregado >= $50','Bajo $50: excluye siempre'],['Tactic slide actual','Costo + performance','Bajo $50 con performance: mantiene + anomalia'],['Historico tactic','Costo mensual >= $50','Bajo $50: remueve mes si opcion activa'],['YTD Outcomes','Total mensual >= minimo YTD','No usa spend'],['YTD Impressions','Impresiones mensuales >= minimo YTD','No usa spend']]
    table(s,['Vista','Regla de inclusion','Fuente de discrepancia'],fr,.72,3.3,11.9,2.78,[2.5,3.75,5.65],None,9)
    foot(s,'Regla maestra: se conserva la logica anterior y se sustituye el punto de corte de $0 por un umbral UI de $50.',12)

    s=slide(prs,'Resumen de filtros y condiciones generales','Lectura rapida de las reglas aplicadas en todo el deck.','RESUMEN FINAL')
    bullets=[
        'Filtros base: Brand, Market, Month, Zone/LMA y Client Code se aplican antes de construir las slides.',
        'Normalizacion: tactic, strategy, site y audience se resuelven antes de agregar las metricas.',
        'Spend: se suma por Tactica efectiva + Site agrupado + Audience; menor a $50 es low spend y $50 pasa.',
        'Executive Summary: toda combinacion low spend se excluye, aunque tenga performance.',
        'Tactic slide actual: low spend con performance se mantiene y genera anomalia; sin performance se omite.',
        'Ventana historica: muestra el numero configurado de meses terminando en el mes del reporte.',
        'Historico de tactica: si la opcion esta activa, meses con costo agregado menor a $50 se remueven.',
        'Video LMA: FEP y YouTube con cero completions se excluyen del Summary; la regla individual revisa actividad.',
        'YTD Outcomes e Impressions: usan sus propios minimos mensuales y no dependen del spend.',
        'Error Summary: documenta low spend con performance y otras anomalias para explicar discrepancias.'
    ]
    for i,item in enumerate(bullets):
        col=0 if i<5 else 1; row=i if i<5 else i-5; x=.65+col*6.15; y=1.55+row*1.0
        rect(s,x,y,5.75,.82,LG if col==0 else LGR,G if col==0 else MG,True)
        text(s,'- '+item,x+.18,y+.08,5.4,.64,10,C,False)
    rect(s,1.2,6.15,10.93,.48,M,G,True)
    text(s,'Regla maestra: conservar las condiciones existentes y reemplazar el punto de corte de $0 por el umbral configurable de $50.',1.45,6.22,10.45,.3,11,DG,True,PP_ALIGN.CENTER)
    foot(s,'Todos los ejemplos son ficticios y estan disenados para mostrar diferencias intencionales entre vistas.',13)

    OUT.parent.mkdir(parents=True,exist_ok=True); prs.save(OUT); return OUT

if __name__=='__main__':
    print(build().resolve())