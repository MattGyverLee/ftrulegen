# Copyright (c) 2024-2026 SIL International
# This software is licensed under the LGPL, version 2.1 or later
# (http://www.gnu.org/licenses/lgpl-2.1.html)

import os
import pytest
from flextrans_rule_generator.model.rule_generator import FLExTransRuleGenerator
from flextrans_rule_generator.model.rule import FLExTransRule
from flextrans_rule_generator.model.word import HeadValue
from flextrans_rule_generator.model.affix import Affix
from flextrans_rule_generator.model.feature import Feature
from flextrans_rule_generator.service.validity_checker import ValidityChecker
from flextrans_rule_generator.service.xml_backend_provider import XmlBackEndProvider
from tests.conftest import TEST_DATA_DIR


@pytest.fixture
def setup():
    rule_generator = FLExTransRuleGenerator()
    provider = XmlBackEndProvider()
    file_path = os.path.join(TEST_DATA_DIR, "Ex1a_Def-Noun.xml")
    provider.load_data_from_file(file_path)
    rule_generator = provider.rule_generator
    rule = rule_generator.rules[0]
    checker = ValidityChecker()
    return checker, rule


def test_source_words_have_categories(setup):
    checker, rule = setup
    checker.rule = rule
    assert checker.check_source_words_have_categories() is True
    rule.source.phrase.words[0].delete_category()
    checker.rule = rule
    assert checker.check_source_words_have_categories() is False
    rule.source.phrase.words[1].delete_category()
    checker.rule = rule
    assert checker.check_source_words_have_categories() is False


def test_target_has_feature(setup):
    checker, rule = setup
    checker.rule = rule
    assert checker.check_target_has_feature() is True
    rule.target.phrase.words[0].features = []
    checker.rule = rule
    assert checker.check_target_has_feature() is True
    rule.target.phrase.words[1].features = []
    checker.rule = rule
    assert checker.check_target_has_feature() is False
    affix = Affix()
    rule.target.phrase.words[0].affixes.append(affix)
    checker.rule = rule
    assert checker.check_target_has_feature() is False
    feature = Feature()
    feature.label = "gender"
    feature.match = "m"
    affix.features.append(feature)
    rule.target.phrase.words[0].affixes.append(affix)
    checker.rule = rule
    assert checker.check_target_has_feature() is True


def test_target_word_marked_as_head(setup):
    checker, rule = setup
    checker.rule = rule
    assert checker.check_target_word_marked_as_head() is True
    rule.target.phrase.words[1].head = HeadValue.NO
    checker.rule = rule
    assert checker.check_target_word_marked_as_head() is False
