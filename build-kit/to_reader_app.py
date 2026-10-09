"""Turn the claude.ai Text & Meaning reader into a standalone web app (GitHub Pages + the same Firebase project as Ops Hub)."""
import sys, os, json, shutil
from PIL import Image, ImageDraw, ImageFont
site, outdir, config_js = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(outdir, exist_ok=True)
t = open(os.path.join(site, 'index.html'), encoding='utf-8').read()

def rep(old, new, count=1):
    global t
    n = t.count(old)
    assert n == count, (n, old[:90])
    t = t.replace(old, new)

# ---------- icon: cream alef on lapis
def make_icon(size):
    img = Image.new('RGB', (size, size), (40, 70, 138))
    d = ImageDraw.Draw(img)
    for path in ['/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf']:
        try:
            f = ImageFont.truetype(path, int(size * 0.62))
            if f.getmask('א').getbbox():
                break
        except Exception:
            f = None
    ch = 'א'
    bbox = d.textbbox((0, 0), ch, font=f)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    d.text(((size - w) / 2 - bbox[0], (size - h) / 2 - bbox[1] - size * 0.02), ch, font=f, fill=(246, 239, 222))
    d.rectangle([size * 0.28, size * 0.80, size * 0.72, size * 0.815], fill=(214, 186, 120))
    return img
for s in (180, 192, 512):
    make_icon(s).save(os.path.join(outdir, f'icon-{s}.png'))

# ---------- standalone document
head = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="Ad Fontes">
<link rel="manifest" href="manifest.json">
<link rel="apple-touch-icon" href="icon-180.png">
<link rel="icon" type="image/png" href="icon-192.png">
<style>body{margin:0}[hidden]{display:none!important}:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}</style>
'''
style_end = t.index('</style>') + len('</style>')
t = head + t[:style_end] + '\n</head>\n<body>\n' + t[style_end:] + '\n</body>\n</html>\n'

# ---------- sign-in panel styles
rep('.mylist .x{', '''.signin{position:fixed;inset:0;z-index:60;background:color-mix(in srgb,var(--bg) 92%,transparent);display:flex;align-items:center;justify-content:center;padding:24px 16px}
.signin[hidden]{display:none}
.signin form{width:100%;max-width:380px;background:var(--surface);border:1px solid var(--rule);border-radius:12px;padding:24px;display:grid;gap:12px}
.signin h2{margin:0;font-family:var(--f-text);font-size:24px}
.signin p{margin:0;color:var(--muted);font-size:15px}
.signin input{font:inherit;font-size:16px;color:var(--ink);background:var(--bg);border:1px solid var(--rule);border-radius:8px;padding:11px 12px}
.signin .err{color:var(--t-deb);font-family:var(--f-ui);font-size:14px;min-height:1.2em}
.signin .btns{display:flex;gap:8px;flex-wrap:wrap}
.signin .go{background:var(--ink);color:var(--bg);border:0;border-radius:8px;padding:10px 16px;font-family:var(--f-ui);font-size:15px;cursor:pointer}
.signin .alt{background:transparent;color:var(--ink);border:1px solid var(--rule);border-radius:8px;padding:10px 16px;font-family:var(--f-ui);font-size:15px;cursor:pointer}
.signin .lnk{background:none;border:0;color:var(--accent);font-family:var(--f-ui);font-size:14px;cursor:pointer;padding:4px 0;justify-self:start}
.sync{cursor:pointer;background:none;border:0;padding:4px 2px}
.mylist .x{''')

# ---------- sync chip becomes a button
rep('<span class="sync" id="sync" title="Bookmarks, your notes and your place are saved to your claude.ai account">This device</span>',
    '<button class="sync" id="sync" title="Sign in to sync bookmarks, notes and your place across devices">Sign in to sync</button>')

# ---------- sign-in markup
rep('<script>\n(function(){', '''<div class="signin" id="signin" hidden>
  <form id="siForm" novalidate>
    <h2>Sync your study</h2>
    <p id="siMsg">Sign in with the same email and password you use for Ops Hub. Bookmarks, notes and your place then follow you between devices.</p>
    <input id="siEmail" type="email" autocomplete="email" placeholder="Email">
    <input id="siPass" type="password" autocomplete="current-password" placeholder="Password (at least 6 characters)">
    <div class="err" id="siErr"></div>
    <div class="btns"><button class="go" type="submit">Sign in</button><button class="alt" type="button" id="siUp">Create account</button><button class="alt" type="button" id="siClose">Not now</button></div>
    <button class="lnk" type="button" id="siForgot">Forgot password?</button>
  </form>
</div>
<script>
window.Auth={email:null,_p:null,_r:null,ready(){if(!this._p)this._p=new Promise(r=>this._r=r);return this._p},resolve(v){this.ready();this._r(v)},signOut(){}};
(function(){''')

# ---------- Sync.init: wait for Firebase sign-in
rep("""    if(!window.claude||!window.claude.use){this.status('This device');return}
    const [db,user]=await Promise.all([claude.use('db'),claude.use('user')]);
    const uid=user?await user.id():null;
    if(!db||!uid){this.status('This device');return}
    this.db=db;this.uid=uid;
    this.ref=db.doc(`data/users/${uid}/reader`);""",
"""    this.status('Sign in to sync');
    const {db,id:uid}=await Auth.ready();
    if(!db||!uid){this.status('This device');return}
    this.db=db;this.uid=uid;
    this.ref=db.doc(`users/${uid}/app/reader`);""")

# chip click: sign in, or show account
rep("  $('#backdrop').onclick=closeSheet;",
"""  $('#backdrop').onclick=closeSheet;
  $('#sync').onclick=()=>{
    if(!Auth.email){document.getElementById('signin').hidden=false;setTimeout(()=>document.getElementById('siEmail').focus(),50);return}
    SEL=null;markSel();
    $('#panel').innerHTML=`<div class="ph"><span>Account</span><span><button data-back>Chapter notes</button> <button data-close>Close</button></span></div><p>Signed in as <b>${esc(Auth.email)}</b>. Your bookmarks, notes and place sync across your devices.</p><button class="chip" id="soBtn">Sign out on this device</button>`;
    wirePanel();$('#soBtn').onclick=()=>Auth.signOut();openSheet();
  };""")

rep('</script>\n\n</body>', '''</script>
<script src="config.js"></script>
<script type="module">
const V='10.12.2';
const box=document.getElementById('signin'),err=document.getElementById('siErr'),msg=document.getElementById('siMsg');
const MSG={'auth/invalid-credential':'That email and password don\\u2019t match. Try again, or tap Forgot password.','auth/user-not-found':'No account with that email yet. Tap Create account.','auth/email-already-in-use':'That email already has an account. Tap Sign in instead.','auth/weak-password':'Use at least 6 characters for the password.','auth/invalid-email':'That email address doesn\\u2019t look right.','auth/missing-password':'Type your password.','auth/network-request-failed':'No internet connection. Try again when you have signal.','auth/too-many-requests':'Too many tries. Wait a minute and try again.'};
const say=e=>{err.textContent=MSG[e&&e.code]||('Something went wrong'+(e&&e.code?' ('+e.code+')':'')+'.')};
document.getElementById('siClose').onclick=()=>{box.hidden=true};
if(window.__MOCK_DB){Auth.email='test@example.com';Auth.resolve({db:window.__MOCK_DB,id:'u1'})}
else if(window.OPS_CONFIG&&window.OPS_CONFIG.apiKey){
  try{
  const [{initializeApp},A,F]=await Promise.all([
    import(`https://www.gstatic.com/firebasejs/${V}/firebase-app.js`),
    import(`https://www.gstatic.com/firebasejs/${V}/firebase-auth.js`),
    import(`https://www.gstatic.com/firebasejs/${V}/firebase-firestore.js`)]);
  const app=initializeApp(window.OPS_CONFIG);
  const auth=A.getAuth(app);
  let fs;try{fs=F.initializeFirestore(app,{localCache:F.persistentLocalCache({tabManager:F.persistentMultipleTabManager()})})}catch(e){fs=F.getFirestore(app)}
  const ws=s=>({id:s.id,exists:s.exists(),data:()=>s.data(),metadata:s.metadata});
  const wq=s=>({docs:s.docs.map(ws),size:s.size,empty:s.empty,metadata:s.metadata});
  const D=p=>{const r=F.doc(fs,p);return{path:p,id:r.id,get:async()=>ws(await F.getDoc(r)),set:d=>F.setDoc(r,d),delete:()=>F.deleteDoc(r),collection:c=>C(p+'/'+c),onSnapshot:(n,e)=>F.onSnapshot(r,s=>n(ws(s)),e)}};
  const C=p=>{const r=F.collection(fs,p);return{path:p,doc:id=>D(p+'/'+id),get:async()=>wq(await F.getDocs(r)),onSnapshot:(n,e)=>F.onSnapshot(r,s=>n(wq(s)),e)}};
  const db={doc:D,collection:C};
  Auth.signOut=async()=>{try{await A.signOut(auth)}catch(e){}try{localStorage.removeItem('tm_marks')}catch(e){}location.reload()};
  let started=false;
  A.onAuthStateChanged(auth,u=>{if(u){Auth.email=u.email;box.hidden=true;if(!started){started=true;Auth.resolve({db,id:u.uid})}}});
  const em=document.getElementById('siEmail'),pw=document.getElementById('siPass');
  const busy=b=>box.querySelectorAll('button').forEach(x=>x.disabled=b);
  document.getElementById('siForm').addEventListener('submit',async e=>{e.preventDefault();err.textContent='';busy(true);try{await A.signInWithEmailAndPassword(auth,em.value.trim(),pw.value)}catch(x){say(x)}busy(false)});
  document.getElementById('siUp').onclick=async()=>{err.textContent='';busy(true);try{await A.createUserWithEmailAndPassword(auth,em.value.trim(),pw.value)}catch(x){say(x)}busy(false)};
  document.getElementById('siForgot').onclick=async()=>{err.textContent='';const v=em.value.trim();if(!v){err.textContent='Type your email first, then tap Forgot password.';return}try{await A.sendPasswordResetEmail(auth,v);msg.textContent='Check your email for a link to set a new password, then come back and sign in.'}catch(x){say(x)}};
  }catch(e){console.warn('sync unavailable',e)}
}
if('serviceWorker' in navigator&&location.protocol==='https:'){navigator.serviceWorker.register('sw.js').catch(()=>{})}
</script>

</body>''')

t = t.replace('your claude.ai account', 'your account').replace('claude.ai', 'your account').replace('Text &amp; Meaning','Ad Fontes').replace('Text & Meaning','Ad Fontes')
open(os.path.join(outdir, 'index.html'), 'w', encoding='utf-8').write(t)

# ---------- data files, flattened to the top level (easier to upload)
idx = json.load(open(os.path.join(site, 'index.json')))
for b in idx['books']:
    name = os.path.basename(b['file'])
    shutil.copy(os.path.join(site, b['file']), os.path.join(outdir, name))
    b['file'] = name
json.dump(idx, open(os.path.join(outdir, 'index.json'), 'w'))
shutil.copy(config_js, os.path.join(outdir, 'config.js'))

json.dump({"name": "Ad Fontes", "short_name": "Ad Fontes", "start_url": "./", "scope": "./", "display": "standalone",
           "background_color": "#F3F4F1", "theme_color": "#F3F4F1",
           "icons": [{"src": "icon-192.png", "sizes": "192x192", "type": "image/png"},
                     {"src": "icon-512.png", "sizes": "512x512", "type": "image/png"}]},
          open(os.path.join(outdir, 'manifest.json'), 'w'), indent=1)

open(os.path.join(outdir, 'sw.js'), 'w').write(r"""// Lets the reader open with no signal: keeps a copy of the app and the chapters you've opened.
const CACHE='adfontes-v2';
const SHELL=['./','index.html','config.js','index.json','manifest.json','icon-180.png','icon-192.png','icon-512.png'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(CACHE).then(c=>c.addAll(SHELL)).then(()=>self.skipWaiting()))});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim()))});
self.addEventListener('fetch',e=>{
  const u=new URL(e.request.url);
  if(e.request.method!=='GET')return;
  const mine=u.origin===location.origin, lib=u.hostname==='www.gstatic.com'&&u.pathname.startsWith('/firebasejs/'), font=/fonts\.(googleapis|gstatic)\.com$/.test(u.hostname);
  if(!(mine||lib||font))return;
  e.respondWith(fetch(e.request).then(r=>{if(r&&r.ok){const cp=r.clone();caches.open(CACHE).then(c=>c.put(e.request,cp))}return r}).catch(()=>caches.match(e.request).then(r=>r||caches.match('index.html'))));
});
""")

open(os.path.join(outdir, 'CREDITS.md'), 'w').write("""# Ad Fontes — data sources

- Hebrew text, morphology, glosses and brief lexicon: STEPBible.org TAHOT, TBESH and TEHMC, based on work at Tyndale House Cambridge (CC BY 4.0). Source: https://github.com/STEPBible/STEPBible-Data. Changes: reformatted into per-book JSON; occurrence counts computed from the full dataset.
- Septuagint: Rahlfs 1935 with CATSS morphology, prepared by Eliran Wong (CC BY-NC-SA 4.0). Source: https://github.com/eliranwong/LXX-Rahlfs-1935. Non-commercial use only; this derived data is shared under the same license.
- English: Berean Standard Bible, NHEB, KJV, ASV, YLT, Rotherham, JPS 1917, Douay-Rheims (Challoner), Geneva 1599 — all public domain, via https://github.com/scrollmapper/bible_databases.
- Study notes and Septuagint comparisons: written with Claude, labeled by type and confidence in the app.
""")
print('built', sorted(os.listdir(outdir)))
