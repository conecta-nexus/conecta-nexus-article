#!/usr/bin/env python3
"""
unify_sources.py

Consumes all bibliographic files in a directory (.ris, .bib, .txt),
normalizes them into structured Publication objects, deduplicates them
into a unique set, and exports the unified collection into a single
VOSviewer-compatible RIS file.

Usage:
    python3 scripts/unify_sources.py
    python3 scripts/unify_sources.py --sources-dir sources/ --output sources/unified_citations.ris
"""

import argparse
import glob
import os
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


def normalize_doi(raw_doi: Optional[str]) -> str:
    """Normalize DOI string by stripping URLs, resolvers, and punctuation."""
    if not raw_doi:
        return ""
    doi = raw_doi.strip()
    # Remove URL prefixes
    doi = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", doi, flags=re.IGNORECASE)
    # Remove trailing periods, semicolons, brackets, or spaces
    doi = doi.rstrip(".,;)}/ ")
    return doi.strip().lower()


def normalize_title(raw_title: Optional[str]) -> str:
    """Normalize title for fuzzy fallback matching (alphanumeric lowercase)."""
    if not raw_title:
        return ""
    # Strip HTML/LaTeX tags and non-alphanumeric characters
    cleaned = re.sub(r"<[^>]+>", "", raw_title)
    cleaned = re.sub(r"[{}\"\']", "", cleaned)
    cleaned = re.sub(r"[^\w\s]", " ", cleaned)
    return " ".join(cleaned.lower().split())


def format_author_name(author_str: str) -> str:
    """Normalize an author string into 'Lastname, Firstname' format."""
    s = author_str.strip().rstrip(",")
    if not s:
        return ""
    # If already formatted as 'Lastname, Firstname'
    if "," in s:
        parts = [p.strip() for p in s.split(",") if p.strip()]
        if len(parts) >= 2:
            return f"{parts[0]}, {', '.join(parts[1:])}"
        return parts[0]
    
    # If formatted as 'Firstname [Middle...] Lastname'
    tokens = s.split()
    if len(tokens) == 1:
        return tokens[0]
    return f"{tokens[-1]}, {' '.join(tokens[:-1])}"


@dataclass
class Publication:
    title: str = ""
    authors: List[str] = field(default_factory=list)
    journal: str = ""
    year: str = ""
    date: str = ""
    volume: str = ""
    issue: str = ""
    start_page: str = ""
    end_page: str = ""
    doi: str = ""
    url: str = ""
    issn: str = ""
    abstract: str = ""
    keywords: List[str] = field(default_factory=list)
    entry_type: str = "JOUR"
    source_files: Set[str] = field(default_factory=set)

    @property
    def clean_doi(self) -> str:
        return normalize_doi(self.doi)

    @property
    def clean_title(self) -> str:
        return normalize_title(self.title)

    def get_dedup_key(self) -> str:
        """Unique key for deduplication: DOI if present, otherwise normalized title."""
        c_doi = self.clean_doi
        if c_doi:
            return f"doi:{c_doi}"
        return f"title:{self.clean_title}"

    def __hash__(self) -> int:
        return hash(self.get_dedup_key())

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Publication):
            return False
        return self.get_dedup_key() == other.get_dedup_key()

    def merge(self, other: "Publication") -> None:
        """Merge metadata from another publication instance to preserve the richest data."""
        self.source_files.update(other.source_files)

        if not self.title and other.title:
            self.title = other.title
        elif len(other.title) > len(self.title):
            self.title = other.title

        # Keep richer author list or author list with proper Lastname, Firstname
        if not self.authors and other.authors:
            self.authors = list(other.authors)
        elif other.authors and len(other.authors) >= len(self.authors):
            # If other authors have commas and self don't, prefer other
            self_commas = sum(1 for a in self.authors if "," in a)
            other_commas = sum(1 for a in other.authors if "," in a)
            if other_commas >= self_commas:
                self.authors = list(other.authors)

        if not self.journal and other.journal:
            self.journal = other.journal
        if not self.year and other.year:
            self.year = other.year
        if not self.date and other.date:
            self.date = other.date
        if not self.volume and other.volume:
            self.volume = other.volume
        if not self.issue and other.issue:
            self.issue = other.issue
        if not self.start_page and other.start_page:
            self.start_page = other.start_page
        if not self.end_page and other.end_page:
            self.end_page = other.end_page
        if not self.doi and other.doi:
            self.doi = other.doi
        if not self.url and other.url:
            self.url = other.url
        if not self.issn and other.issn:
            self.issn = other.issn
        if not self.abstract and other.abstract:
            self.abstract = other.abstract
        elif other.abstract and len(other.abstract) > len(self.abstract):
            self.abstract = other.abstract

        # Union keywords preserving order and uniqueness
        existing_kws_lower = {k.lower() for k in self.keywords}
        for kw in other.keywords:
            if kw and kw.lower() not in existing_kws_lower:
                self.keywords.append(kw)
                existing_kws_lower.add(kw.lower())

        if self.entry_type == "JOUR" and other.entry_type != "JOUR":
            self.entry_type = other.entry_type

    def to_ris(self) -> str:
        """Serialize publication to standard VOSviewer-compatible RIS format."""
        lines = [f"TY  - {self.entry_type or 'JOUR'}"]

        if self.title:
            lines.append(f"T1  - {self.title}")
            lines.append(f"TI  - {self.title}")

        for author in self.authors:
            formatted_author = format_author_name(author)
            if formatted_author:
                lines.append(f"AU  - {formatted_author}")

        if self.journal:
            lines.append(f"JO  - {self.journal}")
            lines.append(f"JF  - {self.journal}")

        if self.volume:
            lines.append(f"VL  - {self.volume}")
        if self.issue:
            lines.append(f"IS  - {self.issue}")
        if self.start_page:
            lines.append(f"SP  - {self.start_page}")
        if self.end_page:
            lines.append(f"EP  - {self.end_page}")
        if self.year:
            lines.append(f"PY  - {self.year}")
        if self.date:
            lines.append(f"DA  - {self.date}")
        elif self.year:
            lines.append(f"DA  - {self.year}/01/01/")

        if self.issn:
            lines.append(f"SN  - {self.issn}")

        if self.doi:
            clean_d = self.clean_doi
            lines.append(f"DO  - https://doi.org/{clean_d}")

        if self.url:
            lines.append(f"UR  - {self.url}")

        for kw in self.keywords:
            clean_kw = kw.strip().rstrip(";,.")
            if clean_kw:
                lines.append(f"KW  - {clean_kw}")

        if self.abstract:
            lines.append(f"AB  - {self.abstract}")

        lines.append("ER  - ")
        return "\n".join(lines)


# =====================================================================
# Parsers for RIS, BibTeX, and ScienceDirect plain text
# =====================================================================

def parse_ris(filepath: str) -> List[Publication]:
    """Parse a RIS file into a list of Publication objects."""
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    entries: List[Publication] = []
    # Split records by ER  -
    raw_records = re.split(r"^ER\s{2}-.*$", content, flags=re.MULTILINE)

    for raw in raw_records:
        if not raw.strip():
            continue

        pub = Publication(source_files={os.path.basename(filepath)})
        lines = raw.splitlines()
        current_tag = None

        for line in lines:
            m = re.match(r"^([A-Z0-9]{2})\s{2}-\s?(.*)$", line)
            if m:
                tag, val = m.group(1), m.group(2).strip()
                current_tag = tag

                if tag == "TY":
                    pub.entry_type = val
                elif tag in ("T1", "TI"):
                    if not pub.title or tag == "T1":
                        pub.title = val
                elif tag in ("AU", "A1"):
                    pub.authors.append(val)
                elif tag in ("JO", "JF", "JA", "BT", "T2"):
                    if not pub.journal or tag in ("JO", "JF", "BT"):
                        pub.journal = val
                elif tag == "VL":
                    pub.volume = val
                elif tag == "IS":
                    pub.issue = val
                elif tag == "SP":
                    pub.start_page = val
                elif tag == "EP":
                    pub.end_page = val
                elif tag == "PY":
                    pub.year = val[:4]
                elif tag == "DA":
                    pub.date = val
                elif tag == "SN":
                    pub.issn = val
                elif tag == "DO":
                    pub.doi = val
                elif tag == "UR":
                    pub.url = val
                elif tag == "KW":
                    if val:
                        pub.keywords.append(val)
                elif tag in ("AB", "N2"):
                    pub.abstract = val
            else:
                # Multi-line continuation for tags like AB or T1
                if current_tag in ("AB", "N2"):
                    if line.strip():
                        pub.abstract += " " + line.strip()
                    else:
                        pub.abstract += "\n\n"
                elif current_tag in ("T1", "TI"):
                    pub.title += " " + line.strip()

        pub.title = pub.title.strip()
        pub.abstract = pub.abstract.strip()

        if pub.title or pub.doi:
            entries.append(pub)

    return entries


def parse_bib(filepath: str) -> List[Publication]:
    """Parse a BibTeX file into a list of Publication objects."""
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    entries: List[Publication] = []
    entry_pattern = re.compile(r"@(\w+)\s*\{\s*([^,]+),\s*(.*?)\n\s*\}\s*(?=@|\Z)", re.DOTALL)
    field_pattern = re.compile(
        r"(\w+)\s*=\s*(?:\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}|\"([^\"]*)\"|(\d+))",
        re.DOTALL,
    )

    for m in entry_pattern.finditer(content):
        entry_type = m.group(1).upper()
        body = m.group(3)

        fields: Dict[str, str] = {}
        for fm in field_pattern.finditer(body):
            key = fm.group(1).lower()
            val = fm.group(2) if fm.group(2) is not None else (fm.group(3) if fm.group(3) is not None else fm.group(4))
            fields[key] = val.strip()

        pub = Publication(source_files={os.path.basename(filepath)})

        # Entry type mapping
        if entry_type in ("BOOK", "INBOOK"):
            pub.entry_type = "BOOK"
        elif entry_type in ("INCOLLECTION", "INPROCEEDINGS", "CONFERENCE"):
            pub.entry_type = "CHAP"
        else:
            pub.entry_type = "JOUR"

        pub.title = fields.get("title", "")
        pub.journal = fields.get("journal", fields.get("booktitle", ""))
        pub.volume = fields.get("volume", "")
        pub.issue = fields.get("number", "")
        pub.year = fields.get("year", "")[:4]
        pub.doi = fields.get("doi", "")
        pub.url = fields.get("url", "")
        pub.issn = fields.get("issn", fields.get("isbn", ""))
        pub.abstract = fields.get("abstract", "")

        # Authors
        if "author" in fields:
            raw_authors = fields["author"].split(" and ")
            for a in raw_authors:
                a_clean = a.strip()
                if a_clean:
                    pub.authors.append(a_clean)

        # Keywords
        if "keywords" in fields:
            raw_kws = fields["keywords"].split(",")
            for k in raw_kws:
                k_clean = k.strip()
                if k_clean:
                    pub.keywords.append(k_clean)

        # Pages
        if "pages" in fields:
            page_parts = re.split(r"-+", fields["pages"])
            if len(page_parts) >= 2:
                pub.start_page, pub.end_page = page_parts[0].strip(), page_parts[1].strip()
            elif len(page_parts) == 1:
                pub.start_page = page_parts[0].strip()

        if pub.title or pub.doi:
            entries.append(pub)

    return entries


def parse_txt(filepath: str) -> List[Publication]:
    """Parse ScienceDirect plain text citation exports into Publication objects."""
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    entries: List[Publication] = []
    # Identify records through the DOI and URL anchors
    anchor_pattern = re.compile(
        r"https?://(?:dx\.)?doi\.org/([^\s\)\n]+)\.\n\((https://www\.sciencedirect\.com/[^\)]+)\)"
    )
    matches = list(anchor_pattern.finditer(content))

    for i, m in enumerate(matches):
        doi = m.group(1).strip()
        url = m.group(2).strip()

        prev_url_end = matches[i - 1].end() if i > 0 else 0
        header_area = content[prev_url_end : m.start()]

        if i > 0:
            parts = header_area.split("\n\n")
            cur_header = parts[-1].strip()
        else:
            cur_header = header_area.strip()

        header_lines = [l.strip() for l in cur_header.splitlines() if l.strip()]

        # Extract body (abstract + keywords)
        next_doi_start = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        body_area = content[m.end() : next_doi_start]

        if i + 1 < len(matches):
            body_parts = body_area.split("\n\n")
            cur_body = "\n\n".join(body_parts[:-1]).strip()
        else:
            cur_body = body_area.strip()

        pub = Publication(
            doi=doi,
            url=url,
            source_files={os.path.basename(filepath)},
        )

        # Parse header lines
        # Line 0: Authors (comma-separated, often ending in comma)
        # Line 1: Title (often ending in comma)
        # Line 2: Journal (often ending in comma)
        # Lines 3+: Volume, Issue, Year, Pages, ISSN/ISBN
        if len(header_lines) >= 1:
            raw_author_line = header_lines[0].rstrip(",")
            # ScienceDirect text formats authors as: "First Last, First Last"
            # We split by comma, but some author names have initials or suffixes
            raw_authors = [a.strip() for a in raw_author_line.split(",") if a.strip()]
            pub.authors = raw_authors

        if len(header_lines) >= 2:
            pub.title = header_lines[1].rstrip(",")

        if len(header_lines) >= 3:
            pub.journal = header_lines[2].rstrip(",")

        for line in header_lines[3:]:
            line_clean = line.rstrip(",")
            vol_match = re.search(r"Volume\s+([A-Za-z0-9\-]+)", line_clean, re.IGNORECASE)
            iss_match = re.search(r"Issue\s+([A-Za-z0-9\-]+)", line_clean, re.IGNORECASE)
            page_match = re.search(r"Pages?\s+([A-Za-z0-9]+)(?:\s*-\s*([A-Za-z0-9]+))?", line_clean, re.IGNORECASE)
            year_match = re.match(r"^(\d{4})$", line_clean)
            issn_match = re.search(r"ISSN\s+([0-9Xx\-]+)", line_clean, re.IGNORECASE)

            if vol_match and not pub.volume:
                pub.volume = vol_match.group(1)
            if iss_match and not pub.issue:
                pub.issue = iss_match.group(1)
            if page_match and not pub.start_page:
                pub.start_page = page_match.group(1)
                if page_match.group(2):
                    pub.end_page = page_match.group(2)
            if year_match and not pub.year:
                pub.year = year_match.group(1)
            if issn_match and not pub.issn:
                pub.issn = issn_match.group(1)

        # Parse body: Abstract and Keywords
        body_lines = [l.strip() for l in cur_body.splitlines() if l.strip()]
        abstract_parts: List[str] = []
        is_abstract = False

        for bline in body_lines:
            if bline.startswith("Keywords:"):
                is_abstract = False
                raw_kws = bline.replace("Keywords:", "").strip()
                # Split by semicolon or comma
                delimiter = ";" if ";" in raw_kws else ","
                for kw in raw_kws.split(delimiter):
                    clean_kw = kw.strip()
                    if clean_kw:
                        pub.keywords.append(clean_kw)
            elif bline.startswith("Abstract:"):
                is_abstract = True
                content_after = bline.replace("Abstract:", "").strip()
                if content_after:
                    abstract_parts.append(content_after)
            elif is_abstract:
                abstract_parts.append(bline)

        pub.abstract = " ".join(abstract_parts).strip()

        if pub.title or pub.doi:
            entries.append(pub)

    return entries


def load_file(filepath: str) -> List[Publication]:
    """Dispatch file loader based on file extension."""
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".ris":
        return parse_ris(filepath)
    elif ext == ".bib":
        return parse_bib(filepath)
    elif ext == ".txt":
        return parse_txt(filepath)
    return []


# =====================================================================
# Main Unification & Pipeline Execution
# =====================================================================

def unify_sources(
    sources_dir: str = "sources",
    output_path: str = "sources/unified_citations.ris",
) -> int:
    """Read all source files, normalize, deduplicate into a set, and write to output file."""
    if not os.path.isdir(sources_dir):
        raise FileNotFoundError(f"Sources directory not found: {sources_dir}")

    output_abs = os.path.abspath(output_path)
    output_filename = os.path.basename(output_path)

    # Find candidate files (.ris, .bib, .txt) excluding the target output file
    pattern_ris = glob.glob(os.path.join(sources_dir, "*.ris"))
    pattern_bib = glob.glob(os.path.join(sources_dir, "*.bib"))
    pattern_txt = glob.glob(os.path.join(sources_dir, "*.txt"))
    all_files = sorted(set(pattern_ris + pattern_bib + pattern_txt))

    source_files = [f for f in all_files if os.path.abspath(f) != output_abs and not os.path.basename(f).startswith("unified_")]

    print("=" * 60)
    print("VOSviewer Bibliographic Unification Pipeline")
    print("=" * 60)
    print(f"Sources directory : {sources_dir}")
    print(f"Target output     : {output_path}")
    print(f"Found input files : {len(source_files)}")
    print("-" * 60)

    total_raw_records = 0
    # Use a dictionary keyed by the publication (uses __hash__ and __eq__) to merge metadata
    unique_registry: Dict[Publication, Publication] = {}

    for filepath in source_files:
        records = load_file(filepath)
        total_raw_records += len(records)
        print(f"  • Ingested {len(records):>3} records from: {os.path.basename(filepath)}")

        for pub in records:
            if pub in unique_registry:
                # Merge into existing record
                unique_registry[pub].merge(pub)
            else:
                unique_registry[pub] = pub

    # Explicitly convert to a Python Set to satisfy set-based deduplication
    publication_set: Set[Publication] = set(unique_registry.values())
    unique_count = len(publication_set)
    duplicates_merged = total_raw_records - unique_count

    print("-" * 60)
    print(f"Total raw records parsed : {total_raw_records}")
    print(f"Duplicates merged        : {duplicates_merged}")
    print(f"Final unique publications: {unique_count}")
    print("-" * 60)

    # Sort publications deterministically by Year (descending) and Title (ascending)
    sorted_publications = sorted(
        publication_set,
        key=lambda p: (p.year or "0000", p.title or ""),
        reverse=True,
    )

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_abs), exist_ok=True)

    # Write unified RIS file
    with open(output_abs, "w", encoding="utf-8") as f_out:
        for pub in sorted_publications:
            f_out.write(pub.to_ris())
            f_out.write("\n\n")

    print(f"Successfully generated: {output_path}")
    print(f"File size: {os.path.getsize(output_abs):,} bytes")
    print("=" * 60)
    return unique_count


def main():
    parser = argparse.ArgumentParser(
        description="Unify and deduplicate bibliographic sources (.ris, .bib, .txt) into a VOSviewer-ready format."
    )
    parser.add_argument(
        "--sources-dir",
        "-s",
        default="sources",
        help="Path to directory containing source citation files (default: sources)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="sources/unified_citations.ris",
        help="Path to the output file (default: sources/unified_citations.ris)",
    )

    args = parser.parse_args()
    unify_sources(sources_dir=args.sources_dir, output_path=args.output)


if __name__ == "__main__":
    main()
