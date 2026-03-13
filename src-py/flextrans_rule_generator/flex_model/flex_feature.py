from __future__ import annotations
from typing import List
from flextrans_rule_generator.flex_model.flex_feature_value import FLExFeatureValue


class FLExFeature:
    def __init__(self, name: str = "", values: List[FLExFeatureValue] = None):
        self.name: str = name
        self.values: list[FLExFeatureValue] = values if values is not None else []

    def set_feature_in_feature_values(self) -> None:
        for val in self.values:
            val.feature = self

    def __str__(self) -> str:
        return self.name

    def __hash__(self):
        return hash((self.name, tuple(hash(v) for v in self.values)))

    def __eq__(self, obj):
        if self is obj:
            return True
        if obj is None or not isinstance(obj, FLExFeature):
            return False
        return self.name == obj.name and self.values == obj.values
