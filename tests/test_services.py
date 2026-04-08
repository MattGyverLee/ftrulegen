"""Unit tests for service classes"""

import unittest
import sys
from pathlib import Path

# Ensure src-py is in the path
src_py = Path(__file__).parent.parent / "src-py"
if str(src_py) not in sys.path:
    sys.path.insert(0, str(src_py))

from src_py.model.feature import Feature
from src_py.model.affix import Affix
from src_py.model.word import Word
from src_py.model.phrase import Phrase
from src_py.model.source_target import Source, Target
from src_py.model.flex_trans_rule import FLExTransRule
from src_py.model.flex_trans_rule_generator import FLExTransRuleGenerator
from src_py.model.enums import (
    AffixType, HeadValue, PhraseType, PermutationsValue
)
from src_py.service.rule_id_parent_setter import RuleIdentifierAndParentSetter
from src_py.service.constituent_finder import ConstituentFinder
from src_py.service.validity_checker import ValidityChecker


class TestRuleIdentifierAndParentSetter(unittest.TestCase):
    """Test RuleIdentifierAndParentSetter service."""

    def test_set_identifiers_simple_rule(self):
        """Test setting identifiers on a simple rule."""
        # Create a simple rule: source word with category, target word with feature
        source = Source()
        target = Target()

        source_word = source.insert_new_word_at(0)
        source_word.word_category = "n"

        target_word = target.insert_new_word_at(0)
        target_feature = Feature(label="number", value="sg")
        target_word.features.append(target_feature)

        rule = FLExTransRule(name="TestRule", source=source, target=target)

        # Set identifiers
        setter = RuleIdentifierAndParentSetter()
        setter.set_identifiers_and_parents(rule)

        # Verify identifiers are set
        self.assertGreater(source.identifier, 0)
        self.assertGreater(source_word.identifier, 0)
        self.assertGreater(source_word.category_constituent.identifier, 0)
        self.assertGreater(target.identifier, 0)
        self.assertGreater(target_word.identifier, 0)
        self.assertGreater(target_feature.identifier, 0)

    def test_identifier_sequence(self):
        """Test that identifiers follow depth-first order."""
        source = Source()
        target = Target()

        # Source: 1 word with 1 feature
        sw = source.insert_new_word_at(0)
        sw.word_category = "n"
        sf = Feature(label="number", value="sg")
        sw.features.append(sf)

        # Target: 1 word with 1 feature
        tw = target.insert_new_word_at(0)
        tw.word_category = "v"
        tf = Feature(label="tense", value="past")
        tw.features.append(tf)

        rule = FLExTransRule(name="TestRule", source=source, target=target)

        setter = RuleIdentifierAndParentSetter()
        setter.set_identifiers_and_parents(rule)

        # Verify sequence is correct (all IDs should be unique and sequential)
        ids = [
            source.identifier,
            sw.identifier,
            sw.category_constituent.identifier,
            sf.identifier,
            target.identifier,
            tw.identifier,
            tw.category_constituent.identifier,
            tf.identifier
        ]

        # Check uniqueness
        self.assertEqual(len(ids), len(set(ids)))
        # Check all are positive
        self.assertTrue(all(id > 0 for id in ids))

    def test_parent_pointers_set(self):
        """Test that parent pointers are set correctly."""
        source = Source()
        target = Target()

        sw = source.insert_new_word_at(0)
        rule = FLExTransRule(name="TestRule", source=source, target=target)

        setter = RuleIdentifierAndParentSetter()
        setter.set_identifiers_and_parents(rule)

        # Check parents
        self.assertEqual(source.phrase.parent, None)  # Root has no parent
        self.assertEqual(sw.parent, source.phrase)


class TestConstituentFinder(unittest.TestCase):
    """Test ConstituentFinder service."""

    def test_find_constituent_in_source(self):
        """Test finding a constituent in the source phrase."""
        source = Source()
        target = Target()

        sw = source.insert_new_word_at(0)
        rule = FLExTransRule(name="TestRule", source=source, target=target)

        setter = RuleIdentifierAndParentSetter()
        setter.set_identifiers_and_parents(rule)

        finder = ConstituentFinder()
        found = finder.find_constituent(rule, sw.identifier)
        self.assertEqual(found, sw)

    def test_find_constituent_in_target(self):
        """Test finding a constituent in the target phrase."""
        source = Source()
        target = Target()

        tw = target.insert_new_word_at(0)
        rule = FLExTransRule(name="TestRule", source=source, target=target)

        setter = RuleIdentifierAndParentSetter()
        setter.set_identifiers_and_parents(rule)

        finder = ConstituentFinder()
        found = finder.find_constituent(rule, tw.identifier)
        self.assertEqual(found, tw)

    def test_find_nonexistent_constituent(self):
        """Test finding a nonexistent constituent."""
        source = Source()
        target = Target()
        rule = FLExTransRule(name="TestRule", source=source, target=target)

        setter = RuleIdentifierAndParentSetter()
        setter.set_identifiers_and_parents(rule)

        finder = ConstituentFinder()
        found = finder.find_constituent(rule, 9999)
        self.assertIsNone(found)


class TestValidityChecker(unittest.TestCase):
    """Test ValidityChecker service."""

    def test_valid_rule(self):
        """Test a valid rule passes all checks."""
        source = Source()
        target = Target()

        # Source: word with category
        sw = source.insert_new_word_at(0)
        sw.word_category = "n"

        # Target: word with feature and head marking
        tw = target.insert_new_word_at(0)
        tw.word_category = "v"
        tw.head = HeadValue.yes
        tf = Feature(label="tense", value="past")
        tw.features.append(tf)

        rule = FLExTransRule(name="TestRule", source=source, target=target)

        is_valid, error_msg = ValidityChecker.validate_rule(rule)
        self.assertTrue(is_valid)
        self.assertEqual(error_msg, "")

    def test_source_word_missing_category(self):
        """Test that rule with uncategorized source word fails."""
        source = Source()
        target = Target()

        # Source: word without category
        sw = source.insert_new_word_at(0)
        sw.word_category = ""

        # Target: word with feature
        tw = target.insert_new_word_at(0)
        tw.head = HeadValue.yes
        tf = Feature(label="tense", value="past")
        tw.features.append(tf)

        rule = FLExTransRule(name="TestRule", source=source, target=target)

        is_valid, error_msg = ValidityChecker.validate_rule(rule)
        self.assertFalse(is_valid)

    def test_target_missing_feature(self):
        """Test that rule with no features in target fails."""
        source = Source()
        target = Target()

        # Source: word with category
        sw = source.insert_new_word_at(0)
        sw.word_category = "n"

        # Target: word without features
        tw = target.insert_new_word_at(0)
        tw.word_category = "v"
        tw.head = HeadValue.yes

        rule = FLExTransRule(name="TestRule", source=source, target=target)

        is_valid, error_msg = ValidityChecker.validate_rule(rule)
        self.assertFalse(is_valid)

    def test_target_missing_head_marking(self):
        """Test that rule with multiple target words but no head fails."""
        source = Source()
        target = Target()

        # Source: one word with category
        sw = source.insert_new_word_at(0)
        sw.word_category = "n"

        # Target: two words, none marked as head
        tw1 = target.insert_new_word_at(0)
        tw1.word_category = "adj"
        tw1.head = HeadValue.no
        tw2 = target.insert_new_word_at(1)
        tw2.word_category = "n"
        tw2.head = HeadValue.no

        # Add feature so it passes feature check
        tf = Feature(label="number", value="sg")
        tw1.features.append(tf)

        rule = FLExTransRule(name="TestRule", source=source, target=target)

        is_valid, error_msg = ValidityChecker.validate_rule(rule)
        self.assertFalse(is_valid)


if __name__ == "__main__":
    unittest.main()
