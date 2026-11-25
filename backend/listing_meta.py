"""
Reading facts out of a property listing, and out of a visitor's question.

Why this exists (RET-04, and RET-01 to RET-03 before it)
--------------------------------------------------------
Vector search matches on overall meaning. Ask "3-bedroom houses in DHA?" and
the words "3 bedroom" pull in every 3-bedroom listing in the data, pushing the
one DHA house out of the top results. The chatbot then answers "I do not have
that information", which is honest but wrong: BRE-S-102 is in DHA, and it has
4 bedrooms. The right answer names it.

Meaning alone cannot fix this, because "DHA" is a hard constraint, not a
flavour. So each listing chunk also carries a few plain facts - area, city,
bedrooms, sale or rent - and a question that names an area can be answered by
looking the area up as well as searching by meaning.

Everything here is Python's standard library, and none of it calls an API.
"""

from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Reading a listing
# ---------------------------------------------------------------------------

# "BRE-S-102 - 10 Marla House, DHA Phase 2, Islamabad"
# The dash may be an em dash or a hyphen.
HEADING_RE = re.compile(
    r"^\s*(?P<ref>BRE-[A-Z]-\d+)\s*[-–—]\s*(?P<rest>.+)$"
)

CITIES = ("islamabad", "rawalpindi")

# "- Bedrooms: 4"
BEDROOMS_RE = re.compile(r"^-\s*Bedrooms:\s*(\d+)", re.M)
# "- Type: House, for sale"
TYPE_RE = re.compile(r"^-\s*Type:\s*(?P<kind>[^,]+),\s*for\s+(?P<deal>sale|rent)", re.M | re.I)

# An Islamabad/Rawalpindi sector, written F-11/3, F-11 or E-11/2.
SECTOR_RE = re.compile(r"\b([A-G])\s*-\s*(\d{1,2})(?:\s*/\s*\d+)?\b", re.I)

# Named areas that are not sectors. The key is what a visitor is likely to
# type; the value is what it should match in the data.
NAMED_AREAS = {
    "dha": "dha",
    "defence": "dha",
    "bahria": "bahria town",
    "bahria town": "bahria town",
    "gulberg": "gulberg",
    "chaklala": "chaklala",
    "satellite town": "satellite town",
    "satellite": "satellite town",
}


def area_keys(area_text: str) -> list[str]:
    """
    Turn an area as written into the keys it should be findable by.

    "DHA Phase 2"               -> ["dha"]
    "F-11/3"                    -> ["f-11"]
    "Bahria Town Islamabad"     -> ["bahria town"]
    "Satellite Town, Block B"   -> ["satellite town"]
    """
    text = (area_text or "").lower()
    keys: list[str] = []

    for match in SECTOR_RE.finditer(text):
        key = f"{match.group(1).lower()}-{int(match.group(2))}"
        if key not in keys:
            keys.append(key)

    # Longest names first, so "satellite town" wins over "satellite".
    for name in sorted(NAMED_AREAS, key=len, reverse=True):
        if name in text:
            canonical = NAMED_AREAS[name]
            if canonical not in keys:
                keys.append(canonical)

    return keys


def parse_listing(heading: str, body: str) -> dict | None:
    """
    Read the facts out of one listing section.

    Returns None when the heading is not a property listing, which is how
    company pages and FAQs are left alone.
    """
    match = HEADING_RE.match(heading or "")
    if not match:
        return None

    rest = match.group("rest")

    # The last comma-separated part is the city when it is one of ours.
    parts = [p.strip() for p in rest.split(",")]
    city = ""
    if parts and parts[-1].lower() in CITIES:
        city = parts.pop().lower()

    # What is left: a description, then the area. The first part describes the
    # property ("10 Marla House"); everything after it is the area.
    area = ", ".join(parts[1:]).strip() if len(parts) > 1 else ""

    # A city can also appear inside the area ("Bahria Town Islamabad").
    if not city:
        for name in CITIES:
            if name in rest.lower():
                city = name
                break

    facts: dict = {
        "is_listing": True,
        "ref": match.group("ref").upper(),
        "city": city,
        "area": area,
        "area_keys": ",".join(area_keys(area)),
    }

    bedrooms = BEDROOMS_RE.search(body or "")
    if bedrooms:
        facts["bedrooms"] = int(bedrooms.group(1))

    type_match = TYPE_RE.search(body or "")
    if type_match:
        facts["kind"] = type_match.group("kind").strip().lower()
        facts["deal"] = type_match.group("deal").strip().lower()

    return facts


# ---------------------------------------------------------------------------
# Reading a question
# ---------------------------------------------------------------------------

# "3-bedroom", "3 bedroom", "3 bed", "three bedroom"
WORD_NUMBERS = {
    "one": 1, "two": 2, "three": 3, "four": 4,
    "five": 5, "six": 6, "seven": 7, "eight": 8,
}
BEDROOMS_IN_QUESTION_RE = re.compile(
    r"\b(\d+|one|two|three|four|five|six|seven|eight)\s*[-\s]?\s*(?:bed|bedroom|bedrooms|bhk)\b",
    re.I,
)


def bedrooms_in_question(question: str) -> int | None:
    """How many bedrooms the visitor asked for, or None."""
    match = BEDROOMS_IN_QUESTION_RE.search(question or "")
    if not match:
        return None
    value = match.group(1).lower()
    if value.isdigit():
        number = int(value)
    else:
        number = WORD_NUMBERS.get(value)
    # A sanity bound: "100 bedroom" is not a real request.
    if number and 1 <= number <= 20:
        return number
    return None


def areas_in_question(question: str, known: set[str]) -> list[str]:
    """
    Which known area keys the question names.

    `known` comes from the stored listings, so the vocabulary is whatever is
    actually in the data rather than a list written by hand here.
    """
    found = []
    for key in area_keys(question or ""):
        if key in known:
            found.append(key)
    return found


def deal_in_question(question: str) -> str | None:
    """Whether the visitor asked about buying or renting."""
    text = (question or "").lower()
    rent_words = ("rent", "renting", "lease", "tenant", "monthly")
    sale_words = ("buy", "buying", "sale", "purchase", "own")
    rent = any(w in text for w in rent_words)
    sale = any(w in text for w in sale_words)
    if rent and not sale:
        return "rent"
    if sale and not rent:
        return "sale"
    return None


# ---------------------------------------------------------------------------
# Putting two sets of search results together
# ---------------------------------------------------------------------------


def merge_hits(plain, extra, top_k):
    """
    Place the area-matched chunks first, then fill up from the ordinary ones.

    `plain` and `extra` are each a dict of parallel lists:
    {"ids": [...], "documents": [...], "metadatas": [...], "distances": [...]}

    Nothing from `plain` is discarded except to stay within `top_k`, and a
    chunk that appears in both is kept once. Kept as a plain function with no
    database in sight so it can be tested on its own.
    """
    fields = ("ids", "documents", "metadatas", "distances")
    out = {f: list(extra.get(f) or []) for f in fields}

    seen = set(out["ids"])
    for index, chunk_id in enumerate(plain.get("ids") or []):
        if len(out["ids"]) >= top_k:
            break
        if chunk_id in seen:
            continue
        seen.add(chunk_id)
        for f in fields:
            values = plain.get(f) or []
            out[f].append(values[index] if index < len(values) else None)

    return out
