#!/usr/bin/env bash
set -e

DEST="CkiLePatron-distribution.zip"
TMP=$(mktemp -d)

echo "Création du ZIP de distribution..."

# Copier les fichiers nécessaires
for item in app.py requirements.txt installer.bat lancer.pyw templates LISEZMOI.txt; do
    cp -r "$item" "$TMP/"
done

# static : sans uploads/
cp -r static "$TMP/static"
rm -rf "$TMP/static/uploads"

# extension : sans les fichiers de dev
cp -r extension "$TMP/extension"
rm -f "$TMP/extension/generate_icon.html"

# Dossier patrons vide
mkdir "$TMP/patrons"

# Créer le zip
rm -f "$DEST"
(cd "$TMP" && zip -r - .) > "$DEST"

rm -rf "$TMP"

echo "✓ Distribution prête : $DEST"
