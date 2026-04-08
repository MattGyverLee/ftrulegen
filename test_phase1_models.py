#!/usr/bin/env python3
"""
Phase 1 Model Layer Tests

Tests all constants, enums, and model classes to verify they work correctly
before proceeding to Phase 2+ services.
"""

import sys
from pathlib import Path

# Add src_py to path
sys.path.insert(0, str(Path(__file__).parent / "src_py"))

from src_py import constants
from src_py.model.enums import (
    AffixType, HeadValue, OverwriteRulesValue, PermutationsValue,
    PhraseType, ValidFeatureType
)
from src_py.model.rule_constituent import RuleConstituent
from src_py.model.feature import Feature
from src_py.model.category import Category
from src_py.model.word import Word
from src_py.model.affix import Affix
from src_py.model.phrase import Phrase
from src_py.model.source_target import Source, Target
from src_py.model.flex_trans_rule import FLExTransRule
from src_py.model.flex_trans_rule_generator import FLExTransRuleGenerator
from src_py.model.disjoint_feature_set import DisjointFeatureSet, DisjointFeatureValuePairing
from src_py.flexmodel.flex_feature import FLExFeature, FLExFeatureValue
from src_py.flexmodel.flex_category import FLExCategory, ValidFeature
from src_py.flexmodel.flex_data import FLExData, SourceFLExData, TargetFLExData


def test_constants():
    """Test constants are properly defined."""
    print("[TEST] Constants...")
    assert constants.VERSION_NUMBER == "1.6.0"
    assert len(constants.GREEK_VARIABLES) == 12
    assert constants.GREEK_VARIABLES[0] == "α"
    assert constants.DISJOINT_NUMBER == "number"
    assert constants.DISJOINT_PL == "pl"
    assert constants.DISJOINT_SG == "sg"
    print("  [OK] Constants initialized correctly")


def test_enums():
    """Test all enums."""
    print("[TEST] Enums...")

    # AffixType
    assert AffixType.prefix.value == "prefix"
    assert AffixType.suffix.value == "suffix"

    # HeadValue
    assert HeadValue.yes.value == "yes"
    assert HeadValue.no.value == "no"

    # OverwriteRulesValue
    assert OverwriteRulesValue.yes.value == "yes"
    assert OverwriteRulesValue.no.value == "no"

    # PermutationsValue
    assert PermutationsValue.no.value == "no"
    assert PermutationsValue.not_head.value == "not_head"
    assert PermutationsValue.with_head.value == "with_head"

    # PhraseType
    assert PhraseType.source.value == "source"
    assert PhraseType.target.value == "target"

    # ValidFeatureType
    assert ValidFeatureType.prefix.value == "prefix"
    assert ValidFeatureType.stem.value == "stem"
    assert ValidFeatureType.suffix.value == "suffix"

    print("  [OK] All enums have correct string values")


def test_rule_constituent():
    """Test base RuleConstituent class."""
    print("[TEST] RuleConstituent base class...")

    rc = RuleConstituent()
    assert rc.identifier == 0
    assert rc.parent is None

    # Test produce_span
    span = rc.produce_span("myclass", "x")
    assert 'class="myclass"' in span
    assert 'id="x.0"' in span
    assert 'onmousedown="toApp' in span

    # Test find_constituent
    assert rc.find_constituent(0) is rc
    assert rc.find_constituent(999) is None

    print("  [OK] RuleConstituent works correctly")


def test_feature():
    """Test Feature class."""
    print("[TEST] Feature model...")

    f = Feature(label="gender", value="masculine", ranking=1)
    assert f.label == "gender"
    assert f.value == "masculine"
    assert f.ranking == 1
    assert f.match == ""

    # Test get_match_or_value
    assert f.get_match_or_value() == "masculine"

    f_with_match = Feature(label="agreement", match="α", value="default")
    assert f_with_match.get_match_or_value() == "α"

    # Test duplicate
    f_dup = f.duplicate()
    assert f_dup.label == f.label
    assert f_dup.value == f.value
    assert f_dup.ranking == f.ranking
    assert f_dup is not f

    print("  [OK] Feature class works correctly")


def test_category():
    """Test Category (runtime) class."""
    print("[TEST] Category model...")

    cat = Category(name="noun")
    assert cat.name == "noun"

    # Test produce_html for source
    html = cat.produce_html()
    assert 'class="category"' in html
    assert 'id="c.' in html
    assert 'cat:noun' in html

    # Test produce_html_target
    html_tgt = cat.produce_html_target(word_identifier=42)
    assert 'class="categorytgt"' in html_tgt
    assert 'id="w.42"' in html_tgt
    assert 'onclick=' in html_tgt  # note: onclick not onmousedown
    assert 'cat:noun' in html_tgt

    print("  [OK] Category class works correctly")


def test_affix():
    """Test Affix class."""
    print("[TEST] Affix model...")

    affix = Affix(affix_type=AffixType.prefix)
    assert affix.affix_type == AffixType.prefix
    assert len(affix.features) == 0

    # Add a feature
    feat = Feature(label="tense", value="past")
    affix.features.append(feat)
    feat.parent = affix

    # Test duplicate
    dup = affix.duplicate()
    assert dup.affix_type == affix.affix_type
    assert len(dup.features) == 1
    assert dup.features[0] is not feat

    print("  [OK] Affix class works correctly")


def test_word():
    """Test Word class."""
    print("[TEST] Word model...")

    word = Word(word_id="1", word_category="noun", head=HeadValue.yes)
    assert word.word_id == "1"
    assert word.word_category == "noun"
    assert word.head == HeadValue.yes
    assert word.category_constituent is not None
    assert word.category_constituent.name == "noun"

    # Add a feature
    feat = Feature(label="gender", value="masculine")
    word.features.append(feat)
    feat.parent = word

    # Test find_constituent
    assert word.find_constituent(word.identifier) is word

    # Test get_id_of_newly_added_word (static method logic)
    new_id = word.get_id_of_newly_added_word([])
    assert new_id == "1"

    word2 = Word(word_id="2", word_category="verb")
    new_id = word.get_id_of_newly_added_word([word, word2])
    assert new_id == "3"

    print("  [OK] Word class works correctly")


def test_phrase():
    """Test Phrase class."""
    print("[TEST] Phrase model...")

    phrase = Phrase(phrase_type=PhraseType.source)
    assert phrase.phrase_type == PhraseType.source
    assert len(phrase.words) == 0

    # Insert words
    w1 = phrase.insert_new_word_at(0)
    assert len(phrase.words) == 1
    assert w1.parent is phrase

    w2 = phrase.insert_new_word_at(1)
    assert len(phrase.words) == 2

    # Test swap
    phrase.swap_position_of_words(0, 1)
    assert phrase.words[0] is w2
    assert phrase.words[1] is w1

    # Test change_id_of_word
    phrase.change_id_of_word(0, "1", "99")
    assert phrase.words[0].word_id == "99"

    # Test find_constituent
    assert phrase.find_constituent(phrase.identifier) is phrase

    print("  [OK] Phrase class works correctly")


def test_source_target():
    """Test Source and Target classes."""
    print("[TEST] Source and Target models...")

    source = Source()
    assert source.phrase_type == PhraseType.source

    target = Target()
    assert target.phrase_type == PhraseType.target

    print("  [OK] Source and Target classes work correctly")


def test_flex_trans_rule():
    """Test FLExTransRule class."""
    print("[TEST] FLExTransRule model...")

    rule = FLExTransRule(name="TestRule", description="A test rule")
    assert rule.name == "TestRule"
    assert rule.description == "A test rule"
    assert isinstance(rule.source, Source)
    assert isinstance(rule.target, Target)

    # Add words to source
    word = rule.source.insert_new_word_at(0)
    assert rule.source.words[0] is word

    # Set parent pointers (normally done by RuleIdentifierAndParentSetter service)
    rule.source.parent = rule
    word.parent = rule.source

    # Test find_constituent with proper structure
    assert rule.find_constituent(rule.identifier) is rule
    # Set a custom identifier for testing
    word.identifier = 42
    assert rule.find_constituent(42) is word

    # Test duplicate
    dup = rule.duplicate()
    assert dup.name == "TestRule (duplicate)"
    assert dup is not rule
    assert len(dup.source.words) == len(rule.source.words)

    print("  [OK] FLExTransRule class works correctly")


def test_flex_trans_rule_generator():
    """Test FLExTransRuleGenerator class."""
    print("[TEST] FLExTransRuleGenerator model...")

    gen = FLExTransRuleGenerator()
    assert len(gen.flex_trans_rules) == 0
    assert gen.overwrite_rules == OverwriteRulesValue.no

    # Add a rule
    rule = FLExTransRule(name="Rule1")
    gen.flex_trans_rules.append(rule)

    # Test duplicate_rule
    gen.duplicate_rule(0)
    assert len(gen.flex_trans_rules) == 2
    assert gen.flex_trans_rules[0].name == "Rule1 (duplicate)"
    assert gen.flex_trans_rules[1].name == "Rule1"

    print("  [OK] FLExTransRuleGenerator class works correctly")


def test_disjoint_features():
    """Test disjoint feature classes."""
    print("[TEST] Disjoint feature models...")

    pairing = DisjointFeatureValuePairing(flex_feature_name="gender", co_feature_value="sg")
    assert pairing.flex_feature_name == "gender"
    assert pairing.co_feature_value == "sg"

    pairing_dup = pairing.duplicate()
    assert pairing_dup is not pairing
    assert pairing_dup.flex_feature_name == pairing.flex_feature_name

    dis_set = DisjointFeatureSet(name="number", co_feature_name="gender")
    assert dis_set.name == "number"
    assert dis_set.co_feature_name == "gender"

    dis_set.pairings.append(pairing)
    assert len(dis_set.pairings) == 1

    print("  [OK] Disjoint feature classes work correctly")


def test_flex_feature_value():
    """Test FLExFeatureValue class."""
    print("[TEST] FLExFeatureValue model...")

    val = FLExFeatureValue(abbreviation="sg")
    assert val.abbreviation == "sg"
    assert not FLExFeatureValue.is_greek("sg")

    val_greek = FLExFeatureValue(abbreviation="α")
    assert FLExFeatureValue.is_greek("α")
    assert val_greek.abbreviation in constants.GREEK_VARIABLES

    print("  [OK] FLExFeatureValue class works correctly")


def test_flex_feature():
    """Test FLExFeature class."""
    print("[TEST] FLExFeature model...")

    feat = FLExFeature(name="number")
    sg = FLExFeatureValue(abbreviation="sg")
    pl = FLExFeatureValue(abbreviation="pl")
    feat.values = [sg, pl]
    feat.__post_init__()

    assert feat.name == "number"
    assert len(feat.values) == 2
    assert sg.feature is feat
    assert pl.feature is feat

    # Test duplicate
    dup = feat.duplicate()
    assert dup.name == feat.name
    assert len(dup.values) == 2
    assert dup.values[0] is not sg

    print("  [OK] FLExFeature class works correctly")


def test_flex_category():
    """Test FLExCategory class."""
    print("[TEST] FLExCategory model...")

    cat = FLExCategory(abbreviation="noun")
    vf = ValidFeature(name="gender", valid_feature_type="prefix")
    cat.valid_features = [vf]

    assert cat.abbreviation == "noun"
    assert len(cat.valid_features) == 1
    assert cat.valid_features[0].name == "gender"

    print("  [OK] FLExCategory class works correctly")


def test_flex_data():
    """Test FLExData and sublclasses."""
    print("[TEST] FLExData models...")

    source_data = SourceFLExData(name="German")
    target_data = TargetFLExData(name="Swedish")

    # Add features
    feat = FLExFeature(name="number")
    feat.values = [
        FLExFeatureValue(abbreviation="sg"),
        FLExFeatureValue(abbreviation="pl")
    ]
    source_data.features = [feat]

    # Add categories
    cat = FLExCategory(abbreviation="noun")
    cat.valid_features = [ValidFeature(name="number", valid_feature_type="stem")]
    source_data.categories = [cat]

    # Test add_variable_values_to_features
    source_data.add_variable_values_to_features()
    assert len(source_data.features[0].values) == 2 + source_data.max_variables

    # Test FLExData root
    data = FLExData(source_data=source_data, target_data=target_data)
    assert data.source_data.name == "German"
    assert data.target_data.name == "Swedish"

    print("  [OK] FLExData classes work correctly")


def test_html_generation():
    """Test HTML generation methods."""
    print("[TEST] HTML generation...")

    # Create a simple rule
    rule = FLExTransRule(name="TestRule")

    # Add a word to source
    word = rule.source.insert_new_word_at(0)
    word.word_id = "1"
    word.word_category = "noun"
    word.head = HeadValue.yes

    # Add a feature
    feat = Feature(label="gender", value="masculine")
    word.features.append(feat)
    feat.parent = word

    # Generate HTML
    html = rule.source.produce_html()
    assert '<li>' in html
    assert 'class="tf-nc"' in html
    assert 'phrase' in html or 'Phrase' in html or '<span' in html

    print("  [OK] HTML generation works correctly")


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("PHASE 1 MODEL LAYER TESTS")
    print("="*70 + "\n")

    try:
        test_constants()
        test_enums()
        test_rule_constituent()
        test_feature()
        test_category()
        test_affix()
        test_word()
        test_phrase()
        test_source_target()
        test_flex_trans_rule()
        test_flex_trans_rule_generator()
        test_disjoint_features()
        test_flex_feature_value()
        test_flex_feature()
        test_flex_category()
        test_flex_data()
        test_html_generation()

        print("\n" + "="*70)
        print("[OK] ALL PHASE 1 TESTS PASSED")
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
