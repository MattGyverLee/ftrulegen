# Copyright (c) 2024-2026 SIL International
# This software is licensed under the LGPL, version 2.1 or later
# (http://www.gnu.org/licenses/lgpl-2.1.html)

import os
import pytest
from flextrans_rule_generator.model.rule_generator import FLExTransRuleGenerator
from flextrans_rule_generator.model.rule import FLExTransRule
from flextrans_rule_generator.model.phrase import Phrase, PhraseType
from flextrans_rule_generator.model.word import Word, HeadValue
from flextrans_rule_generator.model.affix import Affix, AffixType
from flextrans_rule_generator.model.category import Category
from flextrans_rule_generator.model.source import Source
from flextrans_rule_generator.model.target import Target
from flextrans_rule_generator.service.rule_identifier_setter import RuleIdentifierAndParentSetter
from tests.conftest import TEST_DATA_DIR


@pytest.fixture
def setup():
    rule_generator = FLExTransRuleGenerator()
    rule = FLExTransRule()
    rule.name = "Rule 1"
    rule_generator.rules.append(rule)

    source = rule.source
    source_phrase = source.phrase
    source_word = Word()
    source_word.id = "1"
    source_word.category = "Noun"
    source_word.category_constituent.name = "Noun"
    source_word.head = HeadValue.YES
    source_phrase.words.append(source_word)
    source_word2 = Word()
    source_word2.id = "2"
    source_word2.category = "Det"
    source_word2.category_constituent.name = "Det"
    source_word2.head = HeadValue.NO
    source_phrase.words.append(source_word2)
    source_phrase.parent = rule

    target = rule.target
    target_phrase = target.phrase
    target_word = Word()
    target_word.id = "1"
    target_word.category = "Det"
    target_word.head = HeadValue.NO
    target_phrase.words.append(target_word)
    target_word2 = Word()
    target_word2.id = "2"
    target_word2.category = "Noun"
    target_word2.head = HeadValue.YES
    target_phrase.words.append(target_word2)
    target_phrase.parent = rule

    source.parent = rule
    target.parent = rule

    return (rule_generator, rule, source_phrase, source_word, source_word2,
            target_phrase, target_word, target_word2)


def _set_rule_ids_and_parents(rule_generator):
    setter = RuleIdentifierAndParentSetter()
    setter.set_identifiers_and_parents(rule_generator.rules[0])


def test_delete_word_at(setup):
    _, _, source_phrase, *_ = setup
    assert len(source_phrase.words) == 2
    source_phrase.delete_word_at(-1)  # no-op
    assert len(source_phrase.words) == 2
    source_phrase.delete_word_at(2)  # no-op
    assert len(source_phrase.words) == 2
    source_phrase.delete_word_at(1)
    assert len(source_phrase.words) == 1
    assert source_phrase.words[0].id == "1"
    source_phrase.delete_word_at(0)
    assert len(source_phrase.words) == 0


def test_insert_word_at(setup):
    _, _, source_phrase, *_ = setup
    assert len(source_phrase.words) == 2
    word3 = Word()
    word3.id = "3"
    source_phrase.insert_word_at(word3, -1)  # no-op
    assert len(source_phrase.words) == 2
    source_phrase.insert_word_at(word3, 3)  # no-op
    assert len(source_phrase.words) == 2
    source_phrase.insert_word_at(word3, 1)
    assert len(source_phrase.words) == 3
    assert source_phrase.words[1].id == "3"
    word4 = Word()
    word4.id = "4"
    source_phrase.insert_word_at(word4, 0)
    assert len(source_phrase.words) == 4
    assert source_phrase.words[0].id == "4"
    word5 = Word()
    word5.id = "5"
    source_phrase.insert_word_at(word5, len(source_phrase.words))
    assert len(source_phrase.words) == 5
    assert source_phrase.words[4].id == "5"


def test_insert_new_word_at(setup):
    _, _, source_phrase, *_ = setup
    assert len(source_phrase.words) == 2
    source_phrase.insert_new_word_at(-1)  # no-op
    assert len(source_phrase.words) == 2
    source_phrase.insert_new_word_at(3)  # no-op
    assert len(source_phrase.words) == 2
    source_phrase.insert_new_word_at(1)
    assert len(source_phrase.words) == 3
    assert source_phrase.words[1].id == "3"
    source_phrase.insert_new_word_at(0)
    assert len(source_phrase.words) == 4
    assert source_phrase.words[0].id == "4"


def test_insert_new_word_at_non_sequential_ids(setup):
    _, _, source_phrase, source_word, source_word2, *_ = setup
    source_word.id = "2"
    source_word2.id = "3"
    assert len(source_phrase.words) == 2
    source_phrase.insert_new_word_at(0)
    assert len(source_phrase.words) == 3
    assert source_phrase.words[0].id == "1"
    source_phrase.insert_new_word_at(0)
    assert len(source_phrase.words) == 4
    assert source_phrase.words[0].id == "4"
    source_phrase.words[2].id = "5"
    source_phrase.insert_new_word_at(0)
    assert len(source_phrase.words) == 5
    assert source_phrase.words[0].id == "2"


def test_swap_position_of_words(setup):
    _, _, source_phrase, *_ = setup
    assert len(source_phrase.words) == 2
    source_phrase.swap_position_of_words(-1, 0)  # no-op
    assert len(source_phrase.words) == 2
    source_phrase.swap_position_of_words(2, 0)  # no-op
    source_phrase.swap_position_of_words(0, -1)  # no-op
    source_phrase.swap_position_of_words(0, 2)  # no-op

    source_phrase.swap_position_of_words(0, 1)
    assert source_phrase.words[0].id == "2"
    assert source_phrase.words[1].id == "1"
    source_phrase.swap_position_of_words(1, 0)
    assert source_phrase.words[0].id == "1"
    assert source_phrase.words[1].id == "2"


def test_change_id_of_word(setup):
    _, _, source_phrase, *_ = setup
    assert len(source_phrase.words) == 2
    source_phrase.change_id_of_word(-1, "1", "2")  # no-op
    assert source_phrase.words[0].id == "1"
    assert source_phrase.words[1].id == "2"
    source_phrase.change_id_of_word(2, "1", "2")  # no-op
    assert source_phrase.words[0].id == "1"
    source_phrase.change_id_of_word(0, "1", "2")
    assert source_phrase.words[0].id == "2"
    assert source_phrase.words[1].id == "1"
    source_phrase.change_id_of_word(0, "2", "1")
    assert source_phrase.words[0].id == "1"
    assert source_phrase.words[1].id == "2"


def test_mark_word_as_head(setup):
    _, _, source_phrase, source_word, source_word2, *_ = setup
    assert source_phrase.words[0].head == HeadValue.YES
    assert source_phrase.words[1].head == HeadValue.NO
    source_phrase.mark_word_as_head(source_word2)
    assert source_phrase.words[0].head == HeadValue.NO
    assert source_phrase.words[1].head == HeadValue.YES


def test_get_phrase_from_category(setup):
    rule_generator, _, source_phrase, source_word, *_ = setup
    _set_rule_ids_and_parents(rule_generator)
    cat = source_word.category_constituent
    phrase = cat.get_phrase()
    assert phrase is source_phrase


def test_get_features_in_use(setup):
    _, _, _, _, _, target_phrase, target_word, target_word2 = setup
    features_in_use = target_phrase.get_features_in_use()
    assert len(features_in_use) == 0

    target_word.insert_new_feature("gender", "m")
    features_in_use = target_phrase.get_features_in_use()
    assert len(features_in_use) == 1
    assert features_in_use[0].name == "gender"
    assert len(features_in_use[0].values) == 1
    assert features_in_use[0].values[0].abbreviation == "m"

    target_word.insert_new_feature("number", "sg")
    features_in_use = target_phrase.get_features_in_use()
    assert len(features_in_use) == 2
    assert features_in_use[0].name == "gender"
    assert features_in_use[1].name == "number"

    # Duplicate feature should not add a new entry
    target_word.insert_new_feature("gender", "m")
    features_in_use = target_phrase.get_features_in_use()
    assert len(features_in_use) == 2


def test_get_phrase_from_feature(setup):
    rule_generator, _, source_phrase, source_word, source_word2, *_ = setup
    word_feature = source_word.insert_new_feature("gender", "alpha")
    source_word2.insert_new_affix_at(AffixType.PREFIX, 0)
    affix = source_word2.affixes[0]
    affix_feature = affix.insert_new_feature("number", "beta")
    _set_rule_ids_and_parents(rule_generator)
    assert word_feature.get_phrase() is source_phrase
    assert affix_feature.get_phrase() is source_phrase


def test_get_category_of_word_with_id(setup):
    _, _, source_phrase, *_, target_phrase, _, _ = setup
    cat = source_phrase.get_category_of_word_with_id("1")
    assert cat is not None
    assert cat.name == "Noun"
    cat = target_phrase.get_category_of_word_with_id("1")
    assert cat is not None
    # Target word 1 has category "Det" but word 1 in source has "Noun"
    # getCategoryOfWordWithId looks at source word with same ID
    # Actually, let's check what the target word 1's category is
    assert cat.name == "Noun"  # It gets the source word's category
