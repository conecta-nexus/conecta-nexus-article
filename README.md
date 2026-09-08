# Plantilla LaTeX - Revista INGENIO (UFPS)

Plantilla oficial en LaTeX para artículos de investigación y revisión adaptada a las directrices de la **Revista Ingenio** de la Universidad Francisco de Paula Santander (UFPS).

## Requisitos y Configuración Rápida en VS Code

1. **Instalar Visual Studio Code**.
2. **Instalar una distribución de LaTeX**:
   - Windows: [MiKTeX](https://miktex.org/) o [TeX Live](https://www.tug.org/texlive/).
   - macOS: [MacTeX](https://www.tug.org/mactex/).
   - Linux (Ubuntu/Debian): `sudo apt-get install texlive-latex-extra texlive-science texlive-bibtex-extra`
3. **Instalar las siguientes extensiones en VS Code**:
   - `James-Yu.latex-workshop` (LaTeX Workshop).
   - `valentjn.vscode-ltex` (Corrector gramatical y ortográfico en español).
4. **Abrir la carpeta del proyecto en VS Code**:
   - Al editar `main.tex` y guardar (`Ctrl + S`), el PDF se compilará automáticamente.
   - Presiona `Ctrl + Alt + V` para abrir el visor de PDF integrado en una pestaña lateral.

## Automatización en GitHub

Este repositorio cuenta con **GitHub Actions** (`.github/workflows/compile.yml`). Al realizar un `git push`, el documento se compilará automáticamente en los servidores de GitHub y podrás descargar el PDF listo desde la pestaña **Actions > Artifacts**.