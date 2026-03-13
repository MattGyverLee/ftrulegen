# Copyright (c) 2024-2026 SIL International
# This software is licensed under the LGPL, version 2.1 or later
# (http://www.gnu.org/licenses/lgpl-2.1.html)

import os
import tempfile
import pytest
from flextrans_rule_generator.model.rule_generator import FLExTransRuleGenerator
from flextrans_rule_generator.model.rule import FLExTransRule
from flextrans_rule_generator.model.phrase import Phrase, PhraseType
from flextrans_rule_generator.model.word import Word, HeadValue
from flextrans_rule_generator.model.affix import Affix, AffixType
from flextrans_rule_generator.model.feature import Feature
from flextrans_rule_generator.model.source import Source
from flextrans_rule_generator.model.target import Target
from flextrans_rule_generator.service.xml_backend_provider import XmlBackEndProvider
from tests.conftest import TEST_DATA_DIR


def _check_word(word, word_id, category, head):
    assert word is not None
    assert word.id == word_id
    assert word.category == category
    assert word.head == head


def _check_feature(feature, label, match):
    assert feature is not None
    assert feature.label == label
    assert feature.match == match
    assert feature.get_match_or_value() == match
    assert feature.value == ""


def test_load_ex1a_def_noun():
    rule_generator = FLExTransRuleGenerator()
    provider = XmlBackEndProvider()
    provider.load_data_from_file(os.path.join(TEST_DATA_DIR, "Ex1a_Def-Noun.xml"))
    rule_generator = provider.rule_generator
    assert rule_generator is not None
    assert len(rule_generator.rules) == 1
    rule = rule_generator.rules[0]
    assert rule.name == "Definite - Noun"
    assert rule.description == "Ensure definite article gets gender of head noun."

    source = rule.source
    assert source is not None
    source_phrase = source.phrase
    assert source_phrase.type == PhraseType.SOURCE
    words = source_phrase.words
    assert len(words) == 2
    _check_word(words[0], "1", "def", HeadValue.NO)
    assert len(words[0].affixes) == 0
    assert len(words[0].features) == 0
    _check_word(words[1], "2", "n", HeadValue.NO)

    target = rule.target
    assert target is not None
    target_phrase = target.phrase
    assert target_phrase.type == PhraseType.TARGET
    words = target_phrase.words
    assert len(words) == 2
    _check_word(words[0], "1", "", HeadValue.NO)
    assert len(words[0].affixes) == 0
    assert len(words[0].features) == 1
    _check_feature(words[0].features[0], "gender", "\u03b1")
    _check_word(words[1], "2", "", HeadValue.YES)
    assert len(words[1].features) == 1
    _check_feature(words[1].features[0], "gender", "\u03b1")


def test_load_ex4b_indef_adj_noun():
    rule_generator = FLExTransRuleGenerator()
    provider = XmlBackEndProvider()
    provider.load_data_from_file(os.path.join(TEST_DATA_DIR, "Ex4b_Indef-Adj-Noun.xml"))
    rule_generator = provider.rule_generator
    assert rule_generator is not None
    assert len(rule_generator.rules) == 1
    rule = rule_generator.rules[0]
    assert rule.name == "Indefinite - Adjective - Noun"

    source_phrase = rule.source.phrase
    words = source_phrase.words
    assert len(words) == 3
    _check_word(words[0], "1", "indef", HeadValue.NO)
    _check_word(words[1], "2", "adj", HeadValue.NO)
    _check_word(words[2], "3", "n", HeadValue.NO)

    target_phrase = rule.target.phrase
    words = target_phrase.words
    assert len(words) == 3
    _check_word(words[0], "1", "", HeadValue.NO)
    assert len(words[0].affixes) == 2
    assert words[0].affixes[0].type == AffixType.SUFFIX
    _check_feature(words[0].affixes[0].features[0], "gender", "\u03b1")
    assert words[0].affixes[1].type == AffixType.SUFFIX
    _check_feature(words[0].affixes[1].features[0], "number", "\u03b2")

    _check_word(words[1], "3", "", HeadValue.YES)
    assert len(words[1].affixes) == 1
    assert len(words[1].features) == 1
    _check_feature(words[1].features[0], "gender", "\u03b1")
    _check_feature(words[1].affixes[0].features[0], "number", "\u03b2")

    _check_word(words[2], "2", "", HeadValue.NO)
    assert len(words[2].affixes) == 2
    _check_feature(words[2].affixes[0].features[0], "gender", "\u03b1")
    assert words[2].affixes[1].type == AffixType.PREFIX
    _check_feature(words[2].affixes[1].features[0], "number", "\u03b2")


def _make_word(word_id, category, head):
    w = Word()
    w.id = word_id
    w.category = category
    w.head = head
    return w


def _make_feature(label, match):
    f = Feature()
    f.label = label
    f.match = match
    return f


def _make_affix(affix_type, features):
    a = Affix()
    a.type = affix_type
    a.features = features
    return a


def _xml_elements_equal(e1, e2):
    """Recursively compare two XML elements for semantic equality."""
    if e1.tag != e2.tag:
        return False
    # Compare attributes (sorted for order independence)
    if sorted(e1.attrib.items()) != sorted(e2.attrib.items()):
        return False
    # Compare text content (stripped)
    t1 = (e1.text or "").strip()
    t2 = (e2.text or "").strip()
    if t1 != t2:
        return False
    # Compare children
    children1 = list(e1)
    children2 = list(e2)
    if len(children1) != len(children2):
        return False
    for c1, c2 in zip(children1, children2):
        if not _xml_elements_equal(c1, c2):
            return False
    return True


def test_save():
    import xml.etree.ElementTree as ET

    rule_generator = FLExTransRuleGenerator()
    rule = FLExTransRule()
    rule.name = "Indefinite - Adjective - Noun"
    rule.description = "Ensure indefinite article and adjective gets gender and number of head noun."

    source = Source()
    source_phrase = Phrase()
    source_phrase.words.append(_make_word("1", "indef", HeadValue.NO))
    source_phrase.words.append(_make_word("2", "adj", HeadValue.NO))
    source_phrase.words.append(_make_word("3", "n", HeadValue.NO))
    source.phrase = source_phrase
    rule.source = source

    target = Target()
    target_phrase = Phrase()
    w1 = _make_word("1", "", HeadValue.NO)
    w1.affixes.append(_make_affix(AffixType.SUFFIX, [_make_feature("gender", "\u03b1")]))
    w1.affixes.append(_make_affix(AffixType.SUFFIX, [_make_feature("number", "\u03b2")]))
    target_phrase.words.append(w1)

    w2 = _make_word("3", "", HeadValue.YES)
    w2.affixes.append(_make_affix(AffixType.SUFFIX, [_make_feature("number", "\u03b2")]))
    w2.features = [_make_feature("gender", "\u03b1")]
    target_phrase.words.append(w2)

    w3 = _make_word("2", "", HeadValue.NO)
    w3.affixes.append(_make_affix(AffixType.SUFFIX, [_make_feature("gender", "\u03b1")]))
    w3.affixes.append(_make_affix(AffixType.SUFFIX, [_make_feature("number", "\u03b2")]))
    target_phrase.words.append(w3)

    target.phrase = target_phrase
    rule.target = target
    rule_generator.rules.append(rule)

    provider = XmlBackEndProvider()
    provider.rule_generator = rule_generator
    with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as f:
        tmp_path = f.name
    try:
        provider.save_data_to_file(tmp_path)
        with open(tmp_path, "r", encoding="utf-8") as f:
            produced = f.read()
        expected_path = os.path.join(TEST_DATA_DIR, "RuleGenExpected.xml")
        with open(expected_path, "r", encoding="utf-8") as f:
            expected = f.read()
        # Compare XML semantically (attribute order and indentation may differ
        # between Python's serializer and Java's JAXB serializer)
        def _strip_preamble(xml_str):
            """Strip XML declaration and DOCTYPE to get just the root element."""
            import re
            xml_str = re.sub(r'<\?xml[^?]*\?>\s*', '', xml_str)
            xml_str = re.sub(r'<!DOCTYPE[^>]*>\s*', '', xml_str)
            return xml_str.strip()
        produced_root = ET.fromstring(_strip_preamble(produced))
        expected_root = ET.fromstring(_strip_preamble(expected))
        assert _xml_elements_equal(expected_root, produced_root), \
            f"XML content differs semantically.\nProduced:\n{produced}\n"
        # Also verify the file can be round-tripped (load back)
        provider2 = XmlBackEndProvider()
        provider2.load_data_from_file(tmp_path)
        assert len(provider2.rule_generator.rules) == 1
        assert provider2.rule_generator.rules[0].name == "Indefinite - Adjective - Noun"
    finally:
        os.unlink(tmp_path)


def test_load_non_existing_file():
    rule_generator = FLExTransRuleGenerator()
    provider = XmlBackEndProvider()
    missing_file = os.path.join(TEST_DATA_DIR, "IDoNotExist.xml")
    # Clean up if it exists from a previous test
    if os.path.exists(missing_file):
        os.unlink(missing_file)
    provider.load_data_from_file(missing_file)
    assert os.path.exists(missing_file)
    rule_generator = provider.rule_generator
    assert len(rule_generator.rules) == 1
    rule = rule_generator.rules[0]
    assert rule.name == ""
    assert rule.description == ""
    # Clean up
    if os.path.exists(missing_file):
        os.unlink(missing_file)
