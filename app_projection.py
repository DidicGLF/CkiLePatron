"""
Module optionnel — Projection de patrons via PyMuPDF.
Pour désactiver : commenter la ligne `app.register_blueprint(proj_bp)` dans app.py
"""
import io
import json
import os
import re
from flask import Blueprint, render_template, jsonify, abort, request

try:
    import fitz
    FITZ_DISPONIBLE = True
except ImportError:
    FITZ_DISPONIBLE = False

proj_bp = Blueprint('projection', __name__)


def _planche_path(slug, cible):
    """Retourne (patron, chemin_absolu_planche_json) ou (None, None)."""
    from app import find_patron_by_slug, PATRONS_DIR
    patron = find_patron_by_slug(slug)
    if not patron:
        return None, None
    cible_safe = re.sub(r'[^a-zA-Z0-9_-]', '_', cible)
    path = os.path.join(PATRONS_DIR, patron['dossier'], f'planche_{cible_safe}.json')
    return patron, path


def _get_pdf_path(slug, cible):
    """Retourne (patron, chemin_absolu_pdf) ou (None, None)."""
    from app import find_patron_by_slug, PATRONS_DIR
    patron = find_patron_by_slug(slug)
    if not patron:
        return None, None
    pdf_name = patron['fichiers'].get(cible, {}).get('projecteur')
    if not pdf_name:
        return None, None
    pdf_path = os.path.join(PATRONS_DIR, patron['dossier'], pdf_name)
    return patron, pdf_path


def _apply_layers(doc, active):
    """Applique les calques OCG actifs et retourne un nouveau doc."""
    ocgs = doc.get_ocgs()
    if not ocgs or not active:
        return doc
    on_set  = {int(x) for x in active.split(',') if x.strip()}
    all_set = set(ocgs.keys())
    off_set = all_set - on_set
    doc.set_layer(-1, on=list(on_set), off=list(off_set))
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    doc.close()
    return fitz.open(stream=buf, filetype='pdf')


# ── PAGE PRINCIPALE ─────────────────────────────────────────────────────────

@proj_bp.route('/patron/<slug>/projection/<cible>')
def page_projection(slug, cible):
    if not FITZ_DISPONIBLE:
        abort(503)
    from app import find_patron_by_slug
    patron = find_patron_by_slug(slug)
    if not patron:
        abort(404)
    return render_template('projection_app.html',
                           slug=slug,
                           cible=cible,
                           patron_nom=patron['nom'])


# ── API ──────────────────────────────────────────────────────────────────────

@proj_bp.route('/patron/<slug>/projection/<cible>/analyse')
def analyse(slug, cible):
    if not FITZ_DISPONIBLE:
        return jsonify({'error': 'PyMuPDF non disponible'}), 503
    patron, pdf_path = _get_pdf_path(slug, cible)
    if not pdf_path or not os.path.exists(pdf_path):
        return jsonify({'error': 'Fichier introuvable'}), 404

    doc  = fitz.open(pdf_path)
    page = doc[0]
    ocgs = doc.get_ocgs()

    sizes, extras = [], []
    for xref, info in ocgs.items():
        n = info['name']
        entry = {'name': n, 'xref': xref, 'on': info['on']}
        if n.isdigit():
            sizes.append(entry)
        else:
            extras.append(entry)
    sizes.sort(key=lambda x: int(x['name']))

    result = {
        'page_w_pts': page.rect.width,
        'page_h_pts': page.rect.height,
        'page_w_cm':  round(page.rect.width  / 28.35, 1),
        'page_h_cm':  round(page.rect.height / 28.35, 1),
        'sizes':      sizes,
        'extras':     extras,
        'has_layers': len(ocgs) > 0,
    }
    doc.close()
    return jsonify(result)


@proj_bp.route('/patron/<slug>/projection/<cible>/svg')
def svg(slug, cible):
    if not FITZ_DISPONIBLE:
        return jsonify({'error': 'PyMuPDF non disponible'}), 503
    patron, pdf_path = _get_pdf_path(slug, cible)
    if not pdf_path or not os.path.exists(pdf_path):
        return jsonify({'error': 'Fichier introuvable'}), 404

    active = request.args.get('layers', '')
    doc    = fitz.open(pdf_path)
    doc    = _apply_layers(doc, active)
    page   = doc[0]

    svg_data = page.get_svg_image()
    result = {
        'svg':        svg_data,
        'page_w_pts': page.rect.width,
        'page_h_pts': page.rect.height,
        'page_w_cm':  round(page.rect.width  / 28.35, 1),
        'page_h_cm':  round(page.rect.height / 28.35, 1),
    }
    doc.close()
    return jsonify(result)


@proj_bp.route('/patron/<slug>/projection/<cible>/planche', methods=['GET'])
def get_planche(slug, cible):
    patron, path = _planche_path(slug, cible)
    if not patron:
        abort(404)
    if not os.path.isfile(path):
        abort(404)
    try:
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data)
    except Exception:
        abort(500)


@proj_bp.route('/patron/<slug>/projection/<cible>/planche', methods=['POST'])
def save_planche(slug, cible):
    patron, path = _planche_path(slug, cible)
    if not patron:
        abort(404)
    data = request.get_json(silent=True)
    if not data:
        abort(400)
    data['cible'] = cible
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return jsonify({'status': 'ok'})
    except Exception:
        abort(500)


@proj_bp.route('/patron/<slug>/projection/<cible>/texts')
def texts(slug, cible):
    if not FITZ_DISPONIBLE:
        return jsonify({'error': 'PyMuPDF non disponible'}), 503
    patron, pdf_path = _get_pdf_path(slug, cible)
    if not pdf_path or not os.path.exists(pdf_path):
        return jsonify({'error': 'Fichier introuvable'}), 404

    active = request.args.get('layers', '')
    doc    = fitz.open(pdf_path)
    doc    = _apply_layers(doc, active)
    page   = doc[0]

    blocks = page.get_text('dict')['blocks']
    doc.close()

    EXCLUDE = {'kaki le pantalon chino', 'www.klafoutis.com', 'en thermo',
               'en tp', '1x', '32', '34', '36', '38', '40', '42',
               '44', '46', '48', '50', '52'}
    texts_list = []
    for b in blocks:
        if b['type'] != 0:
            continue
        for line in b['lines']:
            for span in line['spans']:
                t = span['text'].strip()
                if not t or len(t) < 3:
                    continue
                if t.lower() in EXCLUDE:
                    continue
                if any(kw in t.lower() for kw in [
                        'klafoutis', 'couture', 'tailles', 'marges', 'ourlets',
                        'symboles', 'niveau', 'bienveillante', 'familiale',
                        'carré', 'impression', '@', 'www']):
                    continue
                x0, y0, x1, y1 = span['bbox']
                texts_list.append({
                    'text': t,
                    'x':    round((x0 + x1) / 2),
                    'y':    round((y0 + y1) / 2),
                })

    return jsonify({'texts': texts_list})
