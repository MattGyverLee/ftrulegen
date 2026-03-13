from __future__ import annotations
from typing import Optional
from flextrans_rule_generator.model.rule_constituent import RuleConstituent


class ConstituentWithFeatures(RuleConstituent):
    def __init__(self):
        super().__init__()
        self.features: list = []  # list[Feature], avoid circular import

    def delete_feature(self, feature) -> None:
        self.features.remove(feature)

    def insert_new_feature(self, label: str, match: str):
        from flextrans_rule_generator.model.feature import Feature
        feat = Feature()
        feat.label = label
        feat.match = match
        self.features.append(feat)
        return feat

    def _find_constituent_in_features(self, identifier: int) -> Optional[RuleConstituent]:
        for feature in self.features:
            constituent = feature.find_constituent(identifier)
            if constituent is not None:
                return constituent
        return None

    def _produce_html_for_features(self, is_head: bool = False) -> None:
        """Produce HTML for features, appending to self._html_sb."""
        if len(self.features) > 0:
            self._html_sb.append("<li>")
            self._html_sb.append('<table class="tf-nc">\n')
            for feature in self.features:
                self._html_sb.append("<tr>\n")
                self._html_sb.append('<td align="left">')
                self._html_sb.append(feature.produce_html(is_head))
                self._html_sb.append("</td>\n")
                self._html_sb.append("</tr>\n")
            self._html_sb.append("</table>\n")
            self._html_sb.append("</li>\n")

    def _duplicate_features(self) -> list:
        return [f.duplicate() for f in self.features]
