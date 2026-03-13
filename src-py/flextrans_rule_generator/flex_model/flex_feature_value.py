from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flextrans_rule_generator.flex_model.flex_feature import FLExFeature

GREEK_VARIABLES = ["α", "β", "γ", "δ", "ε", "ζ", "η", "θ", "ι", "κ", "μ", "ν"]


class FLExFeatureValue:
    def __init__(self, abbreviation: str = ""):
        self.abbreviation: str = abbreviation
        self.feature: FLExFeature | None = None

    @staticmethod
    def is_greek(abbreviation: str) -> bool:
        return abbreviation in GREEK_VARIABLES

    def __str__(self) -> str:
        sb = []
        if self.feature is not None:
            sb.append(self.feature.name)
            sb.append(" : ")
        sb.append(self.abbreviation)
        return "".join(sb)

    def __hash__(self):
        return hash(self.abbreviation)

    def __eq__(self, obj):
        if self is obj:
            return True
        if obj is None or not isinstance(obj, FLExFeatureValue):
            return False
        return self.abbreviation == obj.abbreviation
