import os
import zipfile

# 1. Crear directorios
directories = [
    ".vscode",
    ".github/workflows",
    "cls",
    "assets/figures"
]

for d in directories:
    os.makedirs(d, exist_ok=True)

# 2. Definir contenido de los archivos
files = {
    ".gitignore": """*.aux
*.bbl
*.blg
*.log
*.out
*.toc
*.synctex.gz
*.fls
*.fdb_latexmk
*.nav
*.snm
*.vrb
*.dvi
*.bcf
*.run.xml
*.lot
*.lof
.DS_Store
Thumbs.db
""",

    "README.md": """# Plantilla LaTeX - Revista INGENIO (UFPS)
Plantilla lista para VSCode y GitHub Actions configurada bajo la normativa editorial de la Revista Ingenio UFPS.
""",

    ".vscode/settings.json": """{
  "latex-workshop.latex.autoBuild.run": "onFileChange",
  "latex-workshop.latex.recipes": [
    {
      "name": "pdflatex -> bibtex -> pdflatex x2",
      "tools": ["pdflatex", "bibtex", "pdflatex", "pdflatex"]
    }
  ],
  "latex-workshop.latex.tools": [
    {
      "name": "pdflatex",
      "command": "pdflatex",
      "args": ["-synctex=1", "-interaction=nonstopmode", "-file-line-error", "%DOC%"]
    },
    {
      "name": "bibtex",
      "command": "bibtex",
      "args": ["%DOCFILE%"]
    }
  ],
  "latex-workshop.view.pdf.viewer": "tab",
  "latex-workshop.latex.clean.subfolder.enabled": true
}
""",

    ".github/workflows/compile.yml": """name: Compilar Articulo Ingenio UFPS
on:
  push:
    branches: [ "main", "master" ]
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: xu-cheng/latex-action@v3
        with:
          root_file: main.tex
          args: -pdf -file-line-error -halt-on-error -interaction=nonstopmode
      - uses: actions/upload-artifact@v4
        with:
          name: Articulo-Ingenio-UFPS
          path: main.pdf
"""
}

# Escribir archivos
for path, content in files.items():
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

print("Estructura de plantilla generada con éxito.")

# 3. Empaquetar todo en un archivo .ZIP
zip_name = "plantilla_ingenio_ufps.zip"
with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for root, _, filenames in os.walk("."):
        if ".git" in root or "__pycache__" in root or zip_name in root:
            continue
        for file in filenames:
            if file == zip_name or file == os.path.basename(__file__):
                continue
            full_path = os.path.join(root, file)
            zipf.write(full_path, arcname=os.path.relpath(full_path, "."))

print(f"Archivo empaquetado correctamente: {zip_name}")