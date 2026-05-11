import os
import re
import sys
import json
import shutil
import unicodedata
import urllib.request
from pathlib import Path
from flask import (Flask, render_template, request, redirect,
                   send_from_directory, abort, url_for, flash, jsonify)

# Quand l'app est bundlée par PyInstaller :
#   sys._MEIPASS  → dossier temporaire contenant templates/ et static/
#   sys.executable → chemin du .exe, donc dossier de l'exe = dossier de travail
if getattr(sys, 'frozen', False):
    BASE_DIR   = os.path.dirname(sys.executable)
    BUNDLE_DIR = sys._MEIPASS
else:
    BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
    BUNDLE_DIR = BASE_DIR

PATRONS_DIR = os.path.join(BASE_DIR, "patrons")

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}

# ── Correspondances cible ──────────────────────────────────────────────────

# Détection dans le nom d'un fichier
CIBLE_IN_FILE = [
    ('femme',   'Femme'),
    ('homme',   'Homme'),
    ('enfant',  'Enfant'),
    ('bébé',    'Bébé'),
    ('bebe',    'Bébé'),
]

# Normalisation de la cible issue du nom de dossier
CIBLE_META = {
    'femme':        'Femme',
    'homme':        'Homme',
    'enfant':       'Enfant',
    'bébé':         'Bébé',
    'bebe':         'Bébé',
    'mixte':        'Mixte',
    'famille':      'Famille',
    'pack famille': 'Famille',
}

CIBLES_FILTRE     = ['Femme', 'Homme', 'Enfant', 'Bébé', 'Mixte', 'Famille']
DIFFICULTES       = {1: 'Débutant', 2: 'Facile', 3: 'Intermédiaire', 4: 'Avancé', 5: 'Expert'}

# ── Utilitaires ────────────────────────────────────────────────────────────

def strip_copie(name: str) -> str:
    """Retire le préfixe 'Copie de ' (insensible à la casse)."""
    return re.sub(r'^copie\s+de\s+', '', name, flags=re.IGNORECASE).strip()


def normalize_meta_cible(raw: str) -> str:
    return CIBLE_META.get(raw.strip().lower(), raw.strip())


def detect_file_cible(name_lower: str) -> str | None:
    for kw, label in CIBLE_IN_FILE:
        if kw in name_lower:
            return label
    return None


def make_slug(name: str) -> str:
    """Produit un slug URL-safe stable depuis le nom de dossier."""
    nfkd = unicodedata.normalize('NFKD', name)
    ascii_str = nfkd.encode('ascii', 'ignore').decode('ascii')
    return re.sub(r'[^a-zA-Z0-9]+', '-', ascii_str).strip('-').lower()


def parse_folder_name(name: str) -> dict:
    """
    Extrait nom, description, marque, cible depuis un nom de dossier.
    Format attendu : NOM - description - MARQUE - CIBLE
    """
    parts = [p.strip() for p in name.split(' - ')]
    if len(parts) >= 4:
        nom         = parts[0]
        cible_raw   = parts[-1]
        marque      = parts[-2]
        description = ' - '.join(parts[1:-2])
    elif len(parts) == 3:
        nom, description, cible_raw = parts
        marque = ''
    elif len(parts) == 2:
        nom, cible_raw = parts
        description = marque = ''
    else:
        nom = name
        description = marque = cible_raw = ''

    return {
        'nom':         nom,
        'description': description,
        'marque':      marque,
        'cible':       normalize_meta_cible(cible_raw),
    }


# ── Scan d'un dossier patron ───────────────────────────────────────────────

def scan_patron_folder(folder_path: str, folder_name: str) -> dict | None:
    meta = parse_folder_name(folder_name)

    # fichiers[cible_label][type] = nom_de_fichier_original
    fichiers: dict[str, dict[str, str]] = {}
    tutoriel: str | None = None
    images:   list[str] = []

    try:
        entries = os.listdir(folder_path)
    except OSError:
        return None

    for entry in sorted(entries):
        if entry.startswith('.'):
            continue

        ext       = Path(entry).suffix.lower()
        norm      = strip_copie(entry)
        norm_low  = norm.lower()

        # ── Images patron (pas les assemblages) ──
        if ext in IMAGE_EXTENSIONS:
            if 'assemblage' not in norm_low:
                images.append(entry)
            continue

        if ext != '.pdf':
            continue

        # ── Tutoriel ──
        if 'tutoriel' in norm_low:
            tutoriel = entry
            continue

        # ── Assemblage (instructions collage A4) — ignoré ──
        if 'assemblage' in norm_low:
            continue

        # ── Type de fichier ──
        if 'projecteur' in norm_low:
            ftype = 'projecteur'
        elif 'imprimeur' in norm_low:
            ftype = 'imprimeur'
        elif '_a4' in norm_low:
            ftype = 'a4'
        else:
            continue  # fichier non reconnu

        # ── Cible du fichier ──
        cible = detect_file_cible(norm_low)
        if cible is None:
            # Pas de cible dans le nom : on utilise celle du dossier
            cible = meta['cible'] if meta['cible'] != 'Famille' else 'default'

        fichiers.setdefault(cible, {})[ftype] = entry

    cibles_dispo  = sorted(fichiers.keys())
    est_famille   = len(cibles_dispo) > 1 or meta['cible'] == 'Famille'

    # Lecture des infos complémentaires (patron.json)
    extra = read_patron_json(folder_path)

    return {
        'dossier':          folder_name,
        'slug':             make_slug(folder_name),
        'nom':              meta['nom'],
        'description':      meta['description'],
        'marque':           meta['marque'],
        'cible':            meta['cible'],
        'fichiers':         fichiers,
        'tutoriel':         tutoriel,
        'image':            images[0] if images else None,
        'cibles_dispo':     cibles_dispo,
        'est_famille':      est_famille,
        'url':              extra.get('url', ''),
        'notes':            extra.get('notes', ''),
        'difficulte':       int(extra['difficulte']) if str(extra.get('difficulte', '')).isdigit() else 0,
        'marque_url':       extra.get('marque_url', ''),
    }


# ── Lecture / écriture patron.json ────────────────────────────────────────

def read_patron_json(folder_path: str) -> dict:
    path = os.path.join(folder_path, 'patron.json')
    if os.path.isfile(path):
        try:
            with open(path, encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def write_patron_json(folder_path: str, data: dict) -> None:
    path = os.path.join(folder_path, 'patron.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ── Accès aux patrons ──────────────────────────────────────────────────────

def get_all_patrons() -> list[dict]:
    if not os.path.isdir(PATRONS_DIR):
        return []
    patrons = []
    for entry in os.listdir(PATRONS_DIR):
        fp = os.path.join(PATRONS_DIR, entry)
        if os.path.isdir(fp) and not entry.startswith('.'):
            p = scan_patron_folder(fp, entry)
            if p:
                patrons.append(p)
    return sorted(patrons, key=lambda p: p['nom'].lower())


def find_patron_by_slug(slug: str) -> dict | None:
    if not os.path.isdir(PATRONS_DIR):
        return None
    for entry in os.listdir(PATRONS_DIR):
        fp = os.path.join(PATRONS_DIR, entry)
        if os.path.isdir(fp) and not entry.startswith('.'):
            if make_slug(entry) == slug:
                return scan_patron_folder(fp, entry)
    return None

# ── Application Flask ──────────────────────────────────────────────────────

app = Flask(__name__,
            template_folder=os.path.join(BUNDLE_DIR, 'templates'),
            static_folder=os.path.join(BUNDLE_DIR, 'static'))
app.config['SECRET_KEY'] = 'ckilepatron-secret'
app.config['PATRONS_DIR'] = PATRONS_DIR

@app.context_processor
def inject_globals():
    ext_path = os.path.join(BASE_DIR, 'extension')
    return dict(ext_dossier=ext_path if os.path.isdir(ext_path) else None)


@app.route('/')
def index():
    tous    = get_all_patrons()
    marques = sorted({p['marque'] for p in tous if p['marque']})

    cible_filtre      = request.args.get('cible', '')
    marque_filtre     = request.args.get('marque', '')
    difficulte_filtre = request.args.get('difficulte', '')
    tutoriel_filtre   = request.args.get('tutoriel', '')
    recherche         = request.args.get('q', '').strip()

    patrons = tous

    # Filtre cible
    if cible_filtre == 'Famille':
        patrons = [p for p in patrons if p['est_famille']]
    elif cible_filtre:
        patrons = [p for p in patrons if
                   cible_filtre in p['cibles_dispo'] or
                   p['cible'].lower() == cible_filtre.lower()]

    # Filtre marque
    if marque_filtre:
        patrons = [p for p in patrons if p['marque'] == marque_filtre]

    # Filtre difficulté
    if difficulte_filtre and difficulte_filtre.isdigit():
        patrons = [p for p in patrons if p['difficulte'] == int(difficulte_filtre)]

    # Filtre tutoriel
    if tutoriel_filtre:
        patrons = [p for p in patrons if p['tutoriel']]

    # Recherche texte
    if recherche:
        rl = recherche.lower()
        patrons = [p for p in patrons if
                   rl in p['nom'].lower() or
                   rl in p['description'].lower() or
                   rl in p['marque'].lower()]

    return render_template('index.html',
                           patrons=patrons,
                           total=len(tous),
                           cibles=CIBLES_FILTRE,
                           marques=marques,
                           difficultes=DIFFICULTES,
                           cible_filtre=cible_filtre,
                           marque_filtre=marque_filtre,
                           difficulte_filtre=difficulte_filtre,
                           tutoriel_filtre=tutoriel_filtre,
                           recherche=recherche)
                           

@app.route('/patron/<slug>')
def detail(slug):
    patron = find_patron_by_slug(slug)
    if patron is None:
        abort(404)
    return render_template('detail.html', patron=patron)


@app.route('/patron/<slug>/fichier/<path:filename>')
def fichier(slug, filename):
    """Sert un fichier (PDF, image…) depuis le dossier d'un patron."""
    patron = find_patron_by_slug(slug)
    if patron is None:
        abort(404)

    folder_path = os.path.join(PATRONS_DIR, patron['dossier'])

    # Sécurité : pas de traversal de répertoire
    safe = os.path.realpath(os.path.join(folder_path, filename))
    real = os.path.realpath(folder_path)
    if not safe.startswith(real + os.sep):
        abort(403)

    return send_from_directory(folder_path, filename)


@app.route('/patron/<slug>/projeter/<cible>')
def projeter(slug, cible):
    """
    Ouvre le PDF projecteur pour la cible donnée dans le navigateur.
    Fallback vers une page image si pas de PDF projecteur.
    """
    patron = find_patron_by_slug(slug)
    if patron is None:
        abort(404)

    pdf = patron['fichiers'].get(cible, {}).get('projecteur')
    if pdf:
        # Redirige vers le fichier PDF → le navigateur l'affiche en plein écran
        return send_from_directory(
            os.path.join(PATRONS_DIR, patron['dossier']),
            pdf,
            mimetype='application/pdf'
        )
    # Fallback : page sombre avec image
    return render_template('projection.html', patron=patron, cible=cible)


@app.route('/patron/<slug>/difficulte', methods=['POST'])
def set_difficulte(slug):
    patron = find_patron_by_slug(slug)
    if patron is None:
        abort(404)
    folder_path = os.path.join(PATRONS_DIR, patron['dossier'])
    val = request.form.get('difficulte', '0')
    difficulte = int(val) if val.isdigit() else 0
    extra = read_patron_json(folder_path)
    extra['difficulte'] = difficulte
    write_patron_json(folder_path, extra)
    return ('', 204)


@app.route('/ajouter', methods=['GET', 'POST'])
def ajouter():
    if request.method == 'POST':
        nom         = request.form.get('nom', '').strip()
        description = request.form.get('description', '').strip()
        marque      = request.form.get('marque', '').strip()
        marque_url  = request.form.get('marque_url', '').strip()
        cible       = request.form.get('cible', '').strip()
        url         = request.form.get('url', '').strip()
        notes       = request.form.get('notes', '').strip()
        val         = request.form.get('difficulte', '0')
        difficulte  = int(val) if val.isdigit() else 0

        if not nom:
            flash('Le nom est obligatoire.', 'erreur')
            return redirect(url_for('ajouter'))

        parts = [nom]
        if description:
            parts.append(description)
        if marque:
            parts.append(marque)
        if cible:
            parts.append(cible)
        raw_name    = ' - '.join(parts)
        folder_name = re.sub(r'[/\\:*?"<>|]', '-', raw_name)
        folder_name = re.sub(r'\s*-\s*-\s*', ' - ', folder_name).strip()
        folder_path = os.path.join(PATRONS_DIR, folder_name)

        if os.path.isdir(folder_path):
            flash(f'Un patron « {folder_name} » existe déjà.', 'erreur')
            return redirect(url_for('ajouter'))

        os.makedirs(folder_path, exist_ok=True)
        write_patron_json(folder_path, {'url': url, 'notes': notes, 'difficulte': difficulte, 'marque_url': marque_url})

        # Image uploadée
        image = request.files.get('image')
        if image and image.filename:
            ext = Path(image.filename).suffix.lower()
            if ext not in IMAGE_EXTENSIONS:
                ext = '.jpg'
            image.save(os.path.join(folder_path, f'cover{ext}'))

        flash(f'Patron « {nom} » créé.', 'succes')
        return redirect(url_for('detail', slug=make_slug(folder_name)))

    return render_template('ajouter.html', cibles=CIBLES_FILTRE)


@app.route('/patron/<slug>/supprimer', methods=['POST'])
def supprimer(slug):
    patron = find_patron_by_slug(slug)
    if patron is None:
        abort(404)
    folder_path = os.path.join(PATRONS_DIR, patron['dossier'])
    shutil.rmtree(folder_path)
    flash(f'« {patron["nom"]} » a été supprimé.', 'succes')
    return redirect(url_for('index'))


@app.route('/patron/<slug>/modifier', methods=['GET', 'POST'])
def modifier(slug):
    patron = find_patron_by_slug(slug)
    if patron is None:
        abort(404)

    folder_path = os.path.join(PATRONS_DIR, patron['dossier'])

    if request.method == 'POST':
        nom         = request.form.get('nom', '').strip()
        description = request.form.get('description', '').strip()
        marque      = request.form.get('marque', '').strip()
        marque_url  = request.form.get('marque_url', '').strip()
        cible       = request.form.get('cible', '').strip()
        url         = request.form.get('url', '').strip()
        notes       = request.form.get('notes', '').strip()
        val         = request.form.get('difficulte', '0')
        difficulte  = int(val) if val.isdigit() else 0

        if not nom:
            flash('Le nom est obligatoire.', 'erreur')
            return redirect(url_for('modifier', slug=slug))

        # Reconstruire le nom de dossier depuis tous les champs
        parts = [nom]
        if description:
            parts.append(description)
        if marque:
            parts.append(marque)
        if cible:
            parts.append(cible)
        raw_name = ' - '.join(parts)
        new_name = re.sub(r'[/\\:*?"<>|]', '-', raw_name)
        new_name = re.sub(r'\s*-\s*-\s*', ' - ', new_name).strip()
        new_path = os.path.join(PATRONS_DIR, new_name)

        # Renommer le dossier si nécessaire
        if new_name != patron['dossier']:
            if os.path.isdir(new_path):
                flash(f'Un patron « {new_name} » existe déjà.', 'erreur')
                return redirect(url_for('modifier', slug=slug))
            os.rename(folder_path, new_path)
            folder_path = new_path

        # Image uploadée (remplacement optionnel)
        image = request.files.get('image')
        if image and image.filename:
            ext = Path(image.filename).suffix.lower()
            if ext not in IMAGE_EXTENSIONS:
                ext = '.jpg'
            image.save(os.path.join(folder_path, f'cover{ext}'))

        extra = read_patron_json(folder_path)
        extra.update({'url': url, 'notes': notes, 'difficulte': difficulte, 'marque_url': marque_url})
        write_patron_json(folder_path, extra)
        flash('Informations enregistrées.', 'succes')
        return redirect(url_for('detail', slug=make_slug(new_name)))

    return render_template('modifier.html', patron=patron, cibles=CIBLES_FILTRE)


# ── API ───────────────────────────────────────────────────────────────────────

@app.after_request
def add_cors(response):
    if request.path.startswith('/api/'):
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
    return response


@app.route('/api/importer', methods=['POST', 'OPTIONS'])
def api_importer():
    if request.method == 'OPTIONS':
        return ('', 204)

    data = request.get_json(silent=True) or {}
    nom         = data.get('nom', '').strip()
    description = data.get('description', '').strip()
    marque      = data.get('marque', '').strip()
    marque_url  = data.get('marque_url', '').strip()
    cible       = data.get('cible', '').strip()
    url         = data.get('url', '').strip()
    difficulte  = int(data['difficulte']) if str(data.get('difficulte', '')).isdigit() else 0
    image_url   = data.get('image_url', '').strip()

    if not nom:
        return jsonify({'status': 'error', 'message': 'Nom manquant'}), 400

    # Construire le nom de dossier : NOM - description - MARQUE - CIBLE
    parts = [nom]
    if description:
        parts.append(description)
    if marque:
        parts.append(marque)
    if cible:
        parts.append(cible)

    # Nettoyer les caractères interdits dans un nom de dossier
    # (/ et \ créent des sous-dossiers involontaires sur Linux/Windows)
    raw_name = ' - '.join(parts)
    folder_name = re.sub(r'[/\\:*?"<>|]', '-', raw_name)
    folder_name = re.sub(r'\s*-\s*-\s*', ' - ', folder_name).strip()  # tirets doublés
    folder_path = os.path.join(PATRONS_DIR, folder_name)

    if os.path.isdir(folder_path):
        slug = make_slug(folder_name)
        return jsonify({'status': 'exists', 'slug': slug, 'dossier': folder_name})

    os.makedirs(folder_path, exist_ok=True)
    write_patron_json(folder_path, {'url': url, 'notes': '', 'difficulte': difficulte, 'marque_url': marque_url})

    # Télécharger l'image de couverture
    if image_url:
        try:
            from urllib.parse import urlparse
            ext = os.path.splitext(urlparse(image_url).path)[1].lower()
            if ext not in IMAGE_EXTENSIONS:
                ext = '.jpg'
            img_path = os.path.join(folder_path, f'cover{ext}')
            req = urllib.request.Request(
                image_url,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                with open(img_path, 'wb') as f:
                    f.write(resp.read())
        except Exception:
            pass  # Image non critique, on continue

    slug = make_slug(folder_name)
    return jsonify({'status': 'ok', 'slug': slug, 'dossier': folder_name})


if __name__ == '__main__':
    os.makedirs(PATRONS_DIR, exist_ok=True)
    app.run(debug=True)
