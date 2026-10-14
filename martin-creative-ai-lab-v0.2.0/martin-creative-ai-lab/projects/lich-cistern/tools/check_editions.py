#!/usr/bin/env python3
"""Verify that shipped reading editions contain the current complete manuscript."""
import argparse
import json
import posixpath
import re
import subprocess
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NS={'opf':'http://www.idpf.org/2007/opf','dc':'http://purl.org/dc/elements/1.1/',
    'x':'http://www.w3.org/1999/xhtml','epub':'http://www.idpf.org/2007/ops'}
EDITIONS=json.loads((ROOT/'editions.json').read_text())


def normalize(text):
    return re.sub(r'\s+',' ',text).strip()


def text(node):
    return normalize(''.join(node.itertext()))


def verify(directory,edition='pt'):
    spec=EDITIONS[edition];stem=spec['name']
    source=(ROOT/spec['source']).read_text().strip().split('\n\n')
    expected=[]
    for paragraph in source:
        if paragraph.startswith('# '): expected.append(('h1',normalize(paragraph[2:])))
        else: expected.append(('p',normalize(paragraph)))
    with zipfile.ZipFile(directory/(stem+'.epub')) as z:
        assert z.namelist()[0]=='mimetype' and z.getinfo('mimetype').compress_type==0
        assert z.read('mimetype')==b'application/epub+zip'
        container=ET.fromstring(z.read('META-INF/container.xml'))
        package=next(node.attrib['full-path'] for node in container.iter()
                     if node.tag.endswith('rootfile'))
        opf=ET.fromstring(z.read(package));base=posixpath.dirname(package)
        assert opf.attrib['version']=='3.0'
        assert opf.find('opf:metadata/dc:title',NS).text==spec['title']
        assert opf.find('opf:metadata/dc:language',NS).text==spec['language']
        assert 'Codex' in opf.find('opf:metadata/dc:creator',NS).text
        manifest={node.attrib['id']:node.attrib for node in opf.findall('opf:manifest/opf:item',NS)}
        found=[];chapter_paths=[]
        for item in opf.findall('opf:spine/opf:itemref',NS):
            asset=manifest[item.attrib['idref']]
            name=posixpath.normpath(posixpath.join(base,asset['href']))
            dom=ET.fromstring(z.read(name))
            assert dom.attrib.get('lang')==spec['language']
            assert dom.attrib.get('{http://www.w3.org/XML/1998/namespace}lang')==spec['language']
            # Narrative chapters are identified by their numbered source headings,
            # not package filename assumptions or title-page/TOC positions.
            heading=dom.find('.//x:h1',NS)
            if heading is None or not re.match(r'^\d+\. ',text(heading)):continue
            chapter_paths.append(name)
            found.append(('h1',text(heading)))
            found.extend(('p',text(node)) for node in dom.findall('.//x:body//x:p',NS))
        assert found==expected,'EPUB text/order differs from the current manuscript'
        nav_item=next(x for x in manifest.values() if 'nav' in x.get('properties','').split())
        nav_path=posixpath.join(base,nav_item['href'])
        nav=ET.fromstring(z.read(nav_path))
        links=nav.findall('.//x:nav/x:ol/x:li/x:a',NS)
        targets={posixpath.normpath(posixpath.join(posixpath.dirname(nav_path),a.attrib['href'].split('#')[0])) for a in links}
        assert set(chapter_paths)<=targets,'Navigation omits a narrative chapter'
    pdf=directory/(stem+'.pdf')
    extracted=subprocess.check_output(['pdftotext','-enc','UTF-8',str(pdf),'-'],text=True)
    narrative=extracted.split(spec['font_heading'],1)[0]
    pages=narrative.split('\f')
    reading=[]
    for page in pages[2:]:
        lines=[line for line in page.splitlines() if line.strip()!=spec['title']
               and not re.fullmatch(r'\d+',line.strip())]
        reading.append(normalize('\n'.join(lines)))
    assert normalize(' '.join(reading))==normalize(' '.join(x[1] for x in expected)),\
        'PDF text/order differs from the current manuscript'
    license_text=extracted.split(spec['font_heading'],1)[1]
    license_lines=[line for line in license_text.splitlines() if line.strip()!=spec['title']
                   and not re.fullmatch(r'\d+',line.strip())]
    assert normalize((ROOT/'fonts/LICENSE.txt').read_text()) in normalize('\n'.join(license_lines)),\
        'PDF must include the complete retained font notices'
    info=subprocess.check_output(['pdfinfo',str(pdf)],text=True)
    assert re.search(r'^Title:\s+'+re.escape(spec['title'])+r'\s*$',info,re.M)
    assert re.search(r'JavaScript:\s+no',info) and re.search(r'Encrypted:\s+no',info)
    page_count=int(re.search(r'Pages:\s+(\d+)',info).group(1))
    fonts=subprocess.check_output(['pdffonts',str(pdf)],text=True)
    serif=[line for line in fonts.splitlines() if 'DejaVuSerif' in line]
    assert len(serif)==2 and all('yes yes yes' in normalize(line) for line in serif),\
        'PDF must embed both serif faces with Unicode mapping'
    if edition=='en':
        assert b'/Lang (en-US)' in pdf.read_bytes(),'English PDF catalog must identify its language'
    return {'edition':edition,'chapters':len(chapter_paths),'paragraphs':sum(k=='p' for k,v in expected),
            'pdf_pages':page_count,'verified':'EPUB3 metadata/navigation and exact source/EPUB/PDF narrative sequence'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dist',type=Path,default=ROOT/'dist')
    parser.add_argument('--edition',choices=['pt','en','all'],default='pt')
    args=parser.parse_args()
    for edition in EDITIONS if args.edition=='all' else [args.edition]:
        print(json.dumps(verify(args.dist.resolve(),edition)))


if __name__=='__main__':main()
