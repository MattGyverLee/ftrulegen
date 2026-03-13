# Copyright (c) 2024-2026 SIL International
# This software is licensed under the LGPL, version 2.1 or later
# (http://www.gnu.org/licenses/lgpl-2.1.html)

import pytest
from flextrans_rule_generator.model.word import Word, HeadValue
from flextrans_rule_generator.model.affix import Affix, AffixType
from flextrans_rule_generator.model.feature import Feature
from flextrans_rule_generator.model.category import Category


@pytest.fixture
def word():
    w = Word()
    w.id = "1"
    w.category = "Noun"
    w.category_constituent = Category("Noun")
    w.head = HeadValue.YES
    return w


def _create_two_affixes(word):
    word.insert_new_affix_at(AffixType.PREFIX, 0)
    word.insert_new_affix_at(AffixType.SUFFIX, 1)
    assert len(word.affixes) == 2
    assert word.affixes[0].type == AffixType.PREFIX
    assert word.affixes[1].type == AffixType.SUFFIX


def test_delete_category(word):
    assert word.category == "Noun"
    assert word.category_constituent is not None
    assert word.category_constituent.name == "Noun"
    word.delete_category()
    assert word.category == ""
    assert word.category_constituent is not None
    assert word.category_constituent.name == ""


def test_insert_category(word):
    word.delete_category()
    assert word.category == ""
    word.insert_category("verb")
    assert word.category == "verb"
    assert word.category_constituent is not None
    assert word.category_constituent.name == "verb"


def test_delete_affix_at(word):
    _create_two_affixes(word)
    word.delete_affix_at(0)
    assert len(word.affixes) == 1
    assert word.affixes[0].type == AffixType.SUFFIX

    word.insert_new_affix_at(AffixType.PREFIX, 1)
    assert len(word.affixes) == 2
    assert word.affixes[0].type == AffixType.SUFFIX
    assert word.affixes[1].type == AffixType.PREFIX

    word.delete_affix_at(1)
    assert len(word.affixes) == 1
    assert word.affixes[0].type == AffixType.SUFFIX

    word.delete_affix_at(0)
    assert len(word.affixes) == 0


def test_insert_new_affix_at(word):
    assert len(word.affixes) == 0
    word.insert_new_affix_at(AffixType.PREFIX, 0)
    assert len(word.affixes) == 1
    assert word.affixes[0].type == AffixType.PREFIX
    word.insert_new_affix_at(AffixType.SUFFIX, 0)
    assert len(word.affixes) == 2
    assert word.affixes[0].type == AffixType.SUFFIX
    word.insert_new_affix_at(AffixType.PREFIX, 2)
    assert len(word.affixes) == 3
    assert word.affixes[2].type == AffixType.PREFIX


def test_insert_affix_at(word):
    assert len(word.affixes) == 0
    affix = Affix()
    affix.type = AffixType.PREFIX
    word.insert_affix_at(affix, 0)
    assert len(word.affixes) == 1
    assert word.affixes[0].type == AffixType.PREFIX

    affix2 = Affix()
    affix2.type = AffixType.SUFFIX
    word.insert_affix_at(affix2, 1)
    assert len(word.affixes) == 2
    assert word.affixes[1].type == AffixType.SUFFIX


def test_delete_feature(word):
    feature = Feature()
    feature.label = "gender"
    feature.match = "alpha"
    word.features.append(feature)
    feature2 = Feature()
    feature2.label = "number"
    feature2.match = "singular"
    word.features.append(feature2)
    assert len(word.features) == 2

    word.delete_feature(feature)
    assert len(word.features) == 1
    assert word.features[0] is feature2

    # trying to delete it again does not crash
    word.delete_feature(feature)
    assert len(word.features) == 1
    assert word.features[0] is feature2


def test_swap_position_of_affixes(word):
    _create_two_affixes(word)

    # no-ops for out of bounds
    word.swap_position_of_affixes(-1, 0)
    assert word.affixes[0].type == AffixType.PREFIX
    assert word.affixes[1].type == AffixType.SUFFIX
    word.swap_position_of_affixes(2, 0)
    assert word.affixes[0].type == AffixType.PREFIX
    word.swap_position_of_affixes(0, -1)
    assert word.affixes[0].type == AffixType.PREFIX
    word.swap_position_of_affixes(0, 2)
    assert word.affixes[0].type == AffixType.PREFIX

    word.swap_position_of_affixes(0, 1)
    assert word.affixes[0].type == AffixType.SUFFIX
    assert word.affixes[1].type == AffixType.PREFIX

    word.swap_position_of_affixes(1, 0)
    assert word.affixes[0].type == AffixType.PREFIX
    assert word.affixes[1].type == AffixType.SUFFIX


def test_has_more_than_one_feature(word):
    assert word.has_more_than_one_feature() is False
    feature = Feature()
    feature.label = "gender"
    feature.match = "alpha"
    word.features.append(feature)
    assert word.has_more_than_one_feature() is False
    feature2 = Feature()
    feature2.label = "number"
    feature2.match = "singular"
    word.features.append(feature2)
    assert word.has_more_than_one_feature() is True
    word.delete_feature(feature)
    assert word.has_more_than_one_feature() is False
    _create_two_affixes(word)
    assert word.has_more_than_one_feature() is False
    affix = word.affixes[0]
    affix.features.append(feature)
    assert word.has_more_than_one_feature() is True
    word.delete_feature(feature2)
    assert word.has_more_than_one_feature() is False
    affix.features.append(feature2)
    assert word.has_more_than_one_feature() is True


def _check_rankings(word, one, two, three, four, five):
    assert word.ranking_is_available(1) == one
    assert word.ranking_is_available(2) == two
    assert word.ranking_is_available(3) == three
    assert word.ranking_is_available(4) == four
    assert word.ranking_is_available(5) == five


def test_is_ranking_available(word):
    _check_rankings(word, True, True, True, True, True)
    feature = Feature()
    feature.label = "gender"
    feature.match = "alpha"
    word.features.append(feature)
    _check_rankings(word, True, True, True, True, True)
    feature.ranking = 1
    _check_rankings(word, False, True, True, True, True)
    feature.ranking = 2
    _check_rankings(word, True, False, True, True, True)
    feature.ranking = 3
    _check_rankings(word, True, True, False, True, True)
    feature.ranking = 4
    _check_rankings(word, True, True, True, False, True)
    feature.ranking = 5
    _check_rankings(word, True, True, True, True, False)

    feature2 = Feature()
    feature2.label = "number"
    feature2.match = "singular"
    word.features.append(feature2)
    _check_rankings(word, True, True, True, True, False)
    feature2.ranking = 1
    _check_rankings(word, False, True, True, True, False)

    _create_two_affixes(word)
    _check_rankings(word, False, True, True, True, False)
    affix = word.affixes[0]
    feature3 = Feature()
    affix.features.append(feature3)
    _check_rankings(word, False, True, True, True, False)
    feature3.ranking = 4
    _check_rankings(word, False, True, True, False, False)


def test_get_features(word):
    assert len(word.features) == 0
    word.insert_new_feature("gender", "\u03b1")
    assert len(word.features) == 1
    assert len(word.get_all_features_in_word()) == 1

    word.insert_new_affix_at(AffixType.PREFIX, 0)
    assert len(word.affixes) == 1
    prefix = word.affixes[0]
    prefix.insert_new_feature("number", "\u03b2")
    assert len(prefix.features) == 1
    assert len(word.features) == 1
    assert len(word.get_all_features_in_word()) == 2

    prefix.insert_new_feature("case", "\u03b3")
    assert len(prefix.features) == 2
    assert len(word.features) == 1
    assert len(word.get_all_features_in_word()) == 3

    word.insert_new_affix_at(AffixType.SUFFIX, 1)
    assert len(word.affixes) == 2
    suffix = word.affixes[1]
    suffix.insert_new_feature("tense", "fut")
    assert len(suffix.features) == 1
    assert len(prefix.features) == 2
    assert len(word.features) == 1
    assert len(word.get_all_features_in_word()) == 4
