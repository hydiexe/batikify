const CACHE_NAME = 'batik-cache-v2'; // Versi cache diperbarui untuk memicu 'activate'
// Hanya cache aset lokal. Browser akan menangani caching untuk sumber eksternal.
const urlsToCache = [
  '/app',
  '/static/canting.svg',
  '/static/icons/icon-192x192.png',
  '/static/icons/icon-512x512.png'
];

// Event 'install': Cache file-file penting.
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Opened cache and caching core assets');
        return cache.addAll(urlsToCache);
      })
  );
  self.skipWaiting(); // Paksa service worker baru untuk aktif
});

// Event 'fetch': Menyajikan konten dari cache, lalu network sebagai fallback.
self.addEventListener('fetch', event => {
  // Abaikan permintaan yang bukan GET
  if (event.request.method !== 'GET') {
    return;
  }

  event.respondWith(
    caches.match(event.request)
      .then(cachedResponse => {
        // Jika ada di cache, kembalikan dari cache
        if (cachedResponse) {
          return cachedResponse;
        }

        // Jika tidak, ambil dari network, lalu simpan ke cache untuk penggunaan selanjutnya
        return fetch(event.request).then(
          networkResponse => {
            // Periksa apakah kita menerima respons yang valid
            if(!networkResponse || networkResponse.status !== 200 || networkResponse.type !== 'basic') {
              return networkResponse;
            }
            
            // Gandakan respons karena kita perlu menggunakannya untuk cache dan browser
            const responseToCache = networkResponse.clone();

            caches.open(CACHE_NAME)
              .then(cache => {
                cache.put(event.request, responseToCache);
              });

            return networkResponse;
          }
        );
      })
  );
});


// Event 'activate': Membersihkan cache lama.
self.addEventListener('activate', event => {
  const cacheWhitelist = [CACHE_NAME];
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheWhitelist.indexOf(cacheName) === -1) {
            console.log('Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  return self.clients.claim(); // Ambil alih kontrol halaman dengan cepat
});
