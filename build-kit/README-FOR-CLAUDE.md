# Ad Fontes build kit (for Claude)

Ad Fontes is Eddie's chapter-by-chapter Hebrew Bible study reader, hosted at
https://tools4life.github.io/ad-fontes/ (repo Tools4Life/ad-fontes, GitHub Pages, main branch, root).
Sync uses Firebase project ops-hub-9bebc (same login as Ops Hub); config.js in the repo holds the public config.

## Method and content rules (agreed with Eddie)
- Historical-grammatical. Reference tool only: no devotional framing, no study questions.
- Every analytical claim is tagged data / consensus / debated with a confidence level (high/moderate/low).
- Debated questions: lay out the positions, do not adjudicate. No creedal/trinitarian vocabulary; work from the text.
- Usage over etymology (etymology labeled "background only").
- OT base: Leningrad Codex (STEPBible TAHOT); show Septuagint (Rahlfs/CATSS) differences with per-verse notes.
- NT (when added): critical text with Byzantine/TR variants flagged (STEPBible TAGNT). 66-book canon.
- Pericope mode = Masoretic setumah/petuchah paragraph markers (read from the data; check the marker before v1 too).

## Adding a chapter
1. Data (all on GitHub, reachable from the workspace):
   - git clone --depth 1 --filter=blob:none --no-checkout https://github.com/STEPBible/STEPBible-Data data/step
     then checkout "Translators Amalgamated OT+NT/", the TBESH lexicon and TEHMC morphology files.
   - https://github.com/eliranwong/LXX-Rahlfs-1935 (checkout files used by parse_lxx.py)
   - https://github.com/scrollmapper/bible_databases (formats/csv/<CODE>.csv for the translations listed in build_book.py)
   Layout expected by the scripts: $S/data/step, $S/data/LXX-Rahlfs-1935-x, $S/data/sm, $S/build/parse_lxx.py, $S/out/.
2. python3 -I parse_tahot.py $S/data/step $S/out   (word list + concordance for the whole Hebrew Bible)
3. Write notes/<book><chapter>.json in the same shape as notes/deu7.json:
   paragraphs, paragraphNote, sections (passage panel), words (keyed "verse.wordNumber"), lxx (per-verse differences).
   Verify every count/reference against the data before writing it.
4. Copy the repo's current book file (e.g. deu.json) to $S/site/books/, then:
   python3 -I build_book.py $S <BookCode> <chapter> notes/<file>.json <LXX book label> <English book name> $S/site/books/<book>.json
   (it merges the chapter into the existing book file). For a new book, add it to index.json (flat file names).
5. Publish: if the session can push to Tools4Life/ad-fontes (attach it with push access), commit the changed files
   (book json, and index.json if a book was added) to main and push; the site updates in about a minute.
   Otherwise give Eddie the changed files to upload via GitHub "Add file > Upload files", with click-by-click steps
   (he is not very technical). Tell him to reload Ad Fontes afterwards.
   Requests usually arrive from the app's Menu > Request a chapter, as a pasted message naming the book and chapter.

## Rebuilding the app page itself
The live index.html in the repo root is the source of truth for the page (it has the slide-in menu, margin notes,
Request a chapter, etc.). Edit it directly. Do NOT regenerate it from reader-template.html, which is an older
claude.ai version and would undo later changes. For reference only:
reader-template.html is the claude.ai version; to_reader_app.py converts it to the standalone app
(python3 -I to_reader_app.py <dir with index.html, index.json, books/> <outdir> <config.js>).
