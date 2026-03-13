from __future__ import annotations
from enum import Enum
from typing import Optional
from flextrans_rule_generator.model.constituent_with_features import ConstituentWithFeatures
from flextrans_rule_generator.model.rule_constituent import RuleConstituent
from flextrans_rule_generator.model import strings


class AffixType(Enum):
    PREFIX = "prefix"
    SUFFIX = "suffix"


class Affix(ConstituentWithFeatures):
    def __init__(self):
        super().__init__()
        self.type: AffixType = AffixType.SUFFIX

    def find_constituent(self, identifier: int) -> Optional[RuleConstituent]:
        if self.identifier == identifier:
            return self
        return self._find_constituent_in_features(identifier)

    def _is_head(self) -> bool:
        from flextrans_rule_generator.model.word import Word, HeadValue
        parent = self.parent
        if isinstance(parent, Word):
            return parent.head == HeadValue.YES
        return False

    def produce_html(self) -> str:
        sb = []
        sb.append("<li>")
        sb.append(self.produce_span("tf-nc affix", "a"))
        sb.append(strings.PREFIX if self.type == AffixType.PREFIX else strings.SUFFIX)
        sb.append("</span>")
        if len(self.features) > 0:
            sb.append("<ul>")
            self._html_sb = sb
            self._produce_html_for_features(self._is_head())
            sb.append("</ul>")
        sb.append("</li>\n")
        return "".join(sb)

    def duplicate(self) -> Affix:
        new_affix = Affix()
        new_affix.type = self.type
        new_affix.features = self._duplicate_features()
        return new_affix

    def __hash__(self):
        return hash((self.type, tuple(hash(f) for f in self.features)))

    def __eq__(self, obj):
        if self is obj:
            return True
        if obj is None or not isinstance(obj, Affix):
            return False
        if self.type != obj.type:
            return False
        if self.features != obj.features:
            return False
        return True
