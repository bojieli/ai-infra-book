"""Read-only extraction and identity checks for this six-paper bundle."""
from pathlib import Path
from html.parser import HTMLParser
from hashlib import sha256, sha1
import json, re, subprocess, unicodedata

ORDERS = [173, 174, 176, 177, 178, 179]
PDFS = {173: '173-arxiv-v2', 174: '174-author-paper',
        176: '176-arxiv-v5', 177: '177-author-paper', 179: '179-author-paper'}

def norm(s):
    return ''.join(c for c in unicodedata.normalize('NFKD', s).lower()
                   if c.isalnum() and not unicodedata.combining(c))

def whitespace(s):
    return ' '.join(s.split())

class HTML(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.meta = {}; self.text = []; self.links = []
        self.abstract = []; self.in_abstract = False; self.descriptor = False
        self.scripts = []; self.script = None
        self.feed(source)
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'meta' and 'name' in a:
            self.meta.setdefault(a['name'], []).append(a.get('content', ''))
        if tag == 'a': self.links.append(a.get('href', ''))
        if tag == 'blockquote' and 'abstract' in a.get('class', '').split():
            self.in_abstract = True
        if self.in_abstract and tag == 'span' and a.get('class') == 'descriptor':
            self.descriptor = True
        if tag == 'br' and self.in_abstract: self.abstract.append(' ')
        if tag == 'script' and a.get('type') == 'application/ld+json': self.script = []
    def handle_endtag(self, tag):
        if tag == 'blockquote': self.in_abstract = False
        if tag == 'span': self.descriptor = False
        if tag == 'script' and self.script is not None:
            self.scripts.append(''.join(self.script)); self.script = None
    def handle_data(self, text):
        self.text.append(text)
        if self.in_abstract and not self.descriptor: self.abstract.append(text)
        if self.script is not None: self.script.append(text)

def html(base, file):
    return HTML((base / file).read_text())

def record_file(base, filename):
    p = base / filename; data = p.read_bytes()
    return {'file': str(p), 'bytes': len(data), 'sha256': sha256(data).hexdigest()}

def first_page(base, prefix, mode='default'):
    flags = [] if mode == 'default' else ['-' + mode]
    return subprocess.check_output(['pdftotext', '-f', '1', '-l', '1', *flags,
                                    str(base / (prefix + '.pdf')), '-'])

def extract(base, order):
    if order in [173, 176]:
        name = f'{order}-arxiv.html'; h = html(base, name)
        return whitespace(''.join(h.abstract)), name, {
            'kind': 'arxiv_html', 'selector': 'blockquote.abstract excluding span.descriptor',
            'normalization': 'HTMLParser entity decoding; concatenate text nodes, br -> space; collapse whitespace'}
    if order == 178:
        name = '178-institution.html'; h = html(base, name)
        a = [json.loads(s) for s in h.scripts if json.loads(s).get('@type') == 'ScholarlyArticle']
        assert len(a) == 1
        return whitespace(a[0]['abstract']), name, {
            'kind': 'institution_jsonld', 'selector': 'script[type=application/ld+json], @type=ScholarlyArticle, abstract',
            'normalization': 'JSON decode and whitespace collapse; retain copyright suffix'}
    prefix = PDFS[order]; mode = 'raw' if order in [174, 179] else 'default'
    t = first_page(base, prefix, mode).decode()
    startmark, endmark = {174: ('ABSTRACT\n', '\nACM Reference Format:'),
                          177: ('Abstract\n', '\nCCS Concepts:'),
                          179: ('Abstract\n', '\n1 Introduction')}[order]
    start = t.index(startmark) + len(startmark); end = t.index(endmark, start)
    text = whitespace(t[start:end])
    return text, prefix + '.pdf', {
        'kind': 'pdf_first_page', 'physical_page': 1, 'pdftotext_mode': mode,
        'start_marker': startmark, 'end_marker': endmark,
        'line_range_in_extraction': [t[:start].count('\n') + 1, t[:end].count('\n') + 1],
        'normalization': 'whitespace collapse only; preserve printed line-end hyphens; no footer removal or manual stitching'}

def identities(base):
    selection = json.loads((base / 'selection-snapshot.json').read_text())
    registry = json.loads((base / 'registry-original.json').read_text())['message']['items']
    official = {}
    program = norm(' '.join(html(base, 'program-original.html').text))
    for s in selection['identity_records']:
        order = s['program_order']
        matches = [x for x in registry if x['DOI'].lower() == s['doi'].lower()]
        assert len(matches) == 1
        x = matches[0]
        assert norm(x['title'][0]) == norm(s['title']) and norm(s['title']) in program
        assert [(a.get('given'), a['family']) for a in x['author']] == [
            (a.get('given'), a['family']) for a in s['original_registry_records'][0]['authors']]
        official[order] = x
    assert sorted(official) == ORDERS
    return official

def verify_identities(base):
    official = identities(base); reports = []
    for order, x in official.items():
        doi = x['DOI']; title = x['title'][0]
        authors = [a.get('given', '') + ' ' + a['family'] for a in x['author']]
        aliases = [a['family'] + ', ' + a.get('given', '') for a in x['author']]
        detail = {'program_order': order, 'doi': doi, 'formal_registry_identity': True,
                  'body_pages_read': [], 'publisher_abstract_equivalence_verified': False}
        if order in [173, 176, 178]:
            h = html(base, f'{order}-institution.html' if order == 178 else f'{order}-arxiv.html')
            assert norm(h.meta['citation_title'][0]) == norm(title)
            if order == 176:
                actual = [norm(a) for a in h.meta['citation_author']]
                assert actual == [norm(aliases[i]) for i in [0, 1, 2, 4, 3]]
                blog = html(base, '176-author-publication.html')
                assert 'https://arxiv.org/pdf/2311.02206' in blog.links
                assert norm('Optimizing Datalog for the GPU (ASPLOS ‘25)') in norm(' '.join(blog.text))
                detail['version_caveat'] = 'arXiv HTML last two authors are reversed; PDF p1 author order matches formal registry; arXiv v5 has no official DOI on p1.'
            else:
                assert h.meta['citation_doi'] == [doi]
                assert list(map(norm, h.meta['citation_author'])) == list(map(norm, aliases))
            if order == 178:
                j = [json.loads(s) for s in h.scripts if json.loads(s).get('@type') == 'ScholarlyArticle'][0]
                assert j['identifier'] == doi and norm(j['name']) == norm(title)
                assert [norm(a['name']) for a in j['author']] == list(map(norm, aliases))
        if order in PDFS:
            prefix = PDFS[order]; text = first_page(base, prefix).decode()
            assert norm(title) in norm(text)
            head = text[:text.index('ABSTRACT' if order == 174 else 'Abstract')]
            if order != 179:
                positions = [norm(head).index(norm(a)) for a in authors]
                assert positions == sorted(positions)
                detail['pdf_title_authors'] = True
            else:
                assert all(norm(a) not in norm(head) for a in authors)
                detail['pdf_title_authors'] = False
                detail['version_caveat'] = 'Anonymous 14-page artifact manuscript; p1 has no authors or DOI; formal publication is 15 pages. Related through fixed official lab README, not assumed publisher-equivalent.'
            if order in [173, 174, 177]:
                assert doi in re.sub(r'\s+', '', text)
                detail['pdf_official_doi'] = True
            else:
                assert doi not in re.sub(r'\s+', '', text)
                detail['pdf_official_doi'] = False
            if order == 173: assert 'arXiv:2408.12073v2' in text
            if order == 176: assert 'arXiv:2311.02206v5' in text
        reports.append(detail)
    commit = json.loads((base / '179-artifact-commit.json').read_text())
    tree = json.loads((base / '179-artifact-tree.json').read_text())
    assert commit['sha'] == tree['sha'] == '30b997ad3b42fb8c02f344b08ae716d119f87042'
    for local, remote in [('179-author-paper.pdf', 'doc/NF2FS.pdf'), ('179-artifact-fixed-README.md', 'README.md')]:
        b = (base / local).read_bytes()
        sha = sha1(b'blob ' + str(len(b)).encode() + b'\0' + b).hexdigest()
        assert next(t for t in tree['tree'] if t['path'] == remote)['sha'] == sha
    readme = (base / '179-artifact-fixed-README.md').read_text()
    assert official[179]['title'][0] in readme and 'ASPLOS\'25' in readme and '/doc/NF2FS.pdf' in readme
    return reports
