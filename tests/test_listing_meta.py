r"""
test_listing_meta.py - Task 4.1, unit tests for backend/listing_meta.py

This is the fix for RET-04: a question that names an area must be able to
reach that area's listings even when the rest of the wording pulls somewhere
else. No server, no API key and no network needed:

    pytest tests\test_listing_meta.py -v

Several tests read the real files in data/, so they fail if the data and the
parser ever drift apart.
"""

import sys
from pathlib import Path

import pytest

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT / "backend"))
import listing_meta as lm  # noqa: E402


def real_listings():
    """Every '## ' section of every listing file, parsed."""
    out = []
    for path in sorted((PROJECT / "data" / "listings").glob("*.md")):
        heading, body = None, []
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("## "):
                if heading:
                    out.append((heading, lm.parse_listing(heading, "\n".join(body))))
                heading, body = line[3:].strip(), []
            elif heading is not None:
                body.append(line)
        if heading:
            out.append((heading, lm.parse_listing(heading, "\n".join(body))))
    return out


# ---------------------------------------------------------------------------
# Reading the real data
# ---------------------------------------------------------------------------


def test_LM_01_every_real_listing_is_parsed():
    """LM-01: no listing in data/ is missed by the parser."""
    rows = real_listings()
    assert rows, "no listings found - has data/listings moved?"
    unparsed = [h for h, f in rows if f is None]
    assert unparsed == [], f"these headings were not recognised: {unparsed}"


def test_LM_02_every_listing_has_the_facts_needed_to_filter():
    """LM-02: each listing yields an area key, a city and a sale/rent flag."""
    for heading, facts in real_listings():
        assert facts["area_key"] if "area_key" in facts else facts["area_keys"], heading
        assert facts["city"] in ("islamabad", "rawalpindi"), heading
        assert facts.get("deal") in ("sale", "rent"), heading
        assert isinstance(facts.get("bedrooms"), int), heading


def test_LM_03_the_DHA_case_that_AC_1_depends_on():
    """
    LM-03: the exact situation behind RET-04.

    There is one DHA property and it has four bedrooms, so the only correct
    answer to "3-bedroom houses in DHA?" names it as the nearest match. If
    this ever changes, AC-1's expected answer changes with it.
    """
    dha = [f for _, f in real_listings() if "dha" in f["area_keys"].split(",")]
    assert len(dha) == 1, f"expected exactly one DHA listing, found {len(dha)}"
    assert dha[0]["ref"] == "BRE-S-102"
    assert dha[0]["bedrooms"] == 4
    assert not [f for f in dha if f["bedrooms"] == 3]


def test_LM_04_non_listings_are_left_alone():
    """LM-04: company pages and FAQs must not be given listing metadata."""
    assert lm.parse_listing("Founded", "Bella Real Estate was founded in 2014.") is None
    assert lm.parse_listing("How do I book a viewing?", "- Call us.") is None
    assert lm.parse_listing("", "") is None


# ---------------------------------------------------------------------------
# Area names
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("written,expected", [
    ("DHA Phase 2", ["dha"]),
    ("F-11/3", ["f-11"]),
    ("E-11/2", ["e-11"]),
    ("F-8/2", ["f-8"]),
    ("Bahria Town Islamabad, Phase 8", ["bahria town"]),
    ("Satellite Town, Block B", ["satellite town"]),
    ("Chaklala Scheme 3", ["chaklala"]),
    ("Gulberg Greens", ["gulberg"]),
])
def test_LM_05_area_names_normalise(written, expected):
    """LM-05: an area as written becomes the key it should be found by."""
    assert lm.area_keys(written) == expected


def test_LM_06_longer_area_names_win():
    """LM-06: 'satellite town' must not be shortened to 'satellite'."""
    assert lm.area_keys("Satellite Town") == ["satellite town"]


def test_LM_07_defence_is_understood_as_dha():
    """LM-07: visitors say 'Defence' as often as 'DHA'."""
    assert lm.area_keys("Defence Housing Authority") == ["dha"]


# ---------------------------------------------------------------------------
# Reading a question
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("question,expected", [
    ("Do you have 3-bedroom houses in DHA?", 3),
    ("Any 3 bedroom flats?", 3),
    ("I want a three bedroom house", 3),
    ("2 bed apartment please", 2),
    ("What are your fees?", None),
    ("I need a 100 bedroom palace", None),
])
def test_LM_08_bedrooms_are_read_from_the_question(question, expected):
    """LM-08: the bedroom count is picked up, and nonsense is ignored."""
    assert lm.bedrooms_in_question(question) == expected


def test_LM_09_areas_are_matched_against_what_is_in_the_data():
    """LM-09: only areas the data actually has are recognised."""
    known = {"dha", "f-11", "bahria town"}
    assert lm.areas_in_question("3-bedroom houses in DHA?", known) == ["dha"]
    assert lm.areas_in_question("anything in F-11/3?", known) == ["f-11"]
    assert lm.areas_in_question("houses in Lahore?", known) == []
    assert lm.areas_in_question("what are your fees?", known) == []


def test_LM_10_an_empty_vocabulary_matches_nothing():
    """
    LM-10: with an index built before 4.1 there is no area metadata.

    The vocabulary is then empty and retrieval must quietly behave exactly as
    it did before, rather than failing.
    """
    assert lm.areas_in_question("3-bedroom houses in DHA?", set()) == []


@pytest.mark.parametrize("question,expected", [
    ("What is available to rent?", "rent"),
    ("I want to buy a house", "sale"),
    ("houses for sale in F-11", "sale"),
    ("Do you have anything in DHA?", None),
])
def test_LM_11_buying_or_renting_is_read_from_the_question(question, expected):
    """LM-11: a question that clearly says buy or rent is understood."""
    assert lm.deal_in_question(question) == expected


# ---------------------------------------------------------------------------
# Merging two sets of results
# ---------------------------------------------------------------------------


def hits(ids):
    return {"ids": list(ids),
            "documents": [f"doc-{i}" for i in ids],
            "metadatas": [{"ref": i} for i in ids],
            "distances": [0.1 * n for n, _ in enumerate(ids)]}


def test_LM_12_area_matches_come_first():
    """LM-12: the area's listings lead, so the model definitely sees them."""
    merged = lm.merge_hits(hits(["a", "b", "c"]), hits(["x", "y"]), top_k=8)
    assert merged["ids"][:2] == ["x", "y"]


def test_LM_13_ordinary_results_fill_the_rest():
    """LM-13: nothing is thrown away while there is room."""
    merged = lm.merge_hits(hits(["a", "b", "c"]), hits(["x"]), top_k=8)
    assert merged["ids"] == ["x", "a", "b", "c"]


def test_LM_14_a_chunk_in_both_is_kept_once():
    """LM-14: the same chunk must not be sent to the model twice."""
    merged = lm.merge_hits(hits(["a", "x", "b"]), hits(["x"]), top_k=8)
    assert merged["ids"] == ["x", "a", "b"]
    assert merged["ids"].count("x") == 1


def test_LM_15_the_limit_is_respected():
    """LM-15: the prompt must not grow past TOP_K chunks."""
    merged = lm.merge_hits(hits(list("abcdefgh")), hits(["x", "y"]), top_k=8)
    assert len(merged["ids"]) == 8
    assert merged["ids"][:2] == ["x", "y"]


def test_LM_16_every_field_stays_lined_up():
    """LM-16: documents, metadata and distances must match their ids."""
    merged = lm.merge_hits(hits(["a", "b"]), hits(["x"]), top_k=8)
    for position, chunk_id in enumerate(merged["ids"]):
        assert merged["documents"][position] == f"doc-{chunk_id}"
        assert merged["metadatas"][position]["ref"] == chunk_id
    assert len(merged["distances"]) == len(merged["ids"])


def test_LM_17_no_area_match_leaves_the_results_untouched():
    """LM-17: an empty area result must not disturb ordinary search."""
    plain = hits(["a", "b", "c"])
    merged = lm.merge_hits(plain, hits([]), top_k=8)
    assert merged["ids"] == ["a", "b", "c"]


# ---------------------------------------------------------------------------
# Refreshing stored metadata without re-embedding (ingest.refresh_metadata)
# ---------------------------------------------------------------------------

import ingest  # noqa: E402


class FakeCollection:
    """
    Stands in for a ChromaDB collection.

    It records every call, so a test can prove that nothing was embedded and
    that only the chunks that actually changed were written.
    """

    def __init__(self, stored):
        self.stored = dict(stored)
        self.updates = []
        self.adds = []

    def get(self, ids=None, include=None):
        ids = list(self.stored) if ids is None else [i for i in ids if i in self.stored]
        return {"ids": ids, "metadatas": [self.stored[i] for i in ids]}

    def update(self, ids, metadatas):
        self.updates.append((list(ids), list(metadatas)))
        for chunk_id, meta in zip(ids, metadatas):
            self.stored[chunk_id] = meta

    def upsert(self, *a, **k):          # pragma: no cover - must never happen
        self.adds.append((a, k))


def test_LM_18_old_index_gets_the_new_facts_without_embedding():
    """
    LM-18: an index built before 4.1 is upgraded free of charge.

    The text has not changed, so the embeddings have not changed. Only the
    metadata is rewritten, and no Gemini request is made.
    """
    old_meta = {"source": "data/listings/01.md", "title": "T", "heading": "H", "part": 0}
    new_meta = dict(old_meta, is_listing=True, ref="BRE-S-102", city="islamabad",
                    area="DHA Phase 2", area_keys="dha", area_key="dha",
                    bedrooms=4, deal="sale", kind="house")
    collection = FakeCollection({"c1": old_meta})
    chunks = [{"id": "c1", "text": "unchanged", "metadata": new_meta}]

    ingest.refresh_metadata(collection, chunks, {"c1"})

    assert collection.updates, "the stale chunk should have been updated"
    assert collection.updates[0][0] == ["c1"]
    assert collection.stored["c1"]["area_key"] == "dha"
    assert collection.adds == [], "nothing may be re-embedded or re-added"


def test_LM_19_nothing_is_written_when_metadata_already_matches():
    """LM-19: running it twice must be a no-op, not a rewrite."""
    meta = {"source": "s", "title": "t", "heading": "h", "part": 0,
            "is_listing": True, "area_key": "dha"}
    collection = FakeCollection({"c1": dict(meta)})
    ingest.refresh_metadata(collection, [{"id": "c1", "metadata": dict(meta)}], {"c1"})
    assert collection.updates == []


def test_LM_20_only_the_changed_chunks_are_written():
    """LM-20: a chunk whose metadata is current is left alone."""
    same = {"source": "s", "title": "t", "heading": "h", "part": 0}
    changed_old = dict(same)
    changed_new = dict(same, is_listing=True, area_key="f-11")
    collection = FakeCollection({"keep": dict(same), "fix": changed_old})
    chunks = [{"id": "keep", "metadata": dict(same)},
              {"id": "fix", "metadata": changed_new}]

    ingest.refresh_metadata(collection, chunks, {"keep", "fix"})

    written = collection.updates[0][0]
    assert written == ["fix"]
