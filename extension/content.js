chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg.type === 'EXTRACT') {
    sendResponse(extractPatron());
  }
  return true; // réponse asynchrone possible
});

function extractPatron() {
  // ── Titre ────────────────────────────────────────────────────────────────
  const h1 = document.querySelector('h1');
  const titre = h1 ? h1.textContent.trim() : '';

  // Mots-clés cibles Klafoutis — toujours en MAJUSCULES dans le titre
  // Ordre important : PACK FAMILLE avant FAMILLE pour éviter la correspondance partielle
  const CIBLES = ['PACK FAMILLE', 'FAMILLE', 'FEMME', 'HOMME', 'ENFANT', 'BÉBÉ', 'BEBE', 'MIXTE'];

  function detectCible(str) {
    for (const c of CIBLES) {
      if (str.includes(c)) return c;
    }
    return '';
  }

  const parts = titre.split(' - ').map(s => s.trim()).filter(Boolean);
  const nom   = parts[0] || '';
  const cible = detectCible(titre);

  // Description = tout ce qui est entre le nom et la cible,
  // en retirant le dernier segment s'il contient la cible (ex: "version FEMME")
  let descParts = parts.slice(1);
  if (cible && descParts.length > 0 && descParts[descParts.length - 1].includes(cible)) {
    descParts = descParts.slice(0, -1);
  }
  const description = descParts.join(' - ');

  // ── Difficulté ───────────────────────────────────────────────────────────
  let difficulte = 0;
  const m = document.body.innerText.match(/(\d)\s*\/\s*5/);
  if (m) difficulte = parseInt(m[1], 10);

  // ── Images produit ───────────────────────────────────────────────────────
  const seen = new Set();
  const images = [];

  // Extrait la meilleure URL disponible depuis un élément img
  function getSrc(img) {
    // Priorité : src réel > data-src > data-srcset (1er URL) > srcset (1er URL)
    const candidates = [
      img.src,
      img.dataset.src,
      img.dataset.lazySrc,
      img.dataset.originalSrc,
    ];
    for (const c of candidates) {
      if (c && !c.startsWith('data:') && c.length > 10) return c;
    }
    // Extraire la première URL du srcset
    const srcset = img.srcset || img.dataset.srcset || '';
    if (srcset) {
      const first = srcset.trim().split(/[\s,]+/)[0];
      if (first && !first.startsWith('data:')) return first;
    }
    return null;
  }

  // Convertit n'importe quelle URL image Shopify en version 1024px
  function toHD(src) {
    return src
      .replace(/_([\d]+x[\d]*)\.(jpg|jpeg|png|webp)/i, '_1024x.$2')
      .replace(/\?.*$/, '');
  }

  function isCDN(src) {
    return src.includes('cdn/shop') ||
           src.includes('cdn.shopify.com') ||
           src.includes('klafoutis');
  }

  function addImg(src) {
    // Normaliser les URLs protocol-relative ("//...")
    if (src.startsWith('//')) src = 'https:' + src;
    if (seen.has(src) || !isCDN(src)) return;
    seen.add(src);
    images.push({ thumb: src, full: toHD(src) });
  }

  // 1. Chercher dans les attributs data- (lazy loading)
  document.querySelectorAll('img[data-src], img[data-lazy-src], img[data-original-src]')
    .forEach(img => { const s = getSrc(img); if (s) addImg(s); });

  // 2. Images déjà chargées dans la galerie produit
  const galSelectors = [
    '.product__media img',
    '.product-media-container img',
    '[data-media-id] img',
    '.product__photo img',
    '[id^="media"] img',
    'img[src*="cdn/shop/files"]',
    'img[src*="cdn/shop/products"]',
  ];
  galSelectors.forEach(sel => {
    document.querySelectorAll(sel).forEach(img => {
      const s = getSrc(img); if (s) addImg(s);
    });
  });

  // 3. Fallback : toutes les imgs CDN de la page
  if (images.length === 0) {
    document.querySelectorAll('img').forEach(img => {
      const s = getSrc(img); if (s) addImg(s);
    });
  }

  return {
    titre,
    nom,
    description,
    marque: 'KLAFOUTIS',
    cible,
    difficulte,
    url: window.location.href,
    images: images.slice(0, 30),
  };
}
