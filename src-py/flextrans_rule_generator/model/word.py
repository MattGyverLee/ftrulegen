from __future__ import annotations
from enum import Enum
from typing import Optional, List, TYPE_CHECKING
from flextrans_rule_generator.model.constituent_with_features import ConstituentWithFeatures
from flextrans_rule_generator.model.rule_constituent import RuleConstituent
from flextrans_rule_generator.model.category import Category
from flextrans_rule_generator.model.affix import Affix, AffixType
from flextrans_rule_generator.model import strings

if TYPE_CHECKING:
    from flextrans_rule_generator.model.feature import Feature
    from flextrans_rule_generator.model.phrase import Phrase


class HeadValue(Enum):
    YES = "yes"
    NO = "no"


class Word(ConstituentWithFeatures):
    def __init__(self):
        super().__init__()
        self.affixes: list[Affix] = []
        self.id: str = ""
        self.category: str = ""
        self.head: HeadValue = HeadValue.NO
        self.category_constituent: Category = Category(self.category)

    def delete_category(self) -> None:
        self.category = ""
        self.category_constituent = Category("")

    def insert_category(self, cat: str) -> None:
        self.category = cat
        if self.category_constituent is not None:
            self.category_constituent.name = cat
        else:
            self.category_constituent = Category(cat)

    def delete_affix_at(self, index: int) -> None:
        if index < 0 or index >= len(self.affixes):
            return
        del self.affixes[index]

    def insert_affix_at(self, affix: Affix, index: int) -> None:
        if index < 0 or (index > len(self.affixes) and len(self.affixes) > 0):
            return
        self.affixes.insert(index, affix)

    def insert_new_affix_at(self, affix_type: AffixType, index: int) -> None:
        if index < 0 or (index > len(self.affixes) and len(self.affixes) > 0):
            return
        new_affix = Affix()
        new_affix.type = affix_type
        self.affixes.insert(index, new_affix)

    def swap_position_of_affixes(self, index: int, other_index: int) -> None:
        if index < 0 or index >= len(self.affixes):
            return
        if other_index < 0 or other_index >= len(self.affixes):
            return
        self.affixes[index], self.affixes[other_index] = self.affixes[other_index], self.affixes[index]

    def find_constituent(self, identifier: int) -> Optional[RuleConstituent]:
        if self.identifier == identifier:
            return self
        constituent = self.category_constituent.find_constituent(identifier)
        if constituent is not None:
            return constituent
        constituent = self._find_constituent_in_features(identifier)
        if constituent is not None:
            return constituent
        for affix in self.affixes:
            constituent = affix.find_constituent(identifier)
            if constituent is not None:
                return constituent
        return None

    def get_category_of_word_or_corresponding_source_word(self) -> Category:
        """Get category of this word, or look up the source word's category by ID."""
        result = self.category_constituent
        if self.parent is not None:
            from flextrans_rule_generator.model.phrase import Phrase
            phrase = self.parent
            if isinstance(phrase, Phrase):
                cat = phrase.get_category_of_word_with_id(self.id)
                if cat is not None and len(cat.name) > 0:
                    result = cat
        return result

    def get_all_features_in_word(self) -> list:
        """Collect all features from this word and its affixes."""
        from flextrans_rule_generator.model.feature import Feature
        features: list = []
        features.extend(self.features)
        for affix in self.affixes:
            features.extend(affix.features)
        return features

    def has_more_than_one_feature(self) -> bool:
        count = len(self.features)
        for affix in self.affixes:
            count += len(affix.features)
        return count > 1

    def ranking_is_available(self, ranking: int) -> bool:
        for feat in self.features:
            if feat.ranking == ranking:
                return False
        for affix in self.affixes:
            for feat in affix.features:
                if feat.ranking == ranking:
                    return False
        return True

    def produce_html(self) -> str:
        sb = []
        sb.append("<li>")
        sb.append('<table class="tf-nc">\n')
        sb.append("<tr>\n")
        sb.append('<td align="center">')
        s_class = "headword" if self.head == HeadValue.YES else ""
        sb.append(self.produce_span(s_class, "w"))
        sb.append(strings.WORD)
        if self.head == HeadValue.YES:
            sb.append("(")
            sb.append('<span style="font-style:italic; font-size:smaller">')
            sb.append(strings.HEAD)
            sb.append("</span>")
            sb.append(")")
        if len(self.id) > 0:
            sb.append('<span class="index">')
            sb.append(self.id)
            sb.append("</span>\n")
        sb.append("</span>\n")
        sb.append("</td>\n")
        sb.append("</tr>\n")
        if len(self.category) > 0:
            self._produce_html_of_category(self.category_constituent, sb, True)
        else:
            cat = self.get_category_of_word_or_corresponding_source_word()
            if cat is not None and len(cat.name) > 0:
                self._produce_html_of_category(cat, sb, False)
        sb.append("</table>\n")
        if len(self.features) > 0 or len(self.affixes) > 0:
            sb.append("<ul>\n")
            # Prefixes first
            for affix in self.affixes:
                if affix.type == AffixType.PREFIX:
                    sb.append(affix.produce_html())
            # Features
            self._html_sb = sb
            self._produce_html_for_features(self.head == HeadValue.YES)
            # Suffixes last
            for affix in self.affixes:
                if affix.type == AffixType.SUFFIX:
                    sb.append(affix.produce_html())
            sb.append("</ul>\n")
        sb.append("</li>")
        return "".join(sb)

    def _produce_html_of_category(self, cat: Category, sb: list, is_source: bool) -> None:
        sb.append("<tr>\n")
        sb.append('<td align="center">')
        if is_source:
            sb.append(cat.produce_html())
        else:
            sb.append(cat.produce_html_target(self.identifier))
        sb.append("</td>\n")
        sb.append("</tr>\n")

    def duplicate(self, assign_new_id: bool = False) -> Word:
        new_word = Word()
        s_id = self.id
        if assign_new_id:
            from flextrans_rule_generator.model.phrase import Phrase
            if isinstance(self.parent, Phrase):
                phrase = self.parent
                s_id = phrase.get_id_of_newly_added_word()
        new_word.id = s_id
        new_word.category = self.category
        new_word.category_constituent = self.category_constituent.duplicate()
        new_word.head = self.head
        for affix in self.affixes:
            new_word.affixes.append(affix.duplicate())
        new_word.features = self._duplicate_features()
        return new_word

    def __hash__(self):
        return hash((self.category, self.head, self.id, tuple(hash(a) for a in self.affixes)))

    def __eq__(self, obj):
        if self is obj:
            return True
        if obj is None or not isinstance(obj, Word):
            return False
        if self.category != obj.category:
            return False
        if self.head != obj.head:
            return False
        if self.id != obj.id:
            return False
        if self.affixes != obj.affixes:
            return False
        return True
