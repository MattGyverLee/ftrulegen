"""Unit tests for model classes"""

import unittest
import sys
from pathlib import Path

# Ensure src-py is in the path
src_py = Path(__file__).parent.parent / "src-py"
if str(src_py) not in sys.path:
    sys.path.insert(0, str(src_py))

from src_py.model.enums import (
    AffixType, HeadValue, OverwriteRulesValue,
    PermutationsValue, PhraseType, ValidFeatureType
)
from src_py.model.feature import Feature
from src_py.model.category import Category
from src_py.model.affix import Affix
from src_py.model.word import Word
from src_py.model.phrase import Phrase
from src_py.model.source_target import Source, Target
from src_py.model.flex_trans_rule import FLExTransRule
from src_py.model.flex_trans_rule_generator import FLExTransRuleGenerator


class TestEnums(unittest.TestCase):
    """Test enum classes."""

    def test_affix_type_values(self):
        """Test AffixType enum values."""
        self.assertEqual(AffixType.prefix.value, "prefix")
        self.assertEqual(AffixType.suffix.value, "suffix")

    def test_head_value_values(self):
        """Test HeadValue enum values."""
        self.assertEqual(HeadValue.yes.value, "yes")
        self.assertEqual(HeadValue.no.value, "no")

    def test_phrase_type_values(self):
        """Test PhraseType enum values."""
        self.assertEqual(PhraseType.source.value, "source")
        self.assertEqual(PhraseType.target.value, "target")

    def test_permutations_value(self):
        """Test PermutationsValue enum values."""
        self.assertEqual(PermutationsValue.no.value, "no")
        self.assertEqual(PermutationsValue.with_head.value, "with_head")
        self.assertEqual(PermutationsValue.not_head.value, "not_head")


class TestFeature(unittest.TestCase):
    """Test Feature model class."""

    def test_feature_creation(self):
        """Test creating a feature."""
        feature = Feature(label="gender", value="masculine")
        self.assertEqual(feature.label, "gender")
        self.assertEqual(feature.value, "masculine")
        self.assertEqual(feature.match, "")
        self.assertEqual(feature.ranking, 0)

    def test_feature_get_match_or_value(self):
        """Test get_match_or_value method."""
        feature = Feature(label="gender", value="masculine", match="α")
        self.assertEqual(feature.get_match_or_value(), "α")

        feature2 = Feature(label="number", value="sg")
        self.assertEqual(feature2.get_match_or_value(), "sg")

    def test_feature_with_ranking(self):
        """Test feature with ranking."""
        feature = Feature(label="gender", value="feminine", ranking=1)
        self.assertEqual(feature.ranking, 1)


class TestCategory(unittest.TestCase):
    """Test Category model class."""

    def test_category_creation(self):
        """Test creating a category."""
        cat = Category(name="n")
        self.assertEqual(cat.name, "n")

    def test_category_html_generation(self):
        """Test category HTML generation."""
        cat = Category(name="n")
        cat.identifier = 3
        html = cat.produce_html()
        self.assertIn("class=\"category\"", html)
        self.assertIn("id=\"c.3\"", html)
        self.assertIn("onmousedown", html)


class TestAffix(unittest.TestCase):
    """Test Affix model class."""

    def test_affix_creation(self):
        """Test creating an affix."""
        affix = Affix(affix_type=AffixType.prefix)
        self.assertEqual(affix.affix_type, AffixType.prefix)
        self.assertEqual(len(affix.features), 0)

    def test_affix_with_features(self):
        """Test affix with features."""
        affix = Affix(affix_type=AffixType.suffix)
        feature = Feature(label="gender", value="feminine")
        affix.features.append(feature)
        self.assertEqual(len(affix.features), 1)


class TestWord(unittest.TestCase):
    """Test Word model class."""

    def test_word_creation(self):
        """Test creating a word."""
        word = Word(word_id="1", word_category="n")
        self.assertEqual(word.word_id, "1")
        self.assertEqual(word.word_category, "n")
        self.assertEqual(word.head, HeadValue.no)

    def test_word_with_category_constituent(self):
        """Test word category constituent creation."""
        word = Word(word_id="1", word_category="v")
        self.assertIsNotNone(word.category_constituent)
        self.assertEqual(word.category_constituent.name, "v")

    def test_word_mark_as_head(self):
        """Test marking word as head."""
        word = Word(word_id="1")
        word.head = HeadValue.yes
        self.assertEqual(word.head, HeadValue.yes)

    def test_word_with_features(self):
        """Test word with features."""
        word = Word(word_id="1")
        feature = Feature(label="number", value="sg")
        word.features.append(feature)
        self.assertEqual(len(word.features), 1)

    def test_word_with_affixes(self):
        """Test word with affixes."""
        word = Word(word_id="1")
        prefix = Affix(affix_type=AffixType.prefix)
        word.affixes.append(prefix)
        self.assertEqual(len(word.affixes), 1)


class TestPhrase(unittest.TestCase):
    """Test Phrase model class."""

    def test_phrase_creation(self):
        """Test creating a phrase."""
        phrase = Phrase(phrase_type=PhraseType.source)
        self.assertEqual(phrase.phrase_type, PhraseType.source)
        self.assertEqual(len(phrase.words), 0)

    def test_phrase_insert_word(self):
        """Test inserting a word into a phrase."""
        phrase = Phrase()
        word = phrase.insert_new_word_at(0)
        self.assertEqual(len(phrase.words), 1)
        self.assertEqual(word.word_id, "1")

    def test_phrase_get_new_word_id(self):
        """Test getting next word ID."""
        phrase = Phrase()
        phrase.insert_new_word_at(0)
        phrase.insert_new_word_at(1)
        next_id = phrase.get_id_of_newly_added_word()
        self.assertEqual(next_id, "3")

    def test_phrase_mark_word_as_head(self):
        """Test marking a word as head in a phrase."""
        phrase = Phrase()
        word1 = phrase.insert_new_word_at(0)
        word2 = phrase.insert_new_word_at(1)

        phrase.mark_word_as_head(word1)
        self.assertEqual(word1.head, HeadValue.yes)
        self.assertEqual(word2.head, HeadValue.no)

    def test_phrase_swap_words(self):
        """Test swapping word positions."""
        phrase = Phrase()
        word1 = phrase.insert_new_word_at(0)
        word2 = phrase.insert_new_word_at(1)

        phrase.swap_position_of_words(0, 1)
        self.assertEqual(phrase.words[0], word2)
        self.assertEqual(phrase.words[1], word1)

    def test_phrase_change_word_id(self):
        """Test changing a word's ID."""
        phrase = Phrase()
        word = phrase.insert_new_word_at(0)
        phrase.change_id_of_word(0, "1", "5")
        self.assertEqual(phrase.words[0].word_id, "5")


class TestRule(unittest.TestCase):
    """Test FLExTransRule model class."""

    def test_rule_creation(self):
        """Test creating a rule."""
        source = Source()
        target = Target()
        rule = FLExTransRule(name="TestRule", source=source, target=target)

        self.assertEqual(rule.name, "TestRule")
        self.assertEqual(rule.source.phrase_type, PhraseType.source)
        self.assertEqual(rule.target.phrase_type, PhraseType.target)


class TestRuleGenerator(unittest.TestCase):
    """Test FLExTransRuleGenerator model class."""

    def test_generator_creation(self):
        """Test creating a rule generator."""
        gen = FLExTransRuleGenerator()
        self.assertEqual(len(gen.flex_trans_rules), 0)
        self.assertEqual(gen.overwrite_rules, OverwriteRulesValue.no)

    def test_generator_duplicate_rule(self):
        """Test duplicating a rule."""
        gen = FLExTransRuleGenerator()
        source = Source()
        target = Target()
        rule = FLExTransRule(name="Rule1", source=source, target=target)
        gen.flex_trans_rules.append(rule)

        gen.duplicate_rule(0)
        self.assertEqual(len(gen.flex_trans_rules), 2)


if __name__ == "__main__":
    unittest.main()
