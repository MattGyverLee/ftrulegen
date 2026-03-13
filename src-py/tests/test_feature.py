# Copyright (c) 2024-2026 SIL International
# This software is licensed under the LGPL, version 2.1 or later
# (http://www.gnu.org/licenses/lgpl-2.1.html)

import pytest
from flextrans_rule_generator.model.word import Word
from flextrans_rule_generator.model.affix import Affix
from flextrans_rule_generator.model.feature import Feature


@pytest.fixture
def setup():
    word = Word()
    affix = Affix()
    f_case = Feature()
    f_case.label = "case"
    f_case.value = "acc"
    f_gender = Feature()
    f_gender.label = "gender"
    f_gender.value = "m"
    f_number = Feature()
    f_number.label = "number"
    f_number.value = "sg"
    return word, affix, f_case, f_gender, f_number


MAX_RANKINGS = 5


def _init_word_features(word, f_case, f_gender, f_number):
    assert f_case.ranking == 0
    assert f_gender.ranking == 0
    assert f_number.ranking == 0
    word.features.append(f_case)
    word.features.append(f_gender)
    word.features.append(f_number)
    f_case.parent = word
    f_gender.parent = word
    f_number.parent = word


def _init_affix_features(affix, f_case, f_gender, f_number):
    assert f_case.ranking == 0
    assert f_gender.ranking == 0
    assert f_number.ranking == 0
    affix.features.append(f_case)
    affix.features.append(f_gender)
    affix.features.append(f_number)
    f_case.parent = affix
    f_gender.parent = affix
    f_number.parent = affix


def test_assign_other_rankings_in_affix(setup):
    word, affix, f_case, f_gender, f_number = setup
    _init_affix_features(affix, f_case, f_gender, f_number)
    f_case.ranking = 2
    f_case.assign_rankings_to_sister_features_without_a_ranking(MAX_RANKINGS)
    assert f_case.ranking == 2
    assert f_gender.ranking == 1
    assert f_number.ranking == 3


def test_assign_other_rankings_in_word(setup):
    word, affix, f_case, f_gender, f_number = setup
    _init_word_features(word, f_case, f_gender, f_number)
    f_case.ranking = 2
    f_case.assign_rankings_to_sister_features_without_a_ranking(MAX_RANKINGS)
    assert f_case.ranking == 2
    assert f_gender.ranking == 1
    assert f_number.ranking == 3

    f_case.ranking = 0
    f_number.ranking = 0
    f_gender.ranking = 1
    f_case.assign_rankings_to_sister_features_without_a_ranking(MAX_RANKINGS)
    assert f_case.ranking == 2
    assert f_gender.ranking == 1
    assert f_number.ranking == 3


def test_remove_all_rankings_in_affix(setup):
    word, affix, f_case, f_gender, f_number = setup
    _init_affix_features(affix, f_case, f_gender, f_number)
    f_case.ranking = 1
    f_gender.ranking = 2
    f_number.ranking = 3
    f_case.ranking = 0
    f_case.remove_rankings_from_sister_features()
    assert f_case.ranking == 0
    assert f_gender.ranking == 0
    assert f_number.ranking == 0


def test_remove_all_rankings_in_word(setup):
    word, affix, f_case, f_gender, f_number = setup
    _init_word_features(word, f_case, f_gender, f_number)
    assert len(word.features) == 3
    f_case.ranking = 1
    f_gender.ranking = 2
    f_number.ranking = 3
    f_case.ranking = 0
    f_case.remove_rankings_from_sister_features()
    assert f_case.ranking == 0
    assert f_gender.ranking == 0
    assert f_number.ranking == 0


def test_swap_ranking_in_affix(setup):
    word, affix, f_case, f_gender, f_number = setup
    _init_affix_features(affix, f_case, f_gender, f_number)
    f_case.ranking = 1
    f_gender.ranking = 2
    f_number.ranking = 3
    f_case.ranking = 3
    f_case.swap_ranking_of_sister_feature_with_ranking(3, 1)
    assert f_case.ranking == 3
    assert f_gender.ranking == 2
    assert f_number.ranking == 1

    f_case.ranking = 2
    f_case.swap_ranking_of_sister_feature_with_ranking(2, 3)
    assert f_case.ranking == 2
    assert f_gender.ranking == 3
    assert f_number.ranking == 1


def test_swap_ranking_in_word(setup):
    word, affix, f_case, f_gender, f_number = setup
    _init_word_features(word, f_case, f_gender, f_number)
    f_case.ranking = 1
    f_gender.ranking = 2
    f_number.ranking = 3
    f_case.ranking = 2
    f_case.swap_ranking_of_sister_feature_with_ranking(2, 1)
    assert f_case.ranking == 2
    assert f_gender.ranking == 1
    assert f_number.ranking == 3

    f_case.ranking = 3
    f_case.swap_ranking_of_sister_feature_with_ranking(3, 2)
    assert f_case.ranking == 3
    assert f_gender.ranking == 1
    assert f_number.ranking == 2


def test_sister_feature_has_a_ranking(setup):
    word, affix, f_case, f_gender, f_number = setup
    _init_word_features(word, f_case, f_gender, f_number)
    assert f_case.sister_feature_has_a_ranking() is False
    assert f_gender.sister_feature_has_a_ranking() is False
    assert f_number.sister_feature_has_a_ranking() is False
    f_case.ranking = 1
    assert f_case.sister_feature_has_a_ranking() is False
    assert f_gender.sister_feature_has_a_ranking() is True
    assert f_number.sister_feature_has_a_ranking() is True
    f_gender.ranking = 2
    assert f_case.sister_feature_has_a_ranking() is True
    assert f_gender.sister_feature_has_a_ranking() is True
    assert f_number.sister_feature_has_a_ranking() is True
