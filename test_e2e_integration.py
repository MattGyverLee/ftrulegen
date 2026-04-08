#!/usr/bin/env python3
"""
End-to-End Integration Test - Phases 1-4

Tests that data model (Phase 1), flexmodel (Phase 2), services (Phase 2),
and HTML producer (Phase 3) all work together correctly.
"""

import sys
from pathlib import Path
import tempfile

# Add src_py to path
sys.path.insert(0, str(Path(__file__).parent / "src_py"))

from src_py.model.flex_trans_rule_generator import FLExTransRuleGenerator
from src_py.model.flex_trans_rule import FLExTransRule
from src_py.model.enums import HeadValue, PermutationsValue
from src_py.model.feature import Feature
from src_py.service.xml_backend_provider import XMLBackEndProvider
from src_py.service.rule_id_parent_setter import RuleIdentifierAndParentSetter
from src_py.service.constituent_finder import ConstituentFinder
from src_py.service.validity_checker import ValidityChecker
from src_py.service.web_page_producer import WebPageProducer


def test_e2e_create_save_load_validate_render():
    """Full end-to-end: create -> save -> load -> validate -> render."""
    print("[TEST] End-to-End Integration...")

    # ======== PHASE 1: CREATE MODEL ========
    print("  Creating model...")
    gen = FLExTransRuleGenerator()
    rule = FLExTransRule(
        name="E2E Test Rule",
        description="A complete end-to-end test rule",
        create_permutations=PermutationsValue.with_head
    )

    # Source: 2 words
    w1_src = rule.source.insert_new_word_at(0)
    w1_src.word_id = "1"
    w1_src.word_category = "adjective"

    w2_src = rule.source.insert_new_word_at(1)
    w2_src.word_id = "2"
    w2_src.word_category = "noun"

    # Target: 1 word with features
    w1_tgt = rule.target.insert_new_word_at(0)
    w1_tgt.word_id = "1"
    w1_tgt.word_category = "verb"
    w1_tgt.head = HeadValue.yes

    # Add features to target
    feat_tense = Feature(label="tense", value="past")
    w1_tgt.features.append(feat_tense)
    feat_tense.parent = w1_tgt

    feat_person = Feature(label="person", value="3sg", ranking=1)
    w1_tgt.features.append(feat_person)
    feat_person.parent = w1_tgt

    gen.flex_trans_rules.append(rule)

    # ======== PHASE 2: SAVE TO XML ========
    print("  Saving to XML...")
    with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
        temp_file = f.name

    try:
        XMLBackEndProvider.save_data_to_file(gen, temp_file)
        assert Path(temp_file).exists(), "XML file should be created"
        print(f"    Saved to {Path(temp_file).name}")

        # ======== PHASE 2: LOAD FROM XML ========
        print("  Loading from XML...")
        loaded_gen = XMLBackEndProvider.load_data_from_file(temp_file)
        loaded_rule = loaded_gen.flex_trans_rules[0]

        # Verify structure is preserved
        assert loaded_rule.name == "E2E Test Rule", "Rule name should match"
        assert len(loaded_rule.source.words) == 2, "Should have 2 source words"
        assert len(loaded_rule.target.words) == 1, "Should have 1 target word"

        loaded_w1_src = loaded_rule.source.words[0]
        loaded_w2_src = loaded_rule.source.words[1]
        loaded_w1_tgt = loaded_rule.target.words[0]

        assert loaded_w1_src.word_id == "1", "Source word 1 ID"
        assert loaded_w2_src.word_id == "2", "Source word 2 ID"
        assert loaded_w1_tgt.word_id == "1", "Target word 1 ID"
        assert loaded_w1_src.word_category == "adjective", "Source word 1 category"
        assert loaded_w1_tgt.word_category == "verb", "Target word category"
        assert loaded_w1_tgt.head == HeadValue.yes, "Target word marked as head"

        # ======== PHASE 3: VALIDATE ========
        print("  Validating rule...")
        is_valid, error = ValidityChecker.validate_rule(loaded_rule)
        assert is_valid, f"Rule should be valid: {error}"

        # ======== PHASE 3: SET IDENTIFIERS ========
        print("  Setting identifiers...")
        setter = RuleIdentifierAndParentSetter()
        setter.set_identifiers_and_parents(loaded_rule)

        # Check that identifiers are sequential
        assert loaded_rule.source.identifier == 1, "Source phrase ID should be 1"
        assert loaded_w1_src.identifier == 2, "Source word 1 ID should be 2"
        assert loaded_w2_src.identifier > loaded_w1_src.identifier, "Source word 2 ID > word 1 ID"
        assert loaded_rule.target.identifier > loaded_w2_src.identifier, "Target phrase ID > last source element"

        # ======== PHASE 3: FIND CONSTITUENTS ========
        print("  Testing constituent finder...")
        finder = ConstituentFinder()

        found_src = finder.find_constituent(loaded_rule, loaded_rule.source.identifier)
        assert found_src is loaded_rule.source, "Should find source phrase"

        found_word = finder.find_constituent(loaded_rule, loaded_w1_src.identifier)
        assert found_word is loaded_w1_src, "Should find source word"

        found_tgt = finder.find_constituent(loaded_rule, loaded_rule.target.identifier)
        assert found_tgt is loaded_rule.target, "Should find target phrase"

        found_features = [finder.find_constituent(loaded_rule, f.identifier)
                         for f in loaded_w1_tgt.features]
        assert all(found_features), "Should find all features"

        # ======== PHASE 4: PRODUCE HTML ========
        print("  Producing HTML...")
        producer = WebPageProducer()
        html = producer.produce_web_page(loaded_rule)

        # Verify HTML structure
        assert '<!DOCTYPE html' in html, "Should have DOCTYPE"
        assert '<html xmlns=' in html, "Should have html tag with namespace"
        assert '<head>' in html, "Should have head"
        assert '<body>' in html, "Should have body"
        assert '</body>' in html, "Should have closing body"
        assert '</html>' in html, "Should have closing html"

        # Verify CSS is embedded
        assert '<style>' in html, "Should have embedded CSS"
        assert 'treeflex' in html, "Should reference treeflex"
        assert 'rulegen' in html, "Should reference rulegen"

        # Verify JavaScript is present
        assert 'qrc:///qtwebchannel/qwebchannel.js' in html, "Should reference QWebChannel JS"
        assert 'function toApp' in html, "Should have toApp function"
        assert 'ftRuleGenApp' in html, "Should reference ftRuleGenApp"

        # Verify content is present
        assert 'E2E Test Rule' in html, "Rule name should be in title"
        assert 'word' in html.lower() or 'phrase' in html.lower(), "Should contain linguistic terms"

        # Verify onclick/onmousedown attributes
        assert 'onmousedown=' in html, "Should have onmousedown handlers (for right-click)"

        print("  [OK] HTML produced successfully")

        # ======== VERIFY COMPLETE INTEGRATION ========
        print("  Verifying complete integration...")

        # Count elements
        source_spans = html.count('id="w.')  # Source word spans
        target_spans = html.count('id="w.')  # Overlaps, but count is roughly right
        phrase_spans = html.count('id="p.')  # Phrase spans

        assert phrase_spans >= 2, "Should have at least 2 phrase spans (source, target)"
        assert source_spans >= 1, "Should have word spans"

        print("  [OK] All integration checks passed")

    finally:
        # Cleanup
        Path(temp_file).unlink(missing_ok=True)


def test_e2e_complex_grammar():
    """Test with more complex rule structure."""
    print("[TEST] Complex Grammar Tree...")

    rule = FLExTransRule(name="Complex Rule")

    # Source: 1 noun with prefix and suffix
    w_src = rule.source.insert_new_word_at(0)
    w_src.word_id = "1"
    w_src.word_category = "noun"

    # Add affixes
    from src_py.model.affix import Affix
    from src_py.model.enums import AffixType

    prefix = Affix(affix_type=AffixType.prefix)
    prefix_feat = Feature(label="aspect", value="perfective")
    prefix.features.append(prefix_feat)
    prefix_feat.parent = prefix
    w_src.affixes.append(prefix)
    prefix.parent = w_src

    suffix = Affix(affix_type=AffixType.suffix)
    suffix_feat = Feature(label="case", value="nominative")
    suffix.features.append(suffix_feat)
    suffix_feat.parent = suffix
    w_src.affixes.append(suffix)
    suffix.parent = w_src

    # Target: 1 verb with features
    w_tgt = rule.target.insert_new_word_at(0)
    w_tgt.word_id = "1"
    w_tgt.word_category = "verb"
    w_tgt.head = HeadValue.yes

    feat = Feature(label="mood", value="indicative", ranking=1)
    w_tgt.features.append(feat)
    feat.parent = w_tgt

    # Validate
    is_valid, error = ValidityChecker.validate_rule(rule)
    assert is_valid, f"Complex rule should be valid: {error}"

    # Produce HTML
    producer = WebPageProducer()
    html = producer.produce_web_page(rule)

    # Verify affix markers
    assert 'prefix' in html or 'Prefix' in html, "Should contain prefix"
    assert 'suffix' in html or 'Suffix' in html, "Should contain suffix"

    # Verify feature details
    assert 'aspect' in html or 'perfective' in html, "Should contain aspect feature"
    assert 'mood' in html or 'indicative' in html, "Should contain mood feature"

    print("  [OK] Complex grammar tree produced successfully")


def main():
    """Run all E2E tests."""
    print("\n" + "="*70)
    print("END-TO-END INTEGRATION TESTS (Phases 1-4)")
    print("="*70 + "\n")

    try:
        test_e2e_create_save_load_validate_render()
        test_e2e_complex_grammar()

        print("\n" + "="*70)
        print("[OK] ALL E2E TESTS PASSED")
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
