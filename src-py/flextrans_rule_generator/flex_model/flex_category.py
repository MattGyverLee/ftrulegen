from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flextrans_rule_generator.flex_model.valid_feature import ValidFeature


class FLExCategory:
    def __init__(self):
        self.abbreviation: str = ""
        self.valid_features: list[ValidFeature] = []

    def __str__(self) -> str:
        return self.abbreviation

    def __hash__(self):
        return hash((self.abbreviation, tuple(hash(vf) for vf in self.valid_features)))

    def __eq__(self, obj):
        if self is obj:
            return True
        if obj is None or not isinstance(obj, FLExCategory):
            return False
        return (self.abbreviation == obj.abbreviation and
                self.valid_features == obj.valid_features)
