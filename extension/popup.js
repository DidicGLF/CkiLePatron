const APP_URL = 'http://127.0.0.1:5000';

let selectedImageUrl = null;
let currentDifficulte = 0;

// ── Init ──────────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

  const surKlafoutis = tab.url && tab.url.includes('klafoutis.com') &&
                       tab.url.includes('/products/');

  if (!surKlafoutis) {
    show('page-erreur');
    return;
  }

  try {
    await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      files: ['content.js'],
    });
  } catch (_) { /* déjà injecté */ }

  let data;
  try {
    data = await chrome.tabs.sendMessage(tab.id, { type: 'EXTRACT' });
  } catch (e) {
    afficherErreur('Impossible de lire la page. Rechargez-la et réessayez.');
    return;
  }

  renderForm(data);
  show('page-patron');
});

// ── Rendu du formulaire ───────────────────────────────────────────────────────

function renderForm(data) {
  document.getElementById('f-nom').value         = data.nom         || '';
  document.getElementById('f-description').value = data.description || '';
  document.getElementById('f-marque').value      = data.marque      || '';
  document.getElementById('f-cible').value       = data.cible       || '';

  setDifficulte(data.difficulte || 0);
  renderImages(data.images || []);

  document.getElementById('btn-ajouter').addEventListener('click', onAjouter);
}

// ── Étoiles ───────────────────────────────────────────────────────────────────

function setDifficulte(val) {
  currentDifficulte = val;
  document.querySelectorAll('.spool').forEach(s => {
    s.classList.toggle('is-on', parseInt(s.dataset.v, 10) <= val);
  });
}

document.querySelectorAll('.spool').forEach(spool => {
  spool.addEventListener('click', () => setDifficulte(parseInt(spool.dataset.v, 10)));
});

// ── Grille d'images ───────────────────────────────────────────────────────────

function renderImages(images) {
  const grid   = document.getElementById('image-grid');
  const apercu = document.getElementById('apercu');

  if (images.length === 0) {
    grid.innerHTML = '<span style="color:#666;font-size:12px">Aucune image détectée</span>';
    return;
  }

  function selectImage(full, thumb) {
    selectedImageUrl = full;
    apercu.innerHTML = '';
    const img = document.createElement('img');
    img.src = thumb;
    apercu.appendChild(img);
  }

  images.forEach(({ thumb, full }, i) => {
    const div = document.createElement('div');
    div.className = 'img-choice';

    const img = document.createElement('img');
    img.src = thumb;
    img.alt = '';
    img.loading = 'lazy';

    div.appendChild(img);
    div.addEventListener('click', () => {
      document.querySelectorAll('.img-choice').forEach(d => d.classList.remove('selected'));
      div.classList.add('selected');
      selectImage(full, thumb);
    });

    grid.appendChild(div);

    if (i === 0) {
      div.classList.add('selected');
      selectImage(full, thumb);
    }
  });
}

// ── Envoi vers Flask ──────────────────────────────────────────────────────────

async function onAjouter() {
  const btn = document.getElementById('btn-ajouter');
  btn.disabled = true;
  btn.textContent = 'Envoi…';
  clearStatus();

  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

  const payload = {
    nom:         document.getElementById('f-nom').value.trim(),
    description: document.getElementById('f-description').value.trim(),
    marque:      document.getElementById('f-marque').value.trim(),
    marque_url:  'https://klafoutis.com',
    cible:       document.getElementById('f-cible').value.trim(),
    difficulte:  currentDifficulte,
    url:         tab.url,
    image_url:   selectedImageUrl || '',
  };

  if (!payload.nom) {
    afficherErreur('Le nom est obligatoire.');
    btn.disabled = false;
    btn.textContent = 'Ajouter à CkiLePatron';
    return;
  }

  try {
    const resp = await fetch(`${APP_URL}/api/importer`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const result = await resp.json();

    if (result.status === 'ok') {
      afficherOk(`Patron créé : ${result.dossier}`);
      chrome.runtime.sendMessage({ type: 'RELOAD_APP' });
    } else if (result.status === 'exists') {
      afficherWarn(`Ce patron existe déjà (${result.dossier})`);
    } else {
      afficherErreur(result.message || 'Erreur inconnue');
    }
  } catch (e) {
    afficherErreur("CkiLePatron ne répond pas — vérifiez que l'appli est lancée.");
  }

  btn.disabled = false;
  btn.textContent = 'Ajouter à CkiLePatron';
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function show(id) {
  document.getElementById(id).style.display = '';
}

function clearStatus() {
  const s = document.getElementById('status');
  s.className = '';
  s.style.display = 'none';
  s.textContent = '';
}

function afficherOk(msg) {
  const s = document.getElementById('status');
  s.className = 'ok';
  s.textContent = '✓ ' + msg;
}

function afficherErreur(msg) {
  const s = document.getElementById('status');
  s.className = 'err';
  s.textContent = '✗ ' + msg;
  show('page-patron');
}

function afficherWarn(msg) {
  const s = document.getElementById('status');
  s.className = 'warn';
  s.textContent = '⚠ ' + msg;
}
