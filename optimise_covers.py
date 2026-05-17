"""
Script one-shot : optimise tous les covers existants dans patrons/
Lancer avec : python optimise_covers.py
"""

import os
from pathlib import Path
from PIL import Image

PATRONS_DIR = Path(__file__).parent / 'patrons'
EXTENSIONS  = {'.jpg', '.jpeg', '.png', '.webp'}


COVER_MAX_PX = 900

def optimise(path: Path) -> int:
    import io
    original_size = path.stat().st_size
    img = Image.open(path)
    fmt = img.format
    resized = img.width > COVER_MAX_PX
    if resized:
        ratio = COVER_MAX_PX / img.width
        img = img.resize((COVER_MAX_PX, round(img.height * ratio)), Image.LANCZOS)
    kwargs = {'optimize': True, 'format': fmt}
    if fmt == 'JPEG':
        kwargs['quality'] = 85 if resized else 'keep'
    buf = io.BytesIO()
    img.save(buf, **kwargs)
    if buf.tell() < original_size:
        path.write_bytes(buf.getvalue())
        return buf.tell()
    return original_size


avant = {}
covers = [p for p in PATRONS_DIR.rglob('*') if p.is_file() and p.suffix.lower() in EXTENSIONS]

if not covers:
    print("Aucun cover trouvé.")
else:
    for p in covers:
        avant[p] = p.stat().st_size

    print(f"{len(covers)} image(s) trouvée(s)\n")
    total_avant = total_apres = 0

    for p in covers:
        a = avant[p]
        try:
            b = optimise(p)
            gain = a - b
            pct  = gain / a * 100 if a else 0
            total_avant += a
            total_apres += b
            nom = p.parent.name
            print(f"  {'✓':2}  {nom[:55]:<55}  {a/1024:6.1f} Ko → {b/1024:6.1f} Ko  ({pct:+.1f}%)")
        except Exception as e:
            print(f"  {'✗':2}  {p.parent.name}  — erreur : {e}")

    print()
    gain_total = total_avant - total_apres
    pct_total  = gain_total / total_avant * 100 if total_avant else 0
    print(f"Total : {total_avant/1024:.1f} Ko → {total_apres/1024:.1f} Ko  (−{gain_total/1024:.1f} Ko, {pct_total:.1f}%)")
