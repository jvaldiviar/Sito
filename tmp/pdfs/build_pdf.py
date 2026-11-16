from pathlib import Path
from bs4 import BeautifulSoup
from html import escape
import json,re
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,PageBreak,KeepTogether
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image as PILImage
import pymupdf

pdfmetrics.registerFont(TTFont('Arial','/System/Library/Fonts/Supplemental/Arial.ttf'))
pdfmetrics.registerFont(TTFont('Arial-Bold','/System/Library/Fonts/Supplemental/Arial Bold.ttf'))
pdfmetrics.registerFontFamily('Arial',normal='Arial',bold='Arial-Bold',italic='Arial',boldItalic='Arial-Bold')
blue=colors.HexColor('#27699C'); dark=colors.HexColor('#344451')
styles=getSampleStyleSheet()
for name in ['Normal','Title','Heading1','Heading2','Heading3']:
    styles[name].fontName='Arial'
    styles[name].textColor=dark
styles['Normal'].fontSize=10;styles['Normal'].leading=15;styles['Normal'].spaceAfter=9
styles['Title'].fontSize=28;styles['Title'].leading=34;styles['Title'].alignment=0;styles['Title'].spaceAfter=16
for n,size in [('Heading1',21),('Heading2',14),('Heading3',11)]:
    styles[n].fontName='Arial-Bold';styles[n].fontSize=size;styles[n].leading=size+5;styles[n].textColor=blue;styles[n].spaceBefore=10;styles[n].spaceAfter=10
styles.add(ParagraphStyle('Cell',parent=styles['Normal'],fontSize=9,leading=12,spaceAfter=0))
styles.add(ParagraphStyle('Caption',parent=styles['Normal'],fontSize=8,leading=11,textColor=colors.HexColor('#687D8C')))
def clean(t):return re.sub(r'\s+',' ',t).strip().replace('−','-').replace('–','-').replace('—','-').replace('₄','4')
def txt(el):return clean(el.get_text(' ',strip=True))
def p(t,style='Normal'):return Paragraph(escape(clean(t)),styles[style])
def soup(f):return BeautifulSoup(Path(f).read_text(),'html.parser')
a=soup('Flashbattery4.html');b=soup('Flashbattery5.html')
assets=json.loads(Path('tmp/pdfs/images.json').read_text())
def img(el,w,h):
    original=Path(assets[el['src']]);path=original.with_suffix('.jpg')
    if not path.exists():
        source=PILImage.open(original).convert('RGB');source.thumbnail((1600,1600));source.save(path,quality=90)
    iw,ih=PILImage.open(path).size
    scale=min(w/iw,h/ih)
    return Image(path,iw*scale,ih*scale,hAlign='CENTER')
story=[]
story+=[p('MARSTEK VENUS-E','Title'),p('Batteria AC da 5,12 kWh','Heading2'),p(txt(a.select_one('.sic-venus-sheet__intro')))]
story+=[img(a.select_one('img'),280,260),Spacer(1,12),p('Dettagli prodotto','Heading2')]
for li in a.select('.sic-venus-sheet__spec-list > li'):story.append(p('• '+txt(li)))
story.append(p(txt(a.select_one('.sic-venus-sheet__brand')),'Caption'))
story.append(p('Contenuti: scheda prodotto, specifiche complete, informazioni IVA, funzionalità e galleria immagini.','Caption'))
story.append(PageBreak())
groups=a.select('.sic-venus-sheet__technical-group')
for i,g in enumerate(groups):
    if i in [0,2,5]:story.append(p('Specifiche tecniche'+(' - continua' if i else ''),'Heading1'))
    rows=[]
    for tr in g.select('tr'):
        rows.append([p(txt(c),'Cell') for c in tr.find_all(['th','td'])])
    table=Table(rows,colWidths=[172,335],hAlign='LEFT')
    table.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(0,-1),colors.HexColor('#EDF4F9')),('LINEBELOW',(0,0),(-1,-1),.4,colors.HexColor('#DBE6EE')),('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),9),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
    story.append(KeepTogether([p(txt(g.select_one('h4')),'Heading2'),table]))
    if i in [1,4]:story.append(PageBreak())
story.append(PageBreak())
story.append(p('Informazioni IVA','Heading1'))
tax=a.select_one('.sic-venus-sheet__tax-heading').parent
for el in tax.find_all(['h4','p','li']):
    story.append(p(('• ' if el.name=='li' else '')+txt(el),'Heading2' if el.name=='h4' else 'Normal'))
story.append(p('Riferimento citato nel testo originale: sezione “Domande frequenti e documenti” della pagina web. Il modulo di autocertificazione non è incluso nei due file forniti.','Caption'))
for panel in b.select('.sic-venus-gallery__panel'):
    story.append(PageBreak());story.append(p(txt(panel.select_one('h3')),'Heading1'))
    for card in panel.select('article'):
        # Each feature preserves its complete description and source illustration.
        image=img(card.select_one('img'),165,133)
        text=[p(txt(card.select_one('h4')),'Heading2'),p(txt(card.select_one('.sic-venus-gallery__card-text')))]
        block=Table([[image,text]],colWidths=[180,327])
        block.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),20)]))
        story.append(KeepTogether(block))
gallery=a.select('.sic-venus-sheet__slide img')
for start in [0,4]:
    story.append(PageBreak());story.append(p('Galleria prodotto'+(' - continua' if start else ''),'Heading1'))
    cells=[]
    for el in gallery[start:start+4]:cells.append([img(el,235,250),p(el.get('alt',''),'Caption')])
    while len(cells)%2:cells.append('')
    t=Table([cells[i:i+2] for i in range(0,len(cells),2)],colWidths=[253.5,253.5])
    t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),20)]));story.append(t)
def footer(c,d):
    c.setStrokeColor(colors.HexColor('#D4E2ED'));c.line(44,43,551,43)
    c.setFont('Arial',8);c.setFillColor(colors.HexColor('#687D8C'))
    c.drawString(44,29,'MARSTEK VENUS-E | Flashbattery4 + Flashbattery5')
    c.drawRightString(551,29,str(d.page))
out=Path('output/pdf/Marstek_Venus_E_Informazioni_Complete.pdf');out.parent.mkdir(parents=True,exist_ok=True)
SimpleDocTemplate(str(out),pagesize=A4,rightMargin=44,leftMargin=44,topMargin=38,bottomMargin=57,title='MARSTEK VENUS-E - Informazioni complete',author='').build(story,onFirstPage=footer,onLaterPages=footer)
doc=pymupdf.open(out)
print('Pages:',len(doc))
for i,page in enumerate(doc):
    page.get_pixmap(matrix=pymupdf.Matrix(1,1)).save(f'tmp/pdfs/page-{i+1:02}.png')
    print(i+1,len(page.get_text()),page.get_text()[:70].replace('\n',' '))
# Check every original informational paragraph, list item and table cell is present.
alltext=clean(' '.join(page.get_text() for page in doc))
missing=[]
for el in a.select('.sic-venus-sheet__intro,.sic-venus-sheet__spec-list li,.sic-venus-sheet__technical-table th,.sic-venus-sheet__technical-table td,.sic-venus-sheet__tax-text,.sic-venus-sheet__tax-note p,.sic-venus-sheet__tax-bullet li')+b.select('.sic-venus-gallery__card-text'):
    if txt(el) not in alltext:missing.append(txt(el))
print('Missing content:',missing)
from PIL import ImageOps,ImageDraw
thumbs=[]
for i in range(len(doc)):
    im=PILImage.open(f'tmp/pdfs/page-{i+1:02}.png').convert('RGB');im.thumbnail((300,425));thumbs.append(im)
sheet=PILImage.new('RGB',(300*3,450*((len(thumbs)+2)//3)),'#ccd3d9')
for i,im in enumerate(thumbs):sheet.paste(im,((i%3)*300,(i//3)*450))
sheet.save('tmp/pdfs/contact-sheet.png')
