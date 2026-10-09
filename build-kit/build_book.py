"""Build/merge one chapter into a per-book JSON data file for the reader.
Usage: python3 -I build_book.py <scratch> <BookCode e.g. Deu> <chapter> <notes.json> <lxx_label e.g. Deut> <bsb_name e.g. Deuteronomy> <out_book.json>
"""
import sys, os, re, json, csv, collections, subprocess

S, BK, CH, NOTES, LXXBK, BSBNAME, OUT = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4], sys.argv[5], sys.argv[6], sys.argv[7]
STEP = os.path.join(S, 'data', 'step')
CANON = ['Gen','Exo','Lev','Num','Deu','Jos','Jdg','Rut','1Sa','2Sa','1Ki','2Ki','1Ch','2Ch','Ezr','Neh','Est','Job','Psa','Pro','Ecc','Sng','Isa','Jer','Lam','Ezk','Dan','Hos','Jol','Amo','Oba','Jon','Mic','Nam','Hab','Zep','Hag','Zec','Mal']
ORDER = {b: i for i, b in enumerate(CANON)}

words = json.load(open(os.path.join(S, 'out', 'tahot_words.json'), encoding='utf-8'))

# ---- morphology code expansions (TEHMC)
TEHMC = {}
for line in open(os.path.join(STEP, 'Morphology codes', 'TEHMC - Translators Expansion of Hebrew Morphology Codes - STEPBible.org CC BY.txt'), encoding='utf-8-sig'):
    p = line.rstrip('\n').split('\t')
    if len(p) > 1 and p[0] and p[0][0] in 'HA' and ' ' not in p[0] and '=' in p[1]:
        TEHMC.setdefault(p[0], p[1].strip())

# ---- lexicon (TBESH) keyed by dStrong
TBESH = {}
for line in open(os.path.join(STEP, 'Lexicons', 'TBESH - Translators Brief lexicon of Extended Strongs for Hebrew - STEPBible.org CC BY.txt'), encoding='utf-8-sig'):
    p = line.rstrip('\n').split('\t')
    if len(p) >= 8 and re.match(r'^H\d', p[0]):
        key = p[1].split('=')[0].strip()
        if re.match(r'^H\d+[A-Z]?$', key):
            TBESH.setdefault(key, dict(rel=p[1].split('=', 1)[1].strip() if '=' in p[1] else '', lemma=p[3], tr=p[4], morph=p[5], gloss=p[6], defn=p[7]))

def clean_def(s):
    s = re.sub(r'<(?!/?(br|b|i)\b)[^>]*>', '', s, flags=re.I)
    return re.sub(r'<br\s*/?>', '<br>', s, flags=re.I)

def main_strong(ds):
    m = re.search(r'\{(H\d+[A-Z]?)\}', ds)
    return m.group(1) if m else None

def base(s):
    return re.match(r'H\d+', s).group(0)

counted = [w for w in words if w['type'][0] in 'LQ']
by_base = collections.defaultdict(list)
for w in counted:
    s = main_strong(w['ds'])
    if s:
        by_base[base(s)].append((s, w['book'], w['ch'], w['vs']))

# ---- the chapter
ch = [w for w in words if w['book'] == BK and w['ch'] == CH]
verses = collections.OrderedDict()
codes_used, strongs_used, segs_used = set(), set(), set()
for w in ch:
    segs = []
    hebs = w['heb'].split('/')
    grams = w['gram'].split('/')
    dss = re.split(r'/', w['ds'])
    # glosses per segment from expanded tags
    exps = w['exp'].split('/')
    for i, g in enumerate(grams):
        code = g if i == 0 else 'H' + g
        codes_used.add(code)
        d = dss[i] if i < len(dss) else ''
        sm = re.search(r'(H\d+[A-Z]?)', d)
        st = sm.group(1) if sm else ''
        is_main = '{' in d
        e = exps[i] if i < len(exps) else ''
        em = re.search(r'=([^=]*)$', e.replace('{', '').replace('}', '').split('\\')[0])
        gl = ''
        if em:
            gl = em.group(1).split('»')[0].lstrip(': ').replace('_', ' ')
        segs.append(dict(h=re.sub(r'\\.*$', '', hebs[i]) if i < len(hebs) else '', c=code, s=st, m=is_main, gl=gl))
        if st:
            (strongs_used if is_main else segs_used).add(st)
    disp = w['heb'].replace('/', '')
    disp = disp.replace('\\', '')
    marker = ''
    mk = re.search(r'׃\s*([ספ])\s*$', disp)
    if mk:
        marker = mk.group(1)
        disp = re.sub(r'\s*[ספ]\s*$', '', disp)
    verses.setdefault(w['vs'], []).append(dict(
        n=w['wn'], h=disp.strip(), t=w['tr'].replace('/', ''), g=w['en'].replace('/', ''),
        k=main_strong(w['ds']), segs=segs, ty=w['type'], mv=w['mvar'], sv=w['svar'], mk=marker))

# ---- lexicon entries for main words, with concordance
lex = {}
for s in sorted(strongs_used):
    b = base(s)
    occ = by_base.get(b, [])
    tags = collections.Counter(o[0] for o in occ)
    books = collections.Counter(o[1] for o in occ)
    occ_sorted = sorted(occ, key=lambda o: (ORDER.get(o[1], 99), o[2], o[3]))
    t = TBESH.get(s) or TBESH.get(b) or {}
    if not t:
        # fall back to the expanded tag in the text data itself
        for w in ch:
            m = re.search(r'\{' + s + r'=([^=]*)=([^}]*)\}', w['exp'])
            if m:
                t = dict(lemma=m.group(1), gloss=m.group(2).split('»')[0].lstrip(': ').replace('_', ' '), tr='', morph='', defn='')
                break
    entry = dict(
        lemma=t.get('lemma', ''), tr=t.get('tr', ''), morph=t.get('morph', ''), gloss=t.get('gloss', ''),
        defn=clean_def(t.get('defn', '')), rel=t.get('rel', ''),
        total=len(occ), tagCount=tags.get(s, 0),
        tags={k: [v, (TBESH.get(k) or {}).get('gloss', '')] for k, v in tags.most_common()},
        inBook=books.get(BK, 0),
        books=[[bk, n] for bk, n in sorted(books.items(), key=lambda x: ORDER.get(x[0], 99))])
    if len(occ_sorted) <= 400:
        entry['refs'] = [f'{o[1]} {o[2]}:{o[3]}' + ('' if o[0] == s else f'|{o[0]}') for o in occ_sorted]
    lex[s] = entry
for s in sorted(segs_used):
    t = TBESH.get(s) or {}
    lex.setdefault(s, dict(lemma=t.get('lemma', ''), tr=t.get('tr', ''), morph=t.get('morph', ''), gloss=t.get('gloss', ''), defn=clean_def(t.get('defn', '')), affix=True))

morph = {c: TEHMC.get(c, '') for c in sorted(codes_used)}

# ---- English translations (all public domain; scrollmapper/bible_databases)
TRANS = [
    ('BSB', 'Berean Standard Bible (2023)', 'Modern, readable; public domain since 2023.'),
    ('NHEB', 'New Heart English Bible', 'Modern public-domain update of the World English Bible.'),
    ('KJV', 'King James Version (1769)', 'Traditional English; from the Masoretic Text and the Textus Receptus.'),
    ('ASV', 'American Standard Version (1901)', 'Very literal; renders the divine name as Jehovah.'),
    ('YLT', "Young's Literal Translation (1898)", 'Word-for-word; tries to keep Hebrew verb forms and word order.'),
    ('Rotherham', 'Rotherham Emphasized Bible (1902)', 'Literal; uses Yahweh; punctuation marks Hebrew emphasis.'),
    ('JPS', 'Jewish Publication Society Tanakh (1917)', 'Jewish translation of the Hebrew Bible. This digital copy writes HaShem and G-d for the divine names.'),
    ('DRC', 'Douay-Rheims, Challoner revision (1752)', 'Catholic; translated from the Latin Vulgate, so it can differ from the Hebrew.'),
    ('Geneva1599', 'Geneva Bible (1599)', 'Reformation-era English, before the KJV; original spelling.'),
]
tr_text = {}
for code, _, _ in TRANS:
    path = os.path.join(S, 'data', 'sm', 'formats', 'csv', code + '.csv')
    if not os.path.exists(path):
        continue
    with open(path, encoding='utf-8') as fh:
        for r in csv.DictReader(fh):
            if r['Book'] == BSBNAME and r['Chapter'].isdigit() and int(r['Chapter']) == CH:
                tr_text.setdefault(int(r['Verse']), {})[code] = r['Text']
bsb = {v: d.get('BSB', '') for v, d in tr_text.items()}

# ---- LXX
lxx_path = os.path.join(S, 'out', f'lxx_{BK.lower()}{CH}.json')
subprocess.run([sys.executable, '-I', os.path.join(S, 'build', 'parse_lxx.py'), os.path.join(S, 'data', 'LXX-Rahlfs-1935-x'), LXXBK, str(CH), lxx_path], check=True, stdout=subprocess.DEVNULL)
lxx = json.load(open(lxx_path, encoding='utf-8'))
lxx_lex = {}
lxx_out = {}
for v, ws in lxx.items():
    arr = []
    for x in ws:
        k = x['lexid'] or ''
        if k and k not in lxx_lex:
            lxx_lex[k] = dict(lemma=x['lemma'], gloss=x['lexgloss'] or x['gloss'], total=x['n_lxx'], inBook=x['n_book'], refs=x['refs'])
        arr.append(dict(g=x['g'], tr=x['tr'], k=k, code=x['code'], pos=x['pos'], parse=x['parse'], gl=x['gloss']))
    lxx_out[int(v)] = arr

notes = json.load(open(NOTES, encoding='utf-8'))

chap = dict(
    verses=[dict(v=v, he=verses[v], bsb=bsb.get(v, ''), en=tr_text.get(v, {}), lxx=lxx_out.get(v, [])) for v in verses],
    paragraphs=notes['paragraphs'], paragraphNote=notes['paragraphNote'],
    sections=notes['sections'], wordNotes=notes['words'],
    lxxNotes=notes['lxx'])

book = json.load(open(OUT, encoding='utf-8')) if os.path.exists(OUT) else dict(code=BK, name=BSBNAME, testament='OT', lxxCode=LXXBK, chapters={}, lex={}, lxxLex={}, morph={})
book['chapters'][str(CH)] = chap
book['translations'] = [dict(code=c, name=n, note=d) for c, n, d in TRANS if any(c in x for x in tr_text.values())]
book['lex'].update(lex)
book['lxxLex'].update(lxx_lex)
book['morph'].update(morph)
json.dump(book, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('verses', len(chap['verses']), 'lex', len(lex), 'lxxLex', len(lxx_lex), 'bytes', os.path.getsize(OUT))
missing = [s for s in strongs_used if not lex[s].get('lemma')]
print('missing lexicon:', missing)
print('missing morph:', [c for c, v in morph.items() if not v])
print('bsb verses', len(bsb))
