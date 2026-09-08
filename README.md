# Plantilla LaTeX - Revista INGENIO (UFPS)

Plantilla oficial en LaTeX para artículos de investigación y revisión adaptada a las directrices de la **Revista Ingenio** de la Universidad Francisco de Paula Santander (UFPS).

## Requisitos y Configuración Rápida en VS Code

1. **Instalar Visual Studio Code**.
2. **Instalar paquetes necesarios para LaTeX**:
- Arch y derivados: 
```bash
sudo pacman -Syu --needed \
texlive-basic \
texlive-latex \
texlive-latexrecommended \
texlive-latexextra \
texlive-fontsrecommended \
texlive-fontsextra \
texlive-plaingeneric \
texlive-pictures \
texlive-langspanish \
texlive-publishers \
texlive-bibtexextra \
python
```
- Ubuntu/Debian:
```bash
sudo apt update && sudo apt install -y \
texlive-latex-base \
texlive-latex-recommended \
texlive-latex-extra \
texlive-fonts-recommended \
texlive-fonts-extra \
texlive-plain-generic \
texlive-pictures \
texlive-lang-spanish \
texlive-publishers \
texlive-bibtex-extra \
python3
```
- Fedora:
```bash
sudo dnf install -y \
texlive-scheme-medium \
texlive-newtx \
texlive-binhex \
texlive-babel-spanish \
texlive-ieeetran \
texlive-pgf \
texlive-titlesec \
texlive-caption \
texlive-fancyhdr \
texlive-booktabs \
texlive-microtype \
python3
```
3. **Instalar las siguientes extensiones en VS Code**:
   - `James-Yu.latex-workshop` (LaTeX Workshop) (esta en el marketplace oficial de vscode, no en openvsx, por si se usa VSCodium u otros forks de VSCode).
4. **Abrir la carpeta del proyecto en VS Code**:
   - Al editar `main.tex` y guardar (`Ctrl + S`), el PDF se compilará automáticamente.
   - Presiona `Ctrl + Alt + V` para abrir el visor de PDF integrado en una pestaña lateral.
   - También se puede ver en una pestaña de la barra lateral a la izquierda con el panel de la extensión.

## Automatización en GitHub

Este repositorio cuenta con **GitHub Actions** (`.github/workflows/compile.yml`). Al realizar un `git push`, el documento se compilará automáticamente en los servidores de GitHub y se podrá descargar el PDF listo desde la pestaña **Actions > Artifacts**.