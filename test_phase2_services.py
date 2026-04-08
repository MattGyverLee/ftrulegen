#!/usr/bin/env python3
"""
Phase 2 Service Layer Tests

Tests services that handle business logic (no Qt dependency).
Includes: RuleIdentifierAndParentSetter, ConstituentFinder, ValidityChecker
"""

import sys
from pathlib import Path
import tempfile

# Add src_py to path
sys.path.insert(0, str(Path(__file__).parent / "src_py"))

from src_py.model.flex_trans_rule import FLExTransRule
from src_py.model.source_target import Source, Target
from src_py.model.enums import HeadValue, PermutationsValue
from src_py.model.feature import Feature
from src_py.service.rule_id_parent_setter import RuleIdentifierAndParentSetter
from src_py.service.constituent_finder import ConstituentFinder
from src_py.service.validity_checker import ValidityChecker
from src_py.service.xml_backend_provider import XMLBackEndProvider


def test_rule_id_parent_setter():
    """Test RuleIdentifierAndParentSetter assigns correct ID sequence."""
    print("[TEST] RuleIdentifierAndParentSetter...")

    # Create a simple rule
    rule = FLExTransRule(name="TestRule")

    # Add words to source
    w1 = rule.source.insert_new_word_at(0)
    w1.word_id = "1"
    w1.word_category = "noun"

    w2 = rule.source.insert_new_word_at(1)
    w2.word_id = "2"
    w2.word_category = "verb"

    # Add features to first word
    feat = Feature(label="gender", value="masculine")
    w1.features.append(feat)

    # Add words to target
    tw1 = rule.target.insert_new_word_at(0)
    tw1.word_id = "1"
    tw1.word_category = "noun"
    tw1.head = HeadValue.yes

    # Set identifiers and parents
    setter = RuleIdentifierAndParentSetter()
    setter.set_identifiers_and_parents(rule)

    # Check that identifiers were assigned correctly
    # Source phrase should get ID 1
    assert rule.source.identifier == 1, f"Source phrase ID should be 1, got {rule.source.identifier}"

    # Source word 1 should get ID 2
    assert w1.identifier == 2, f"Source word 1 ID should be 2, got {w1.identifier}"

    # Source word 1's category should get ID 3
    assert w1.category_constituent.identifier == 3, f"Category ID should be 3, got {w1.category_constituent.identifier}"

    # Feature should get ID 4
    assert feat.identifier == 4, f"Feature ID should be 4, got {feat.identifier}"

    # Source word 2 should get ID 5
    assert w2.identifier == 5, f"Source word 2 ID should be 5, got {w2.identifier}"

    # Target phrase ID should be greater than all source IDs
    target_start = 6 + w2.affixes.__len__()  # Account for any affixes
    assert rule.target.identifier > rule.source.identifier, "Target phrase ID should be > source phrase ID"

    # Check parent pointers
    assert rule.source.parent is rule
    assert rule.target.parent is rule
    assert w1.parent is rule.source
    assert w2.parent is rule.source
    assert tw1.parent is rule.target
    assert feat.parent is w1

    print("  [OK] RuleIdentifierAndParentSetter works correctly")


def test_constituent_finder():
    """Test ConstituentFinder locates constituents by ID."""
    print("[TEST] ConstituentFinder...")

    rule = FLExTransRule(name="TestRule")

    # Add words
    w1 = rule.source.insert_new_word_at(0)
    w1.word_id = "1"
    w1.word_category = "noun"

    tw1 = rule.target.insert_new_word_at(0)
    tw1.word_id = "1"
    tw1.word_category = "verb"
    tw1.head = HeadValue.yes

    # Set IDs
    setter = RuleIdentifierAndParentSetter()
    setter.set_identifiers_and_parents(rule)

    # Test finding by ID
    finder = ConstituentFinder()

    found_source = finder.find_constituent(rule, rule.source.identifier)
    assert found_source is rule.source, "Should find source phrase"

    found_word = finder.find_constituent(rule, w1.identifier)
    assert found_word is w1, "Should find source word"

    found_target = finder.find_constituent(rule, rule.target.identifier)
    assert found_target is rule.target, "Should find target phrase"

    found_tword = finder.find_constituent(rule, tw1.identifier)
    assert found_tword is tw1, "Should find target word"

    not_found = finder.find_constituent(rule, 99999)
    assert not_found is None, "Should return None for non-existent ID"

    print("  [OK] ConstituentFinder works correctly")


def test_validity_checker_categories():
    """Test ValidityChecker for source word categories."""
    print("[TEST] ValidityChecker - categories...")

    rule = FLExTransRule(name="TestRule")

    # Valid: word with category
    w1 = rule.source.insert_new_word_at(0)
    w1.word_id = "1"
    w1.word_category = "noun"

    is_valid, msg = ValidityChecker.check_source_words_have_categories(rule)
    assert is_valid, f"Should be valid: {msg}"

    # Invalid: word without category
    w2 = rule.source.insert_new_word_at(1)
    w2.word_id = "2"
    w2.word_category = ""  # Missing category

    is_valid, msg = ValidityChecker.check_source_words_have_categories(rule)
    assert not is_valid, "Should be invalid without category"
    assert "category" in msg.lower(), f"Error message should mention category: {msg}"

    print("  [OK] ValidityChecker categories check works correctly")


def test_validity_checker_features():
    """Test ValidityChecker for target features."""
    print("[TEST] ValidityChecker - features...")

    rule = FLExTransRule(name="TestRule")

    # Source
    w1 = rule.source.insert_new_word_at(0)
    w1.word_id = "1"
    w1.word_category = "noun"

    # Target (no features)
    tw1 = rule.target.insert_new_word_at(0)
    tw1.word_id = "1"
    tw1.word_category = "noun"

    is_valid, msg = ValidityChecker.check_target_has_feature(rule)
    assert not is_valid, "Should be invalid without features"
    assert "feature" in msg.lower(), f"Error should mention feature: {msg}"

    # Add feature to target
    feat = Feature(label="gender", value="masculine")
    tw1.features.append(feat)

    is_valid, msg = ValidityChecker.check_target_has_feature(rule)
    assert is_valid, f"Should be valid with feature: {msg}"

    print("  [OK] ValidityChecker features check works correctly")


def test_validity_checker_head():
    """Test ValidityChecker for head word marking."""
    print("[TEST] ValidityChecker - head word...")

    rule = FLExTransRule(name="TestRule")

    # Source
    w1 = rule.source.insert_new_word_at(0)
    w1.word_id = "1"
    w1.word_category = "noun"

    # Target with 1 word - no head required
    tw1 = rule.target.insert_new_word_at(0)
    tw1.word_id = "1"
    tw1.word_category = "noun"
    tw1.head = HeadValue.no

    is_valid, msg = ValidityChecker.check_target_word_marked_as_head(rule)
    assert is_valid, "Single word target doesn't need head marking"

    # Add second word to target
    tw2 = rule.target.insert_new_word_at(1)
    tw2.word_id = "2"
    tw2.word_category = "verb"
    tw2.head = HeadValue.no

    # Now head is required
    is_valid, msg = ValidityChecker.check_target_word_marked_as_head(rule)
    assert not is_valid, "Multi-word target needs head marking"

    # Mark one as head
    tw1.head = HeadValue.yes

    is_valid, msg = ValidityChecker.check_target_word_marked_as_head(rule)
    assert is_valid, "Should be valid with one head word"

    print("  [OK] ValidityChecker head word check works correctly")


def test_validity_checker_full():
    """Test ValidityChecker.validate_rule() with all checks."""
    print("[TEST] ValidityChecker - full validation...")

    rule = FLExTransRule(name="TestRule")

    # Valid setup
    w1 = rule.source.insert_new_word_at(0)
    w1.word_id = "1"
    w1.word_category = "noun"

    tw1 = rule.target.insert_new_word_at(0)
    tw1.word_id = "1"
    tw1.word_category = "noun"
    tw1.head = HeadValue.yes

    # Add feature to target
    feat = Feature(label="number", value="singular")
    tw1.features.append(feat)

    # Should pass all checks
    is_valid, msg = ValidityChecker.validate_rule(rule)
    assert is_valid, f"Should be valid: {msg}"

    # Remove category from source
    w1.word_category = ""
    is_valid, msg = ValidityChecker.validate_rule(rule)
    assert not is_valid, "Should fail without source category"

    # Restore and remove target feature
    w1.word_category = "noun"
    tw1.features.clear()
    is_valid, msg = ValidityChecker.validate_rule(rule)
    assert not is_valid, "Should fail without target feature"

    print("  [OK] ValidityChecker full validation works correctly")


def test_xml_backend_create_and_load():
    """Test XMLBackEndProvider save and load."""
    print("[TEST] XMLBackEndProvider - save/load...")

    # Create and save
    with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
        temp_file = f.name

    try:
        # Create a rule
        from src_py.model.flex_trans_rule_generator import FLExTransRuleGenerator

        gen = FLExTransRuleGenerator()
        rule = FLExTransRule(name="SaveTestRule", description="Test description")
        rule.create_permutations = PermutationsValue.with_head

        w1 = rule.source.insert_new_word_at(0)
        w1.word_id = "1"
        w1.word_category = "noun"

        tw1 = rule.target.insert_new_word_at(0)
        tw1.word_id = "1"
        tw1.word_category = "verb"
        tw1.head = HeadValue.yes

        gen.flex_trans_rules.append(rule)

        # Save
        XMLBackEndProvider.save_data_to_file(gen, temp_file)
        assert Path(temp_file).exists(), "File should be created"

        # Load
        loaded_gen = XMLBackEndProvider.load_data_from_file(temp_file)
        assert len(loaded_gen.flex_trans_rules) == 1, "Should load one rule"

        loaded_rule = loaded_gen.flex_trans_rules[0]
        assert loaded_rule.name == "SaveTestRule", "Name should be preserved"
        assert loaded_rule.description == "Test description", "Description should be preserved"
        assert len(loaded_rule.source.words) == 1, "Should have one source word"
        assert len(loaded_rule.target.words) == 1, "Should have one target word"

        # Check loaded word properties
        loaded_source_word = loaded_rule.source.words[0]
        assert loaded_source_word.word_id == "1", "Word ID should be preserved"
        assert loaded_source_word.word_category == "noun", "Word category should be preserved"

        loaded_target_word = loaded_rule.target.words[0]
        assert loaded_target_word.head == HeadValue.yes, "Head marking should be preserved"

        print("  [OK] XMLBackEndProvider save/load works correctly")

    finally:
        # Cleanup
        Path(temp_file).unlink(missing_ok=True)


def test_xml_backend_default_creation():
    """Test XMLBackEndProvider creates default file."""
    print("[TEST] XMLBackEndProvider - default creation...")

    with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=True) as f:
        temp_file = f.name  # File is deleted when context exits

    # Load from non-existent file - should create default
    loaded_gen = XMLBackEndProvider.load_data_from_file(temp_file)
    assert Path(temp_file).exists(), "File should be created"
    assert len(loaded_gen.flex_trans_rules) == 1, "Should have default rule"

    rule = loaded_gen.flex_trans_rules[0]
    assert rule.name == "Rule 1", "Default rule name"
    assert len(rule.source.words) == 1, "Default should have one word in source"
    assert len(rule.target.words) == 1, "Default should have one word in target"

    # Cleanup
    Path(temp_file).unlink(missing_ok=True)

    print("  [OK] XMLBackEndProvider default creation works correctly")


def main():
    """Run all Phase 2 tests."""
    print("\n" + "="*70)
    print("PHASE 2 SERVICE LAYER TESTS")
    print("="*70 + "\n")

    try:
        test_rule_id_parent_setter()
        test_constituent_finder()
        test_validity_checker_categories()
        test_validity_checker_features()
        test_validity_checker_head()
        test_validity_checker_full()
        test_xml_backend_create_and_load()
        test_xml_backend_default_creation()

        print("\n" + "="*70)
        print("[OK] ALL PHASE 2 TESTS PASSED")
        print("="*70 + "\n")
        return 0

    except AssertionError as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
