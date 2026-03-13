from __future__ import annotations
from typing import List, TYPE_CHECKING

from flextrans_rule_generator.flex_model.flex_category import FLExCategory
from flextrans_rule_generator.flex_model.flex_feature import FLExFeature
from flextrans_rule_generator.flex_model.flex_feature_value import FLExFeatureValue, GREEK_VARIABLES

if TYPE_CHECKING:
    from flextrans_rule_generator.model.category import Category


class FLExDataBase:
    def __init__(self):
        self.name: str = ""
        self.categories: list[FLExCategory] = []
        self.features: list[FLExFeature] = []
        self.features_without_variables: list[FLExFeature] = []
        self.max_variables: int = 4

    def add_variable_values_to_features(self) -> None:
        for feature in self.features:
            feature_without_variables = FLExFeature()
            feature_without_variables.name = feature.name
            for v in feature.values:
                feature_without_variables.values.append(v)
            self.features_without_variables.append(feature_without_variables)
            for i in range(min(self.max_variables, len(GREEK_VARIABLES))):
                variable_value = FLExFeatureValue(GREEK_VARIABLES[i])
                variable_value.feature = feature
                feature.values.append(variable_value)

    def clear(self) -> None:
        self.categories.clear()
        self.features.clear()

    def set_feature_in_feature_values(self) -> None:
        for feat in self.features:
            feat.set_feature_in_feature_values()

    def get_features_for_category(self, cat: Category) -> list[FLExFeature]:
        features_for_category: list[FLExFeature] = []
        flex_cat = next((c for c in self.categories if c.abbreviation == cat.name), None)
        if flex_cat is not None:
            for vf in flex_cat.valid_features:
                flex_feat = next((f for f in self.features if f.name == vf.name), None)
                if flex_feat is not None:
                    features_for_category.append(flex_feat)
        return features_for_category
