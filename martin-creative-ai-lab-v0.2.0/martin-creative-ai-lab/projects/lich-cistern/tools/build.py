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
TITLE = 'A água sob Darsen'
AUTHOR = 'Codex, sob direção de Martin Melcop Neto'


def chapters():
    sections = []
    for block in (ROOT/'story.md').read_text().strip().split('\n\n'):
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


def pdf(path):
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
    doc=Edition(str(path),pagesize=A5,title=TITLE,author=AUTHOR,
                subject='P04 — Independent Portuguese seed adaptation',
                leftMargin=18*mm,rightMargin=18*mm,topMargin=21*mm,bottomMargin=19*mm)

    def running(canvas, document):
        if document.page>1:
            canvas.saveState()
            canvas.setFont('DejaVuSerif',8)
            canvas.setFillColor(colors.HexColor('#4e5963'))
            canvas.drawString(18*mm,height-13*mm,TITLE)
            canvas.drawRightString(width-18*mm,11*mm,str(document.page))
            canvas.restoreState()
    doc.addPageTemplates(PageTemplate(id='Reading',
        frames=Frame(doc.leftMargin,doc.bottomMargin,doc.width,doc.height,id='Body',
                     leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0),
        onPage=running))
    flow=[Spacer(1,34*mm),Paragraph(TITLE,title),
          Paragraph('Uma narrativa de<br/>O Lich mais velho da tumba mais antiga',center),
          Spacer(1,25*mm),Paragraph(AUTHOR,center),
          Paragraph('Martin Creative AI Lab · 2026',center),PageBreak(),
          Paragraph('Sobre esta edição',front),
          Paragraph('Narrativa independente, desenvolvida a partir da seed P04 do laboratório. '
                    'Não incorpora nem substitui os manuscritos históricos do romance. '
                    'Baldino, Aevren e Darsen vêm dessa seed; os acontecimentos, os demais '
                    'personagens e as regras locais desta história são uma nova adaptação.',small),
          Paragraph('Texto e revisão por Codex, sob direção de Martin Melcop Neto. '
                    'Edição 0.1.0 · Português brasileiro · 12 de outubro de 2026.',small),
          Spacer(1,8*mm),Paragraph('Sumário',front)]
    toc=TableOfContents()
    toc.levelStyles=[ParagraphStyle('Contents',fontName='DejaVuSerif',fontSize=10.5,
                                     leading=17,spaceBefore=8,leftIndent=0)]
    flow.append(toc)
    sections=chapters()
    for index,(name,paras) in enumerate(sections):
        flow.extend([PageBreak(),Paragraph(escape(name),heading)])
        if index==len(sections)-1:
            flow.extend(Paragraph(escape(text),body) for text in paras[:-3])
            flow.append(KeepTogether([Paragraph(escape(text),body) for text in paras[-3:]]))
        else: flow.extend(Paragraph(escape(text),body) for text in paras)
    flow.extend([PageBreak(),Paragraph('Fontes tipográficas',front),
                 Paragraph('DejaVu Serif. As fontes incorporadas abaixo preservam '
                           'o texto e os caracteres portugueses entre leitores de PDF. '
                           'Os arquivos originais não foram alterados. Avisos e licença:',small)])
    license_style=ParagraphStyle('License',parent=small,fontSize=7.5,leading=10)
    for part in (ROOT/'fonts/LICENSE.txt').read_text().strip().split('\n\n'):
        flow.append(Paragraph(escape(part).replace('\n','<br/>'),license_style))
    doc.multiBuild(flow)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=ROOT/'dist')
    args=parser.parse_args()
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
    name='a-agua-sob-darsen-0.1.0'
    subprocess.run(['pandoc',str(ROOT/'story.md'),'--from=markdown','--to=epub3',
                    '--metadata-file',str(ROOT/'metadata.yaml'),'--css',str(ROOT/'book.css'),
                    '--toc','--toc-depth=1','--split-level=1',
                    '--output',str(out/(name+'.epub'))],check=True)
    pdf(out/(name+'.pdf'))
    words=len(re.findall(r"\b[\w]+(?:[-’'][\w]+)*\b",(ROOT/'story.md').read_text()))
    print(json.dumps({'epub':str(out/(name+'.epub')),'pdf':str(out/(name+'.pdf')),
                      'chapters':len(chapters()),'words':words}))


if __name__=='__main__':main()
