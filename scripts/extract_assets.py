#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script: extraer_assets.py
Propósito: Extrae todas las imágenes (media), logotipos, encabezados y pies de página
           de la plantilla oficial de Word 'plantilla_ingenio.docx' y los organiza
           en el directorio 'assets/' para su uso directo en la plantilla LaTeX.
Requisitos: Python 3.8+ (No requiere librerías externas).
"""

import os
import sys
import zipfile
import json
import xml.etree.ElementTree as ET
from pathlib import Path

# Namespaces estándar de OpenXML (archivos .docx)
NS = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'rel': 'http://schemas.openxmlformats.org/package/2006/relationships'
}


def resolver_rutas():
    """Calcula las rutas relativas al proyecto de forma independiente al CWD."""
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    docx_path = project_root / "plantilla_ingenio.docx"
    assets_dir = project_root / "assets"
    
    return project_root, docx_path, assets_dir


def extraer_texto_xml(xml_content):
    """Extrae todos los párrafos de un nodo XML de WordProcessingML."""
    root = ET.fromstring(xml_content)
    parrafos = []
    
    for p in root.findall('.//w:p', NS):
        textos = [t.text for t in p.findall('.//w:t', NS) if t.text]
        linea = "".join(textos).strip()
        if linea:
            parrafos.append(linea)
            
    return parrafos


def procesar_relaciones(zip_file, rels_path):
    """Mapea IDs de relaciones con archivos de destino (imágenes, enlaces)."""
    relaciones = {}
    if rels_path in zip_file.namelist():
        tree = ET.fromstring(zip_file.read(rels_path))
        for rel in tree.findall('.//{http://schemas.openxmlformats.org/package/2006/relationships}Relationship'):
            r_id = rel.get('Id')
            target = rel.get('Target')
            relaciones[r_id] = target
    return relaciones


def main():
    project_root, docx_path, assets_dir = resolver_rutas()

    print("=" * 70)
    print("EXTRACTOR DE ASSETS - REVISTA INGENIO (UFPS)")
    print("=" * 70)
    print(f"[>] Raíz del proyecto : {project_root}")
    print(f"[>] Archivo docx origen: {docx_path}")
    print(f"[>] Directorio assets  : {assets_dir}")
    print("-" * 70)

    # 1. Validación de existencia del archivo original
    if not docx_path.is_file():
        print(f"[ERROR] No se encontró el archivo '{docx_path.name}' en la raíz del proyecto.")
        print(f"        Por favor copia el archivo a:\n        {docx_path}")
        sys.exit(1)

    # 2. Creación de subdirectorios en assets/
    dir_brand = assets_dir / "brand"
    dir_figures = assets_dir / "figures"
    dir_brand.mkdir(parents=True, exist_ok=True)
    dir_figures.mkdir(parents=True, exist_ok=True)

    manifest = {
        "origen": docx_path.name,
        "media": [],
        "encabezados": {},
        "pies_de_pagina": {}
    }

    try:
        with zipfile.ZipFile(docx_path, 'r') as docx_zip:
            file_list = docx_zip.namelist()

            # --- A. Identificar relaciones de encabezados y pies ---
            header_media_targets = set()
            footer_media_targets = set()

            for filename in file_list:
                if filename.startswith("word/_rels/header") and filename.endswith(".xml.rels"):
                    rels = procesar_relaciones(docx_zip, filename)
                    for target in rels.values():
                        header_media_targets.add(os.path.basename(target))
                elif filename.startswith("word/_rels/footer") and filename.endswith(".xml.rels"):
                    rels = procesar_relaciones(docx_zip, filename)
                    for target in rels.values():
                        footer_media_targets.add(os.path.basename(target))

            # --- B. Extracción de imágenes y medios (word/media/*) ---
            media_files = [f for f in file_list if f.startswith("word/media/")]
            print(f"[*] Recursos multimedia encontrados: {len(media_files)}")

            for m_path in media_files:
                base_name = os.path.basename(m_path)
                data = docx_zip.read(m_path)

                # Clasificar si la imagen pertenece a membretes/logos o al cuerpo del artículo
                if base_name in header_media_targets or base_name in footer_media_targets or "logo" in base_name.lower():
                    destino = dir_brand / base_name
                    tipo = "brand_header_footer"
                else:
                    destino = dir_figures / base_name
                    tipo = "body_figure"

                with open(destino, "wb") as f_out:
                    f_out.write(data)

                peso_kb = round(len(data) / 1024, 2)
                manifest["media"].append({
                    "archivo": str(destino.relative_to(project_root)),
                    "nombre": base_name,
                    "tamano_kb": peso_kb,
                    "tipo": tipo
                })
                print(f"    [+] Extraído: {destino.relative_to(project_root)} ({peso_kb} KB)")

            # --- C. Extracción de textos de encabezados (word/header*.xml) ---
            headers = [f for f in file_list if f.startswith("word/header") and f.endswith(".xml")]
            for h in sorted(headers):
                parrafos = extraer_texto_xml(docx_zip.read(h))
                if parrafos:
                    manifest["encabezados"][h] = parrafos

            # --- D. Extracción de textos de pies de página (word/footer*.xml) ---
            footers = [f for f in file_list if f.startswith("word/footer") and f.endswith(".xml")]
            for f in sorted(footers):
                parrafos = extraer_texto_xml(docx_zip.read(f))
                if parrafos:
                    manifest["pies_de_pagina"][f] = parrafos

        # --- 3. Guardar resumen legible de encabezados y pies de página ---
        texto_resumen_path = assets_dir / "encabezados_y_pies.txt"
        with open(texto_resumen_path, "w", encoding="utf-8") as f_txt:
            f_txt.write("====================================================\n")
            f_txt.write("TEXTOS DE ENCABEZADO Y PIE EXTRAÍDOS DE LA PLANTILLA\n")
            f_txt.write("====================================================\n\n")

            f_txt.write("--- ENCABEZADOS (HEADERS) ---\n")
            if manifest["encabezados"]:
                for h_name, lineas in manifest["encabezados"].items():
                    f_txt.write(f"\n[{h_name}]\n")
                    for l in lineas:
                        f_txt.write(f"  * {l}\n")
            else:
                f_txt.write("No se detectó texto estático en encabezados.\n")

            f_txt.write("\n\n--- PIES DE PÁGINA (FOOTERS) ---\n")
            if manifest["pies_de_pagina"]:
                for f_name, lineas in manifest["pies_de_pagina"].items():
                    f_txt.write(f"\n[{f_name}]\n")
                    for l in lineas:
                        f_txt.write(f"  * {l}\n")
            else:
                f_txt.write("No se detectó texto estático en pies de página.\n")

        # --- 4. Guardar manifiesto JSON ---
        manifest_path = assets_dir / "manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f_json:
            json.dump(manifest, f_json, indent=2, ensure_ascii=False)

        print("-" * 70)
        print(f"[OK] Manifiesto generado : {manifest_path.relative_to(project_root)}")
        print(f"[OK] Textos extraídos    : {texto_resumen_path.relative_to(project_root)}")
        print(f"[OK] Extracción completada exitosamente.")
        print("=" * 70)

    except zipfile.BadZipFile:
        print(f"[ERROR] El archivo '{docx_path.name}' no es un archivo .docx válido o está dañado.")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Ocurrió un error inesperado durante el procesamiento: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()