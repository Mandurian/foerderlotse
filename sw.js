// Förderlotse Service Worker: App-Hülle offline, Daten zuerst frisch aus dem Netz.
const CACHE = "foerderlotse-v3";
const SHELL = ["./", "index.html", "manifest.webmanifest", "icons/icon.svg", "icons/icon-192.png", "icons/icon-512.png",
               "data/programme.json", "data/antragshilfe.json", "data/meta.json"];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});
self.addEventListener("fetch", e => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET" || url.origin !== location.origin) return;
  const istDaten = url.pathname.includes("/data/") || e.request.mode === "navigate";
  if (istDaten) {
    // Netzwerk zuerst, damit die wöchentlichen Updates ankommen; offline aus dem Cache
    e.respondWith(fetch(e.request).then(r => {
      const kopie = r.clone(); caches.open(CACHE).then(c => c.put(e.request, kopie)); return r;
    }).catch(() => caches.match(e.request).then(r => r || caches.match("index.html"))));
  } else {
    e.respondWith(caches.match(e.request).then(r => r || fetch(e.request)));
  }
});
