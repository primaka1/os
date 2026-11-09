// Potrebno da se stranica može dodati na početni zaslon kao aplikacija.
// Ništa ne sprema – sve se uvijek učitava svježe s interneta.
self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", e => e.waitUntil(self.clients.claim()));
self.addEventListener("fetch", () => {});
