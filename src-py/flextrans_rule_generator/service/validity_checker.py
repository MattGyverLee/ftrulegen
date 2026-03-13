# Copyright (c) 2024-2026 SIL International
# This software is licensed under the LGPL, version 2.1 or later
# (http://www.gnu.org/licenses/lgpl-2.1.html)

from flextrans_rule_generator.model.rule import FLExTransRule
from flextrans_rule_generator.model.word import HeadValue


class ValidityChecker:
    def __init__(self):
        self.rule: FLExTransRule = None

    def check_source_words_have_categories(self) -> bool:
        for word in self.rule.source.phrase.words:
            if len(word.category) == 0:
                return False
        return True

    def check_target_has_feature(self) -> bool:
        for word in self.rule.target.phrase.words:
            if word.features is not None and len(word.features) > 0:
                return True
            for affix in word.affixes:
                if affix.features is not None and len(affix.features) > 0:
                    return True
        return False

    def check_target_word_marked_as_head(self) -> bool:
        for word in self.rule.target.phrase.words:
            if word.head == HeadValue.YES:
                return True
        return False
