from __future__ import annotations
from typing import Optional, TYPE_CHECKING
from flextrans_rule_generator.model.rule_constituent import RuleConstituent
from flextrans_rule_generator.model import strings

if TYPE_CHECKING:
    from flextrans_rule_generator.model.word import Word
    from flextrans_rule_generator.model.phrase import Phrase
    from flextrans_rule_generator.model.affix import Affix
    from flextrans_rule_generator.model.constituent_with_features import ConstituentWithFeatures

FEATURE_CLASS = "feature"


class Feature(RuleConstituent):
    def __init__(self):
        super().__init__()
        self.match: str = ""
        self.label: str = ""
        self.value: str = ""
        self.unmarked: str = ""
        self.ranking: int = 0

    def get_match_or_value(self) -> str:
        if len(self.match) > 0:
            return self.match
        else:
            return self.value

    def get_phrase(self) -> Optional[Phrase]:
        from flextrans_rule_generator.model.word import Word
        from flextrans_rule_generator.model.affix import Affix
        constituent = self.parent
        if isinstance(constituent, Word):
            word = constituent
            phrase = word.parent
            return phrase
        elif isinstance(constituent, Affix):
            affix = constituent
            if affix is not None:
                word = affix.parent
                if word is not None:
                    phrase = word.parent
                    return phrase
        return None

    def get_word(self) -> Optional[Word]:
        from flextrans_rule_generator.model.word import Word
        from flextrans_rule_generator.model.affix import Affix
        constituent = self.parent
        if isinstance(constituent, Word):
            return constituent
        elif isinstance(constituent, Affix):
            affix = constituent
            if affix is not None:
                return affix.parent
        return None

    def find_constituent(self, identifier: int) -> Optional[RuleConstituent]:
        if self.identifier == identifier:
            return self
        return None

    def produce_html(self, is_head: bool = False) -> str:
        s_class = FEATURE_CLASS + " headfeature" if is_head else FEATURE_CLASS
        sb = []
        sb.append(self.produce_span(s_class, "f"))
        sb.append(self.label if len(self.label) > 0 else strings.FEATURE_X)
        sb.append(":")
        sb.append(self.get_match_or_value())
        if self.ranking > 0:
            sb.append('<span class="ranking ')
            sb.append(FEATURE_CLASS)
            sb.append('">')
            sb.append(str(self.ranking))
            sb.append("</span>")
        if len(self.unmarked) > 0:
            self._format_unmarked(sb)
        sb.append("</span>")
        return "".join(sb)

    def _format_unmarked(self, sb: list) -> None:
        sb.append('\n<span class="unmarked ')
        sb.append(FEATURE_CLASS)
        sb.append('">')
        sb.append(strings.UNMARKED)
        sb.append(":")
        sb.append(self.unmarked)
        sb.append("</span>")

    def duplicate(self) -> Feature:
        new_feature = Feature()
        new_feature.label = self.label
        new_feature.match = self.match
        new_feature.value = self.value
        new_feature.unmarked = self.unmarked
        new_feature.ranking = self.ranking
        return new_feature

    def assign_rankings_to_sister_features_without_a_ranking(self, max_rankings: int) -> None:
        from flextrans_rule_generator.model.constituent_with_features import ConstituentWithFeatures
        cwfs = self.parent
        if not isinstance(cwfs, ConstituentWithFeatures):
            return
        is_already_set = [False] * max_rankings
        max_size = len(cwfs.features)
        for i in range(min(max_size, max_rankings)):
            f = cwfs.features[i]
            ranking = f.ranking
            if 0 < ranking <= max_size:
                is_already_set[ranking - 1] = True
        last_next = 0
        for f in cwfs.features:
            if f.ranking == 0:
                for nxt in range(last_next, min(max_rankings, max_size)):
                    if not is_already_set[nxt]:
                        f.ranking = nxt + 1
                        is_already_set[nxt] = True
                        last_next = nxt + 1
                        break

    def sister_feature_has_a_ranking(self) -> bool:
        from flextrans_rule_generator.model.constituent_with_features import ConstituentWithFeatures
        cwfs = self.parent
        if not isinstance(cwfs, ConstituentWithFeatures):
            return False
        for f in cwfs.features:
            if f is not self:
                if f.ranking > 0:
                    return True
        return False

    def swap_ranking_of_sister_feature_with_ranking(self, new_ranking: int, old_ranking: int) -> None:
        if old_ranking <= 0:
            return
        from flextrans_rule_generator.model.constituent_with_features import ConstituentWithFeatures
        cwfs = self.parent
        if not isinstance(cwfs, ConstituentWithFeatures):
            return
        for f in cwfs.features:
            if f is not self and f.ranking == new_ranking:
                f.ranking = old_ranking
                break

    def remove_rankings_from_sister_features(self) -> None:
        from flextrans_rule_generator.model.constituent_with_features import ConstituentWithFeatures
        cwfs = self.parent
        if not isinstance(cwfs, ConstituentWithFeatures):
            return
        for f in cwfs.features:
            f.ranking = 0
