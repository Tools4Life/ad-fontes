"""Parse STEPBible TAHOT files into a word list + concordance index.
Usage: python3 -I parse_tahot.py <step_dir> <out_dir>
"""
import sys, os, re, json, glob, collections

step, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
REF = re.compile(r'^(\w{3})\.(\d+)\.(\d+)(?:\((\d+)\.(\d+)\))?#(\d+)=(\S+)$')

words = []
for f in sorted(glob.glob(os.path.join(step, 'Translators Amalgamated OT+NT', 'TAHOT *.txt'))):
    with open(f, encoding='utf-8-sig') as fh:
        for line in fh:
            cols = line.rstrip('\n').split('\t')
            m = REF.match(cols[0])
            if not m or len(cols) < 12:
                continue
            bk, ch, vs, hch, hvs, wn, typ = m.groups()
            words.append(dict(
                book=bk, ch=int(ch), vs=int(vs),
                hch=int(hch) if hch else None, hvs=int(hvs) if hvs else None,
                wn=int(wn), type=typ,
                heb=cols[1], tr=cols[2], en=cols[3], ds=cols[4], gram=cols[5],
                mvar=cols[6], svar=cols[7], root=cols[8], alt=cols[9],
                conj=cols[10], exp=cols[11]))

def main_strong(ds):
    m = re.search(r'\{(H\d+[A-Z]?)\}', ds)
    return m.group(1) if m else None

def base(s):
    return re.match(r'H\d+', s).group(0) if s else None

cnt_d = collections.Counter(); cnt_b = collections.Counter()
book_d = collections.Counter(); book_b = collections.Counter()
refs_b = collections.defaultdict(list)
for w in words:
    if not (w['type'].startswith('L') or w['type'].startswith('Q')):
        # Only count Leningrad-text words (avoid double counting variant rows)
        continue
    s = main_strong(w['ds'])
    if not s:
        continue
    b = base(s)
    cnt_d[s] += 1; cnt_b[b] += 1
    book_d[(w['book'], s)] += 1; book_b[(w['book'], b)] += 1
    refs_b[b].append(f"{w['book']} {w['ch']}:{w['vs']}")

json.dump(words, open(os.path.join(out, 'tahot_words.json'), 'w'), ensure_ascii=False)
json.dump(dict(cnt_d=cnt_d, cnt_b=cnt_b,
               book_d={f'{k[0]}|{k[1]}': v for k, v in book_d.items()},
               book_b={f'{k[0]}|{k[1]}': v for k, v in book_b.items()},
               refs_b=refs_b),
          open(os.path.join(out, 'concordance.json'), 'w'), ensure_ascii=False)
types = collections.Counter(w['type'] for w in words)
print('words', len(words), 'types', types.most_common(15))
