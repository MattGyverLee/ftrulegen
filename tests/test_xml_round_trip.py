"""Unit tests for XML serialization round-trip"""

import unittest
import tempfile
import os
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
from src_py.model.disjoint_feature_set import DisjointFeatureSet, DisjointFeatureValuePairing
from src_py.model.enums import AffixType, HeadValue, PhraseType, OverwriteRulesValue
from src_py.service.xml_backend_provider import XMLBackEndProvider


class TestXMLRoundTrip(unittest.TestCase):
    """Test XML serialization and deserialization."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test files."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_save_and_load_empty_generator(self):
        """Test saving and loading an empty generator."""
        gen = FLExTransRuleGenerator()
        filepath = os.path.join(self.temp_dir, "empty.xml")

        XMLBackEndProvider.save_data_to_file(gen, filepath)
        loaded = XMLBackEndProvider.load_data_from_file(filepath)

        self.assertIsNotNone(loaded)
        self.assertEqual(len(loaded.flex_trans_rules), 0)

    def test_save_and_load_simple_rule(self):
        """Test saving and loading a simple rule."""
        gen = FLExTransRuleGenerator()

        # Create a simple rule
        source = Source()
        target = Target()

        sw = source.insert_new_word_at(0)
        sw.word_category = "n"

        tw = target.insert_new_word_at(0)
        tw.word_category = "v"
        tw.head = HeadValue.yes
        feature = Feature(label="tense", value="past")
        tw.features.append(feature)

        rule = FLExTransRule(name="TestRule", description="A test rule", source=source, target=target)
        gen.flex_trans_rules.append(rule)

        filepath = os.path.join(self.temp_dir, "simple.xml")
        XMLBackEndProvider.save_data_to_file(gen, filepath)
        loaded = XMLBackEndProvider.load_data_from_file(filepath)

        self.assertEqual(len(loaded.flex_trans_rules), 1)
        loaded_rule = loaded.flex_trans_rules[0]
        self.assertEqual(loaded_rule.name, "TestRule")
        self.assertEqual(loaded_rule.description, "A test rule")
        self.assertEqual(len(loaded_rule.source.words), 1)
        self.assertEqual(len(loaded_rule.target.words), 1)

    def test_save_and_load_complex_rule(self):
        """Test saving and loading a complex rule with affixes and features."""
        gen = FLExTransRuleGenerator()

        source = Source()
        target = Target()

        # Source: word with prefix and feature
        sw = source.insert_new_word_at(0)
        sw.word_category = "v"
        prefix = Affix(affix_type=AffixType.prefix)
        prefix_feature = Feature(label="number", value="pl")
        prefix.features.append(prefix_feature)
        sw.affixes.append(prefix)

        # Target: two words, one marked as head
        tw1 = target.insert_new_word_at(0)
        tw1.word_category = "adj"
        tw1.head = HeadValue.yes
        tw1_feature = Feature(label="gender", value="masculine")
        tw1.features.append(tw1_feature)

        tw2 = target.insert_new_word_at(1)
        tw2.word_category = "n"
        tw2.head = HeadValue.no
        tw2_feature = Feature(label="number", value="pl")
        tw2.features.append(tw2_feature)

        rule = FLExTransRule(name="ComplexRule", source=source, target=target)
        gen.flex_trans_rules.append(rule)

        filepath = os.path.join(self.temp_dir, "complex.xml")
        XMLBackEndProvider.save_data_to_file(gen, filepath)
        loaded = XMLBackEndProvider.load_data_from_file(filepath)

        self.assertEqual(len(loaded.flex_trans_rules), 1)
        loaded_rule = loaded.flex_trans_rules[0]
        self.assertEqual(len(loaded_rule.source.words), 1)
        self.assertEqual(len(loaded_rule.target.words), 2)
        self.assertEqual(len(loaded_rule.source.words[0].affixes), 1)

    def test_save_and_load_with_disjoint_features(self):
        """Test saving and loading with disjoint feature sets."""
        gen = FLExTransRuleGenerator()

        # Add a simple rule
        source = Source()
        target = Target()

        sw = source.insert_new_word_at(0)
        sw.word_category = "n"

        tw = target.insert_new_word_at(0)
        tw.head = HeadValue.yes
        tw.features.append(Feature(label="number", value="sg"))

        rule = FLExTransRule(name="Rule1", source=source, target=target)
        gen.flex_trans_rules.append(rule)

        # Add disjoint feature set
        disjoint = DisjointFeatureSet(
            name="Number",
            language=PhraseType.target,
            co_feature_name="number"
        )
        disjoint.pairings.append(DisjointFeatureValuePairing(
            flex_feature_name="number",
            co_feature_value="sg"
        ))
        gen.disjoint_features.append(disjoint)

        filepath = os.path.join(self.temp_dir, "disjoint.xml")
        XMLBackEndProvider.save_data_to_file(gen, filepath)
        loaded = XMLBackEndProvider.load_data_from_file(filepath)

        self.assertEqual(len(loaded.disjoint_features), 1)
        loaded_disjoint = loaded.disjoint_features[0]
        self.assertEqual(loaded_disjoint.name, "Number")
        self.assertEqual(len(loaded_disjoint.pairings), 1)

    def test_overwrite_rules_setting(self):
        """Test that overwrite_rules setting is preserved."""
        gen = FLExTransRuleGenerator()
        gen.overwrite_rules = OverwriteRulesValue.yes

        # Add a simple rule
        source = Source()
        target = Target()

        sw = source.insert_new_word_at(0)
        sw.word_category = "n"

        tw = target.insert_new_word_at(0)
        tw.head = HeadValue.yes
        tw.features.append(Feature(label="number", value="sg"))

        rule = FLExTransRule(name="Rule1", source=source, target=target)
        gen.flex_trans_rules.append(rule)

        filepath = os.path.join(self.temp_dir, "overwrite.xml")
        XMLBackEndProvider.save_data_to_file(gen, filepath)
        loaded = XMLBackEndProvider.load_data_from_file(filepath)

        self.assertEqual(loaded.overwrite_rules, OverwriteRulesValue.yes)


if __name__ == "__main__":
    unittest.main()
