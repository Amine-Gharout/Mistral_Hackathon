"""Domain-aware hierarchical chunking for the ANAH 2026 guide."""

from __future__ import annotations

import re
from typing import Optional


# Heading patterns to detect section boundaries
HEADING_PATTERNS = [
    re.compile(r"^(Chapitre\s+\d+|CHAPITRE\s+\d+)", re.MULTILINE),
    re.compile(r"^(Partie\s+\d+|PARTIE\s+\d+)", re.MULTILINE),
    re.compile(r"^(\d+\.\s+[A-ZÀ-Ü])", re.MULTILINE),
    re.compile(r"^(MaPrimeRénov|Éco-PTZ|Éco-prêt|CEE|Certificats d'Économies)",
               re.MULTILINE | re.IGNORECASE),
    re.compile(r"^(Conditions|Montant|Plafond|Éligibilité|Barème|Tableau)",
               re.MULTILINE | re.IGNORECASE),
]

# Keywords to classify chunk type
TABLE_KEYWORDS = [
    "tableau", "barème", "plafond", "montant", "€", "revenus",
    "très modestes", "modestes", "intermédiaires", "supérieurs",
]

AID_TYPE_KEYWORDS = {
    "mpr_par_geste": ["par geste", "geste par geste", "forfaitaire"],
    "mpr_ampleur": ["rénovation d'ampleur", "parcours accompagné", "rénovation globale"],
    "eco_ptz": ["éco-ptz", "éco-prêt", "prêt à taux zéro"],
    "cee": ["certificats d'économies", "CEE", "coup de pouce"],
    "tva": ["TVA", "5,5%", "taux réduit"],
    "conditions_revenus": ["revenus", "barème", "plafonds de ressources"],
}


def chunk_pages(pages: list[dict], chunk_size: int = 1200, overlap: int = 100) -> list[dict]:
    """
    Create hierarchical chunks from extracted PDF pages.

    Strategy:
    - Detect section boundaries from headings
    - Create section-level chunks (500-1500 tokens ≈ chunk_size chars)
    - Identify table-like content and tag it
    - Add overlap between adjacent chunks

    Args:
        pages: List of page dicts from loader
        chunk_size: Target chunk size in characters
        overlap: Number of overlap characters between chunks

    Returns:
        List of chunk dicts with text, metadata
    """
    if not pages:
        return _get_fallback_chunks()

    # Concatenate all pages with page markers
    full_text = ""
    page_boundaries = []
    for page in pages:
        start = len(full_text)
        full_text += f"\n--- Page {page['page_number']} ---\n{page['text']}\n"
        page_boundaries.append((start, len(full_text), page["page_number"]))

    # Split into sections based on headings
    sections = _split_into_sections(full_text)

    # Create chunks from sections
    chunks = []
    chunk_id = 0

    for section in sections:
        section_text = section["text"]
        section_title = section["title"]

        if len(section_text) <= chunk_size:
            # Section fits in one chunk
            chunk = _create_chunk(
                chunk_id=chunk_id,
                text=section_text,
                title=section_title,
                page_number=_find_page(section["start_pos"], page_boundaries),
            )
            chunks.append(chunk)
            chunk_id += 1
        else:
            # Split section into smaller chunks
            sub_chunks = _split_text(section_text, chunk_size, overlap)
            for i, sub_text in enumerate(sub_chunks):
                chunk = _create_chunk(
                    chunk_id=chunk_id,
                    text=sub_text,
                    title=f"{section_title} (partie {i + 1})",
                    page_number=_find_page(
                        section["start_pos"], page_boundaries),
                )
                chunks.append(chunk)
                chunk_id += 1

    print(f"[RAG] Created {len(chunks)} chunks from PDF")
    return chunks


def _split_into_sections(text: str) -> list[dict]:
    """Split text into sections based on heading patterns."""
    # Find all heading positions
    headings = []
    for pattern in HEADING_PATTERNS:
        for match in pattern.finditer(text):
            headings.append((match.start(), match.group()))

    # Sort by position
    headings.sort(key=lambda x: x[0])

    if not headings:
        # No headings found — treat entire text as one section
        return [{"title": "Document complet", "text": text, "start_pos": 0}]

    # Deduplicate close headings (within 50 chars)
    deduped = [headings[0]]
    for pos, title in headings[1:]:
        if pos - deduped[-1][0] > 50:
            deduped.append((pos, title))

    # Create sections
    sections = []
    for i, (pos, title) in enumerate(deduped):
        end = deduped[i + 1][0] if i + 1 < len(deduped) else len(text)
        section_text = text[pos:end].strip()
        if section_text:
            sections.append({
                "title": title.strip(),
                "text": section_text,
                "start_pos": pos,
            })

    return sections


def _split_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Split text into overlapping chunks at sentence boundaries."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current = ""

    for sentence in sentences:
        if len(current) + len(sentence) > chunk_size and current:
            chunks.append(current.strip())
            # Keep overlap from the end of current chunk
            overlap_text = current[-overlap:] if len(
                current) > overlap else current
            current = overlap_text + " " + sentence
        else:
            current = current + " " + sentence if current else sentence

    if current.strip():
        chunks.append(current.strip())

    return chunks


def _create_chunk(chunk_id: int, text: str, title: str, page_number: Optional[int]) -> dict:
    """Create a chunk dict with metadata."""
    # Detect chunk type
    text_lower = text.lower()
    is_table = any(kw in text_lower for kw in TABLE_KEYWORDS) and (
        "€" in text or "montant" in text_lower)

    # Detect aid type
    aid_type = "general"
    for aid, keywords in AID_TYPE_KEYWORDS.items():
        if any(kw.lower() in text_lower for kw in keywords):
            aid_type = aid
            break

    return {
        "chunk_id": chunk_id,
        "text": text,
        "title": title,
        "page_number": page_number,
        "chunk_type": "table" if is_table else "prose",
        "aid_type": aid_type,
        "char_count": len(text),
        "effective_date": "2026-01-01",
    }


def _find_page(pos: int, page_boundaries: list[tuple]) -> Optional[int]:
    """Find which page a position falls in."""
    for start, end, page_num in page_boundaries:
        if start <= pos < end:
            return page_num
    return None


def _get_fallback_chunks() -> list[dict]:
    """Return built-in knowledge chunks when PDF is not available."""
    fallback = [
        {
            "chunk_id": 0,
            "text": (
                "MaPrimeRénov' est une aide de l'État pour la rénovation énergétique des logements. "
                "Elle est ouverte à tous les propriétaires occupants et bailleurs, sans conditions de revenus "
                "pour le parcours accompagné (rénovation d'ampleur). Le parcours par geste est réservé aux "
                "ménages des catégories bleu (très modestes), jaune (modestes) et violet (intermédiaires). "
                "Les ménages roses (revenus supérieurs) ne sont éligibles qu'au parcours accompagné. "
                "Source : ANAH Guide des aides financières 2026."
            ),
            "title": "MaPrimeRénov' — Présentation générale",
            "page_number": None,
            "chunk_type": "prose",
            "aid_type": "mpr_par_geste",
            "char_count": 0,
            "effective_date": "2026-01-01",
        },
        {
            "chunk_id": 1,
            "text": (
                "MaPrimeRénov' Parcours accompagné (rénovation d'ampleur) permet de financer une rénovation "
                "globale du logement. Conditions : gain d'au moins 2 classes DPE, au moins 2 gestes d'isolation, "
                "accompagnement obligatoire par un Accompagnateur Rénov'. Le programme a été réouvert le 23 février 2026. "
                "Plafonds de travaux : 40 000 € HT pour 2 classes, 55 000 € pour 3 classes, 70 000 € pour 4+ classes. "
                "Taux de financement : jusqu'à 80% pour les très modestes, 60% modestes, 50% intermédiaires, 35% supérieurs. "
                "Bonification sortie de passoire thermique : +10% si le logement passe de F/G à D minimum."
            ),
            "title": "MaPrimeRénov' Parcours accompagné",
            "page_number": None,
            "chunk_type": "prose",
            "aid_type": "mpr_ampleur",
            "char_count": 0,
            "effective_date": "2026-01-01",
        },
        {
            "chunk_id": 2,
            "text": (
                "L'Éco-prêt à taux zéro (Éco-PTZ) est un prêt sans intérêts pour financer les travaux de "
                "rénovation énergétique. Montants : 15 000 € pour 1 action, 25 000 € pour 2 actions, "
                "30 000 € pour 3+ actions, 50 000 € pour une rénovation d'ampleur (performance globale). "
                "Durée de remboursement : jusqu'à 15 ans (20 ans pour la performance globale). "
                "Conditions : logement de plus de 2 ans, résidence principale, travaux par un professionnel RGE. "
                "L'Éco-PTZ est cumulable avec MaPrimeRénov' et les CEE."
            ),
            "title": "Éco-PTZ — Éco-prêt à taux zéro",
            "page_number": None,
            "chunk_type": "prose",
            "aid_type": "eco_ptz",
            "char_count": 0,
            "effective_date": "2026-01-01",
        },
        {
            "chunk_id": 3,
            "text": (
                "Les Certificats d'Économies d'Énergie (CEE) — Coup de pouce chauffage : les fournisseurs "
                "d'énergie versent des primes pour le remplacement d'une chaudière gaz, fioul ou charbon par "
                "un système de chauffage performant (PAC, biomasse, solaire, réseau de chaleur). "
                "Montants indicatifs : 5 000 € pour les très modestes, 4 000 € pour les modestes, "
                "2 500 € pour les intermédiaires et supérieurs. Les montants varient selon le fournisseur. "
                "Les CEE sont cumulables avec MaPrimeRénov' par geste mais pas avec le parcours accompagné."
            ),
            "title": "CEE Coup de pouce chauffage",
            "page_number": None,
            "chunk_type": "prose",
            "aid_type": "cee",
            "char_count": 0,
            "effective_date": "2026-01-01",
        },
        {
            "chunk_id": 4,
            "text": (
                "Documents nécessaires pour une demande MaPrimeRénov' : "
                "1. Dernier avis d'imposition (pour le RFR). "
                "2. Devis détaillé des travaux signé par un professionnel RGE. "
                "3. Justificatif de propriété (taxe foncière ou titre de propriété). "
                "4. Diagnostic de Performance Énergétique (DPE) ou audit énergétique. "
                "5. RIB pour le versement de l'aide. "
                "6. Pour la rénovation d'ampleur : rapport de l'Accompagnateur Rénov'. "
                "La demande se fait sur le site maprimerenov.gouv.fr AVANT le début des travaux."
            ),
            "title": "Documents nécessaires — MaPrimeRénov'",
            "page_number": None,
            "chunk_type": "prose",
            "aid_type": "general",
            "char_count": 0,
            "effective_date": "2026-01-01",
        },
        {
            "chunk_id": 5,
            "text": (
                "Barème des plafonds de ressources 2026 pour MaPrimeRénov' : "
                "En Île-de-France (personne seule) : Bleu ≤ 24 031 €, Jaune ≤ 29 253 €, Violet ≤ 40 851 €, Rose > 40 851 €. "
                "Hors Île-de-France (personne seule) : Bleu ≤ 17 363 €, Jaune ≤ 22 259 €, Violet ≤ 31 185 €, Rose > 31 185 €. "
                "Pour un ménage de 4 personnes hors IDF : Bleu ≤ 35 676 €, Jaune ≤ 45 735 €, Violet ≤ 64 550 €. "
                "Pour chaque personne supplémentaire (hors IDF) : +5 151 € (bleu), +6 598 € (jaune), +9 357 € (violet)."
            ),
            "title": "Barème des revenus MaPrimeRénov' 2026",
            "page_number": None,
            "chunk_type": "table",
            "aid_type": "conditions_revenus",
            "char_count": 0,
            "effective_date": "2026-01-01",
        },
    ]

    for chunk in fallback:
        chunk["char_count"] = len(chunk["text"])

    return fallback
