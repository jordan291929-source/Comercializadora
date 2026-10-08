// Comercializadora Viviana: la app abre sin internet.
// Lo propio va primero a la red (así cada publicación se ve al instante) y, si no hay señal, sale de la copia guardada.
// Las librerías externas tienen versión fija en la URL: se sirven de la copia guardada.
const CACHE='cv-app-v1';
const SHELL=['/','/__/firebase/init.json','/manifest.webmanifest','/icons/logo-mark.png','/icons/icon-192.png','/icons/yape.png','/icons/plin.png',
  '/fonts/inter-latin-400-normal.woff2','/fonts/inter-latin-500-normal.woff2','/fonts/inter-latin-600-normal.woff2','/fonts/inter-latin-700-normal.woff2',
  'https://www.gstatic.com/firebasejs/10.12.2/firebase-app-compat.js','https://www.gstatic.com/firebasejs/10.12.2/firebase-auth-compat.js',
  'https://www.gstatic.com/firebasejs/10.12.2/firebase-database-compat.js','https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(CACHE).then(c=>Promise.all(SHELL.map(u=>c.add(new Request(u,u.startsWith('http')?{mode:'no-cors'}:{})).catch(()=>{})))).then(()=>self.skipWaiting()));});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim()));});
self.addEventListener('fetch',e=>{
  const req=e.request,url=new URL(req.url);
  if(req.method!=='GET')return;
  const libs=url.hostname==='www.gstatic.com'&&url.pathname.startsWith('/firebasejs/')||url.hostname==='cdnjs.cloudflare.com';
  if(libs){e.respondWith(caches.match(req,{ignoreVary:true}).then(hit=>hit||fetch(req).then(res=>{const copy=res.clone();caches.open(CACHE).then(c=>c.put(req,copy));return res;})));return;}
  if(url.origin!==location.origin)return;
  if(url.pathname.startsWith('/__/auth/'))return;
  const isPage=req.mode==='navigate';
  e.respondWith(fetch(req).then(res=>{if(res.ok){const copy=res.clone();caches.open(CACHE).then(c=>c.put(isPage?'/':req,copy));}return res;})
    .catch(()=>caches.match(isPage?'/':req,{ignoreSearch:isPage}).then(hit=>hit||Response.error())));
});
