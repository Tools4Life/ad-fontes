// Lets the reader open with no signal: keeps a copy of the app and the chapters you've opened.
const CACHE='adfontes-v4';
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
