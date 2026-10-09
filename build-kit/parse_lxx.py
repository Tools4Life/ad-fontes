"""Extract one LXX chapter (Rahlfs 1935, Eliran Wong / CATSS data) + LXX-wide lemma counts.
Usage: python3 -I parse_lxx.py <lxx_dir> <book_label e.g. 'Deut'> <chapter> <out_json>
"""
import sys, os, re, json, collections

d, bk, ch, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]

def col(path, idx=2):
    res = {}
    with open(os.path.join(d, path), encoding='utf-8-sig') as fh:
        for line in fh:
            p = line.rstrip('\n').split('\t')
            if len(p) > idx and p[0].isdigit():
                res[int(p[0])] = p[idx] if idx < len(p) else ''
    return res

# verse starts
starts = []
with open(os.path.join(d, '01_wordlist_unicode/alignment_with_OSSP/E-verse.csv'), encoding='utf-8-sig') as fh:
    for line in fh:
        p = line.rstrip('\n').split('\t')
        m = re.search(r'「(\S+) (\d+):(\d+)」', p[2])
        if m:
            starts.append((int(p[0]), m.group(1), int(m.group(2)), int(m.group(3))))
starts.sort()

text = col('01_wordlist_unicode/text_accented.csv', 2)
lemma = {int(k): v for k, v in col('02_lexemes/OSSP_lexemes.csv', 1).items()}
lexno = {int(k): v for k, v in col('02_lexemes/Lex_LXXno.csv', 1).items()}
gloss = {int(k): v for k, v in col('06_English_gloss/beta.csv', 1).items()}
tr = {int(k): v for k, v in col('04_SBL_transliteration/final_transliteration_SBL.csv', 1).items()}
morph = {}
with open(os.path.join(d, '03b_descriptions_on_morphology_codes/morphology_623693_with_description.csv'), encoding='utf-8-sig') as fh:
    for line in fh:
        p = line.rstrip('\n').split('\t')
        if p[0].isdigit():
            morph[int(p[0])] = (p[1] if len(p) > 1 else '', p[2] if len(p) > 2 else '', p[3] if len(p) > 3 else '')

lex = {}
with open(os.path.join(d, '11_end-users_files/LXX_lexicon_formatted_for_UniqueBibleAppPlus.csv'), encoding='utf-8-sig') as fh:
    for line in fh:
        p = line.rstrip('\n').split('\t')
        if len(p) >= 5:
            lex[p[0]] = dict(lemma=p[1], tr=p[2], pos=p[3], gloss=p[4])

# map every word to its verse
maxw = max(text)
ref_of = {}
for i, (s, b, c, v) in enumerate(starts):
    e = starts[i + 1][0] if i + 1 < len(starts) else maxw + 1
    for w in range(s, e):
        ref_of[w] = (b, c, v)

cnt = collections.Counter(); book_cnt = collections.Counter()
refs = collections.defaultdict(list)
for w, r in ref_of.items():
    k = lexno.get(w)
    if not k:
        continue
    cnt[k] += 1
    book_cnt[(r[0], k)] += 1
    refs[k].append(f'{r[0]} {r[1]}:{r[2]}')

verses = collections.OrderedDict()
for w in sorted(ref_of):
    b, c, v = ref_of[w]
    if b == bk and c == ch:
        k = lexno.get(w)
        L = lex.get('L' + str(k), {}) if k else {}
        verses.setdefault(v, []).append(dict(
            g=text.get(w, ''), tr=tr.get(w, ''), lemma=lemma.get(w, ''), lexid=k,
            gloss=gloss.get(w, '').replace('<br>', ' '),
            code=morph.get(w, ('', '', ''))[0], pos=morph.get(w, ('', '', ''))[1],
            parse=morph.get(w, ('', '', ''))[2],
            lexgloss=L.get('gloss', ''),
            n_lxx=cnt.get(k, 0), n_book=book_cnt.get((bk, k), 0),
            refs=refs[k] if cnt.get(k, 0) <= 300 else None))
json.dump(verses, open(out, 'w'), ensure_ascii=False)
print({v: ' '.join(x['g'] for x in ws) for v, ws in list(verses.items())})
