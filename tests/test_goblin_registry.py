"""Tests for app.core.goblin_registry."""

import pytest

from app.core.goblin_registry import (
    GoblinEntry,
    GoblinRegistry,
    registry,
)

EXPECTED_IDS = {
    "aeterna_skyeward",
    "ledgergut",
    "squarmish",
    "signor",
    "packrat_mcduffel",
    "patch",
    "grimscratch",
}


class TestRegistryReturnsAllGoblins:
    def test_get_all_returns_list(self):
        result = registry.get_all()
        assert isinstance(result, list)

    def test_get_all_contains_all_expected_ids(self):
        ids = {g.id for g in registry.get_all()}
        assert ids == EXPECTED_IDS

    def test_get_all_count_matches(self):
        assert len(registry.get_all()) == len(EXPECTED_IDS)


class TestGetById:
    def test_fetch_known_goblin(self):
        goblin = registry.get_by_id("ledgergut")
        assert goblin.id == "ledgergut"

    def test_fetch_each_goblin_by_id(self):
        for goblin_id in EXPECTED_IDS:
            goblin = registry.get_by_id(goblin_id)
            assert goblin.id == goblin_id

    def test_unknown_id_raises_key_error(self):
        with pytest.raises(KeyError):
            registry.get_by_id("not_a_real_goblin")


class TestNoDuplicateIds:
    def test_duplicate_id_raises_value_error(self):
        duplicate = GoblinEntry(
            id="ledgergut",
            display_name="Ledgergut Copy",
            species_or_class="Accounting Goblin",
            department="Finance & Accounting",
            mission="Duplicate mission.",
            owns=["receipt ingestion"],
            guiding_question="Why am I a duplicate?",
            status="planned",
            canonical_doc_path="docs/library/02-character-bible.md",
        )
        original = GoblinEntry(
            id="ledgergut",
            display_name="Ledgergut",
            species_or_class="Accounting Goblin",
            department="Finance & Accounting",
            mission="Original mission.",
            owns=["receipt ingestion"],
            guiding_question="Original question.",
            status="draft",
            canonical_doc_path="docs/goblins/GBO-001-ledgergut-workflow.md",
        )
        with pytest.raises(ValueError, match="Duplicate goblin id"):
            GoblinRegistry([original, duplicate])

    def test_registry_ids_are_unique(self):
        all_ids = [g.id for g in registry.get_all()]
        assert len(all_ids) == len(set(all_ids))


class TestEachGoblinOwnsAtLeastOneResponsibility:
    def test_all_goblins_have_owns(self):
        for goblin in registry.get_all():
            assert goblin.owns, f"'{goblin.id}' has no owned responsibilities"

    def test_empty_owns_raises_value_error(self):
        no_owns = GoblinEntry(
            id="blammo",
            display_name="Blammo",
            species_or_class="Mystery Goblin",
            department="Unknown",
            mission="Does nothing.",
            owns=[],
            guiding_question="Why am I here?",
            status="planned",
            canonical_doc_path="docs/library/02-character-bible.md",
        )
        with pytest.raises(ValueError, match="must own at least one responsibility"):
            GoblinRegistry([no_owns])


class TestGoblinEntryFields:
    def test_all_required_fields_present(self):
        required_fields = {
            "id",
            "display_name",
            "species_or_class",
            "department",
            "mission",
            "owns",
            "guiding_question",
            "status",
            "canonical_doc_path",
        }
        for goblin in registry.get_all():
            for field in required_fields:
                assert hasattr(goblin, field), (
                    f"'{goblin.id}' missing field '{field}'"
                )
                assert getattr(goblin, field) not in (None, "", []), (
                    f"'{goblin.id}' has empty value for '{field}'"
                )

    def test_goblin_entries_are_immutable(self):
        goblin = registry.get_by_id("ledgergut")
        with pytest.raises((AttributeError, TypeError)):
            goblin.id = "changed"  # type: ignore[misc]
