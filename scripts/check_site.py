#!/usr/bin/env python3
"""Offline document, navigation, metadata and content-preservation checks.
No browser layout or Core Web Vitals claims are made by this script.
"""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit, unquote
from urllib.robotparser import RobotFileParser
import json, re, subprocess
import xml.etree.ElementTree as ET
ROOT = Path(__file__).resolve().parents[1]
ORIGIN = 'https://www.institutodesaudedonortedopara.com'
BASELINE = 'e25d4f90ed704017e9a7ad603b032a8efbbff453'
VOID = set('area base br col embed hr img input link meta param source track wbr'.split())
errors = []
checks = 0

def check(condition, message):
    global checks
    checks += 1
    if not condition: errors.append(message)

class Element:
    def __init__(self, tag='', attrs=(), parent=None):
        self.tag, self.attrs, self.parent = tag, dict(attrs), parent
        self.children = []
    def text(self):
        return ' '.join(x.text() if isinstance(x, Element) else x for x in self.children)
    def all(self, tag=None):
        for child in self.children:
            if isinstance(child, Element):
                if tag is None or child.tag == tag:
                    yield child
                yield from child.all(tag)
    def get(self, key, default=''):
        return self.attrs.get(key, default)

class Document(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.root = Element()
        self.stack = [self.root]
        self.structure_errors = []
        self.feed(source)
        self.close()
        if len(self.stack) != 1:
            self.structure_errors.append('Unclosed: ' + ','.join(x.tag for x in self.stack[1:]))
    def handle_starttag(self, tag, attrs):
        node = Element(tag, attrs, self.stack[-1])
        self.stack[-1].children.append(node)
        if tag not in VOID:
            self.stack.append(node)
    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)
    def handle_endtag(self, tag):
        if self.stack[-1].tag == tag:
            self.stack.pop()
        else:
            self.structure_errors.append(f'Unexpected </{tag}> within <{self.stack[-1].tag}>')
    def handle_data(self, data):
        self.stack[-1].children.append(data)
    def all(self, tag=None):
        return list(self.root.all(tag))
    def meta(self, key):
        return [x.get('content') for x in self.all('meta') if x.get('name') == key or x.get('property') == key]

files = [ROOT/'index.html', *sorted((ROOT/'noticias').glob('*.html'))]
pages = {('/' if f.name == 'index.html' else '/' + f.relative_to(ROOT).as_posix()): Document(f.read_text()) for f in files}
robots = RobotFileParser()
robots.parse((ROOT/'robots.txt').read_text().splitlines())
locations = [x.text for x in ET.parse(ROOT/'sitemap.xml').findall('.//{*}loc')]
check(len(pages) == 5, 'Expected home and all four published articles')
check(len(locations) == len(set(locations)) and set(locations) == {ORIGIN+p for p in pages}, 'Sitemap URLs')
check('Sitemap: '+ORIGIN+'/sitemap.xml' in (ROOT/'robots.txt').read_text(), 'Robots sitemap')
check((ROOT/'CNAME').read_text().strip() == urlsplit(ORIGIN).netloc, 'Preserve official domain')
check((ROOT/'.nojekyll').exists(), 'Static hosting marker')

names, descriptions, initial_bytes = [], [], []
for pathname, doc in pages.items():
    label = pathname + ': '
    check(not doc.structure_errors, label+str(doc.structure_errors))
    check(len(doc.all('h1')) == 1 and len(doc.all('main')) == 1, label+'landmarks/H1')
    check(doc.all('html')[0].get('lang') == 'pt-BR', label+'language')
    check(doc.meta('viewport') == ['width=device-width, initial-scale=1'], label+'zoom-friendly viewport')
    check(len(doc.all('title')) == 1, label+'title')
    names.append(doc.all('title')[0].text())
    check(len(doc.meta('description')) == 1 and bool(doc.meta('description')[0]), label+'description')
    descriptions += doc.meta('description')
    check(all('noindex' not in value for value in doc.meta('robots')), label+'robots meta')
    check(robots.can_fetch('Googlebot', ORIGIN+pathname), label+'robots.txt')
    check([x.get('href') for x in doc.all('link') if x.get('rel') == 'canonical'] == [ORIGIN+pathname], label+'canonical')
    check(doc.meta('og:url') == [ORIGIN+pathname], label+'Open Graph URL')
    check(any(x.get('href') == '#conteudo' for x in doc.all('a')), label+'skip link')
    check(doc.all('main')[0].get('tabindex') == '-1', label+'skip target')
    ids = [x.get('id') for x in doc.all() if x.get('id')]
    check(len(ids) == len(set(ids)), label+'unique IDs')
    fetched = {ROOT/'index.html' if pathname == '/' else ROOT/pathname.lstrip('/')}
    for node in doc.all():
        for attribute in ('aria-controls','aria-labelledby','aria-describedby','for'):
            if node.get(attribute): check(all(x in ids for x in node.get(attribute).split()), label+'unresolved '+attribute)
        if node.tag in ('a','button','summary'):
            check(bool(node.get('aria-label') or node.text().strip() or any(x.get('alt') for x in node.all('img'))), label+'unnamed interactive control')
        if node.tag == 'nav': check(bool(node.get('aria-label')), label+'unnamed navigation')
        if node.tag == 'img':
            check('alt' in node.attrs, label+'image alternative')
            check(node.get('width').isdigit() and node.get('height').isdigit(), label+'image layout dimensions')
        if node.tag in ('input','select','textarea'):
            ancestor = node.parent
            while ancestor and ancestor.tag != 'label': ancestor = ancestor.parent
            check(bool(ancestor or any(x.get('for') == node.get('id') and node.get('id') for x in doc.all('label'))), label+'form label')
        if node.get('target') == '_blank': check('noopener' in node.get('rel').split(), label+'external tab safety')
        attr = 'src' if node.tag in ('img','script') else 'href'
        if node.tag not in ('a','link','img','script') or not node.get(attr): continue
        url = urlsplit(urljoin(ORIGIN+pathname, node.get(attr)))
        if url.netloc == 'wa.me': check(url.path == '/5594981081535', label+'WhatsApp destination')
        if url.netloc != urlsplit(ORIGIN).netloc: continue
        target = ROOT / (unquote(url.path).lstrip('/') or 'index.html')
        check(target.is_file(), label+'missing resource '+node.get(attr))
        if url.fragment:
            dest = pages.get(url.path)
            check(dest is not None and any(x.get('id') == unquote(url.fragment) for x in dest.all()), label+'broken anchor '+node.get(attr))
        if node.tag in ('img','script') and node.get('loading') != 'lazy' or node.get('rel') in ('stylesheet','preload'):
            fetched.add(target)
        if node.tag == 'script': check('defer' in node.attrs, label+'nonblocking script')
    structured = [json.loads(n.text()) for n in doc.all('script') if n.get('type') == 'application/ld+json']
    organization = next(x for x in structured if x.get('@type') == 'Organization')
    check(organization['telephone'] == '+55 94 98108-1535', label+'organization contact')
    check(organization['address']['addressLocality'] == 'Novo Repartimento', label+'organization locality')
    baseline_file = 'index.html' if pathname == '/' else pathname.lstrip('/')
    baseline = subprocess.check_output(['git','show',BASELINE+':'+baseline_file], cwd=ROOT, text=True)
    base_doc = Document(baseline)
    check({x.get('id') for x in base_doc.all() if x.get('id')} <= set(ids), label+'published anchors preserved')
    if pathname != '/':
        current_main = re.search(r'<main.*?</main>', (ROOT/baseline_file).read_text(), re.S).group()
        old_main = re.search(r'<main.*?</main>', baseline, re.S).group()
        check(current_main.replace(' tabindex="-1"','') == old_main, label+'news content unchanged')
        check(structured == [json.loads(n.text()) for n in base_doc.all('script') if n.get('type') == 'application/ld+json'], label+'news facts/schema/dates unchanged')
        check(names[-1] == base_doc.all('title')[0].text() and doc.meta('description') == base_doc.meta('description'), label+'news SEO preserved')
    for field in ('organization','city','contact','kind','idea'):
        check(any(n.get('name') == field and 'required' in n.attrs for n in doc.all()), label+'proposal contract '+field)
    check(any(n.get('id') == 'proposal-dialog' for n in doc.all('dialog')), label+'proposal dialog')
    for file in fetched:
        check(file.is_file(), label+'initial resource '+str(file))
    size = sum(p.stat().st_size for p in fetched if p.is_file())
    if pathname == '/': size += (ROOT/'cuidado-isnp.webp').stat().st_size
    initial_bytes.append((pathname,size))
    check(size < 800_000, label+'initial source resource budget (<800 KB uncompressed)')

check(len(set(names)) == len(names), 'Unique page titles')
check(len(set(descriptions)) == len(descriptions), 'Unique descriptions')
home = pages['/']
check({p.lstrip('/') for p in pages if p != '/'} <= {n.get('href') for n in home.all('a')}, 'All news reachable from home')
for css in ROOT.glob('*.css'):
    for value in re.findall(r"url\(['\"]?([^)'\"]+)",css.read_text()):
        check((css.parent/value).is_file(), css.name+': CSS asset '+value)
check((ROOT/'assets/fonts/OFL.txt').is_file(), 'Font license')

# Source-level text contrast, separate from rendered image/background checks.
def luminance(color):
    rgb = [int(color[i:i+2],16)/255 for i in (1,3,5)]
    return sum((v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4)*w for v,w in zip(rgb,(.2126,.7152,.0722)))
for fg,bg in [('#173c2c','#ffffff'),('#586b60','#ffffff'),('#586b60','#f3f6f3'),('#ffffff','#075437'),('#ffffff','#247443'),('#c0dda9','#073c2c'),('#658173','#ffffff'),('#658173','#f3f6f3')]:
    a,b = sorted((luminance(fg),luminance(bg)))
    # Muted display headings are large text; body copy requires 4.5:1.
    required = 3 if fg == '#658173' else 4.5
    check((b+.05)/(a+.05) >= required, 'Contrast '+fg+' on '+bg)
if errors: raise SystemExit('\n'.join(errors))
print(f'PASS — {checks} checks across {len(pages)} pages. All four article bodies, schema, dates and published anchors preserved.')
for page,size in initial_bytes: print(f'  {page}: {size:,} source bytes before compression (eager resources; home includes desktop hero)')
print('Limit: static checks do not render layouts or measure Core Web Vitals.')
