from __future__ import annotations
from enum import Enum
from typing import Optional, List, TYPE_CHECKING
from flextrans_rule_generator.model.rule_constituent import RuleConstituent
from flextrans_rule_generator.model.word import Word, HeadValue
from flextrans_rule_generator.model.category import Category
from flextrans_rule_generator.model import strings

if TYPE_CHECKING:
    from flextrans_rule_generator.model.feature import Feature
    from flextrans_rule_generator.flex_model.flex_feature import FLExFeature
    from flextrans_rule_generator.flex_model.flex_feature_value import FLExFeatureValue
    from flextrans_rule_generator.flex_model.flex_category import FLExCategory


class PhraseType(Enum):
    SOURCE = "source"
    TARGET = "target"


class Phrase(RuleConstituent):
    def __init__(self):
        super().__init__()
        self.words: list[Word] = []
        self.type: PhraseType = PhraseType.SOURCE

    def delete_word_at(self, index: int) -> None:
        if index < 0 or index >= len(self.words):
            return
        del self.words[index]

    def insert_new_word_at(self, index: int) -> None:
        if index < 0 or index > len(self.words):
            return
        new_word = Word()
        new_word.id = self.get_id_of_newly_added_word()
        self.words.insert(index, new_word)

    def insert_word_at(self, word: Word, index: int) -> None:
        if index < 0 or index > len(self.words):
            return
        self.words.insert(index, word)

    def get_id_of_newly_added_word(self) -> str:
        for i in range(len(self.words)):
            s_id = str(i + 1)
            found_it = False
            for word in self.words:
                if word.id == s_id:
                    found_it = True
                    break
            if not found_it:
                return str(i + 1)
        return str(len(self.words) + 1)

    def swap_position_of_words(self, index: int, other_index: int) -> None:
        if index < 0 or index >= len(self.words):
            return
        if other_index < 0 or other_index >= len(self.words):
            return
        self.words[index], self.words[other_index] = self.words[other_index], self.words[index]

    def change_id_of_word(self, index: int, old_id: str, new_id: str) -> None:
        if index < 0 or index >= len(self.words):
            return
        other_word = next((w for w in self.words if w.id == new_id), None)
        if other_word is not None:
            index_other = self.words.index(other_word)
            self.words[index_other].id = old_id
        self.words[index].id = new_id

    def mark_word_as_head(self, word: Word) -> None:
        index = self.words.index(word) if word in self.words else -1
        if index < 0 or index >= len(self.words):
            return
        for w in self.words:
            if w is word:
                w.head = HeadValue.YES
            else:
                w.head = HeadValue.NO

    def get_features_in_use(self) -> list:
        from flextrans_rule_generator.flex_model.flex_feature import FLExFeature
        from flextrans_rule_generator.flex_model.flex_feature_value import FLExFeatureValue
        features_in_use: list = []
        for w in self.words:
            for feat in w.features:
                if self._feature_already_in_use(feat, features_in_use) or self._is_newly_inserted_feature(feat):
                    continue
                values = [FLExFeatureValue(feat.get_match_or_value())]
                existing = FLExFeature()
                existing.name = feat.label
                existing.values = values
                existing.set_feature_in_feature_values()
                features_in_use.append(existing)
        return features_in_use

    def get_features_in_use_for_category(self, categories: list, cat: Category) -> list:
        from flextrans_rule_generator.flex_model.flex_feature import FLExFeature
        from flextrans_rule_generator.flex_model.flex_feature_value import FLExFeatureValue
        features_in_use: list = []
        for w in self.words:
            for feat in w.get_all_features_in_word():
                if self._feature_already_in_use(feat, features_in_use) or self._is_newly_inserted_feature(feat):
                    continue
                flex_cat = next((c for c in categories if c.abbreviation == cat.name), None)
                if flex_cat is not None:
                    vf = next((v for v in flex_cat.valid_features if v.name == feat.label), None)
                    if vf is None:
                        continue
                values = [FLExFeatureValue(feat.get_match_or_value())]
                existing = FLExFeature()
                existing.name = feat.label
                existing.values = values
                existing.set_feature_in_feature_values()
                features_in_use.append(existing)
        return features_in_use

    def _feature_already_in_use(self, feat, features_in_use: list) -> bool:
        for ff in features_in_use:
            if ff.name == feat.label:
                if len(ff.values) > 0 and ff.values[0].abbreviation == feat.get_match_or_value():
                    return True
        return False

    @staticmethod
    def _is_newly_inserted_feature(feat) -> bool:
        return feat.label == "" and feat.get_match_or_value() == ""

    def produce_html(self) -> str:
        sb = []
        sb.append("<li>")
        sb.append(self.produce_span("tf-nc", "p"))
        sb.append(strings.PHRASE)
        sb.append('<span class="language">')
        if self.type == PhraseType.SOURCE:
            sb.append(strings.SRC)
        else:
            sb.append(strings.TGT)
        sb.append("</span></span>\n")
        sb.append("<ul>")
        for word in self.words:
            sb.append(word.produce_html())
        sb.append("</ul>")
        sb.append("</li>")
        return "".join(sb)

    def find_constituent(self, identifier: int) -> Optional[RuleConstituent]:
        if self.identifier == identifier:
            return self
        for word in self.words:
            constituent = word.find_constituent(identifier)
            if constituent is not None:
                return constituent
        return None

    def duplicate(self) -> Phrase:
        new_phrase = Phrase()
        for word in self.words:
            new_phrase.words.append(word.duplicate(False))
        return new_phrase

    def get_category_of_word_with_id(self, word_id: str) -> Optional[Category]:
        """Look up the source word's category by matching word ID."""
        cat = None
        parent = self.parent
        # Import here to avoid circular imports
        from flextrans_rule_generator.model.rule import FLExTransRule
        if isinstance(parent, FLExTransRule):
            phrase = parent.source.phrase
            word = next((w for w in phrase.words if w.id == word_id), None)
            if word is not None:
                return word.category_constituent
        return cat

    def __hash__(self):
        return hash((self.type, tuple(hash(w) for w in self.words)))

    def __eq__(self, obj):
        if self is obj:
            return True
        if obj is None or not isinstance(obj, Phrase):
            return False
        if self.type != obj.type:
            return False
        if self.words != obj.words:
            return False
        return True
