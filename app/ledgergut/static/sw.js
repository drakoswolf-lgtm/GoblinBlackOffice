/* Goblin Black Office service worker — cache only an explicit static allowlist.
   Receipt pages, CSV exports, auth responses, and API routes are NEVER cached. */
const CACHE = 'gbo-v2';

/* Only non-sensitive shell assets are pre-cached and served from cache when offline.
   No dynamic pages, no receipt data, no auth-protected routes. */
const STATIC_ALLOWLIST = [
  '/manifest.json',
  '/static/black-office.css',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png',
];

self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(STATIC_ALLOWLIST)));
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
  );
  self.clients.claim();
});

self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);
  if (
    event.request.method !== 'GET' ||
    url.origin !== self.location.origin ||
    !STATIC_ALLOWLIST.includes(url.pathname)
  ) {
    return;
  }
  event.respondWith(caches.match(event.request).then(cached => cached || fetch(event.request)));
});
