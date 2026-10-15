#!/usr/bin/env python3
"""Build this story's EPUB with Pandoc and A5 PDF with ReportLab."""
import argparse
import json
import re
import subprocess
from html import escape
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A5
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, PageBreak, PageTemplate,
                                Paragraph, Spacer, KeepTogether)
from reportlab.platypus.tableofcontents import TableOfContents

ROOT = Path(__file__).resolve().parents[1]
EDITIONS = json.loads((ROOT/'editions.json').read_text())


def chapters(edition='pt'):
    sections = []
    for block in (ROOT/EDITIONS[edition]['source']).read_text().strip().split('\n\n'):
        if block.startswith('# '):
            sections.append((block[2:], []))
        else:
            if not sections: raise ValueError('Narrative must start with a chapter title.')
            sections[-1][1].append(block)
    return sections


class Edition(BaseDocTemplate):
    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name=='Chapter':
            title = flowable.getPlainText()
            key = 'chapter-'+title.split('.',1)[0]
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(title, key, 0, False)
            self.notify('TOCEntry',(0,title,self.page,key))


def pdf(path, edition='pt'):
    spec=EDITIONS[edition]
    title_text,author=spec['title'],spec['author']
    for name,file in [('DejaVuSerif','DejaVuSerif.ttf'),('DejaVuSerif-Bold','DejaVuSerif-Bold.ttf')]:
        pdfmetrics.registerFont(TTFont(name,str(ROOT/'fonts'/file)))
    ink=colors.HexColor('#17283a')
    body=ParagraphStyle('Body',fontName='DejaVuSerif',fontSize=10.8,leading=15,
                        spaceAfter=6,allowWidows=0,allowOrphans=0)
    heading=ParagraphStyle('Chapter',fontName='DejaVuSerif-Bold',fontSize=19,leading=25,
                           textColor=ink,spaceAfter=22,keepWithNext=True)
    front=ParagraphStyle('Front',parent=heading)
    title=ParagraphStyle('Title',fontName='DejaVuSerif-Bold',fontSize=28,leading=36,
                         alignment=TA_CENTER,textColor=ink,spaceAfter=25)
    center=ParagraphStyle('Center',fontName='DejaVuSerif',fontSize=11,leading=18,
                          alignment=TA_CENTER,spaceAfter=14)
    small=ParagraphStyle('Small',fontName='DejaVuSerif',fontSize=9,leading=13,
                         spaceAfter=12)
    width,height=A5
    doc=Edition(str(path),pagesize=A5,title=title_text,author=author,
                subject=spec['pdf_subject'],
                leftMargin=18*mm,rightMargin=18*mm,topMargin=21*mm,bottomMargin=19*mm)

    def running(canvas, document):
        if edition=='en':
            from reportlab.pdfbase.pdfdoc import PDFString
            canvas._doc.Catalog.Lang=PDFString(spec['language'])
        if document.page>1:
            canvas.saveState()
            canvas.setFont('DejaVuSerif',8)
            canvas.setFillColor(colors.HexColor('#4e5963'))
            canvas.drawString(18*mm,height-13*mm,title_text)
            canvas.drawRightString(width-18*mm,11*mm,str(document.page))
            canvas.restoreState()
    doc.addPageTemplates(PageTemplate(id='Reading',
        frames=Frame(doc.leftMargin,doc.bottomMargin,doc.width,doc.height,id='Body',
                     leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0),
        onPage=running))
    flow=[Spacer(1,34*mm),Paragraph(escape(title_text),title),
          Paragraph(spec['subtitle'],center),
          Spacer(1,25*mm),Paragraph(escape(author),center),
          Paragraph('Martin Creative AI Lab · 2026',center),PageBreak(),
          Paragraph(spec['about_heading'],front),
          *[Paragraph(escape(part),small) for part in spec['about']],
          Spacer(1,8*mm),Paragraph(spec['contents_heading'],front)]
    toc=TableOfContents()
    toc.levelStyles=[ParagraphStyle('Contents',fontName='DejaVuSerif',fontSize=10.5,
                                     leading=17,spaceBefore=8,leftIndent=0)]
    flow.append(toc)
    sections=chapters(edition)
    for name,paras in sections:
        flow.extend([PageBreak(),Paragraph(escape(name),heading)])
        # Keep each scene's closing exchange together across a page boundary.
        flow.extend(Paragraph(escape(text),body) for text in paras[:-3])
        flow.append(KeepTogether([Paragraph(escape(text),body) for text in paras[-3:]]))
    flow.extend([PageBreak(),Paragraph(spec['font_heading'],front),
                 Paragraph(escape(spec['font_note']),small)])
    license_style=ParagraphStyle('License',parent=small,fontSize=7.5,leading=10)
    for part in (ROOT/'fonts/LICENSE.txt').read_text().strip().split('\n\n'):
        flow.append(Paragraph(escape(part).replace('\n','<br/>'),license_style))
    doc.multiBuild(flow)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=ROOT/'dist')
    parser.add_argument('--edition',choices=['pt','en','all'],default='pt')
    args=parser.parse_args()
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
    for edition in EDITIONS if args.edition=='all' else [args.edition]:
        spec=EDITIONS[edition];name=spec['name']
        subprocess.run(['pandoc',str(ROOT/spec['source']),'--from=markdown','--to=epub3',
                        '--metadata-file',str(ROOT/spec['metadata']),'--css',str(ROOT/'book.css'),
                        '--toc','--toc-depth=1','--split-level=1',
                        '--output',str(out/(name+'.epub'))],check=True)
        pdf(out/(name+'.pdf'),edition)
        words=len(re.findall(r"\b[\w]+(?:[-’'][\w]+)*\b",(ROOT/spec['source']).read_text()))
        print(json.dumps({'edition':edition,'epub':str(out/(name+'.epub')),'pdf':str(out/(name+'.pdf')),
                          'chapters':len(chapters(edition)),'words':words}))


if __name__=='__main__':main()
