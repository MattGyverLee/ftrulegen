from __future__ import annotations
from typing import List, TYPE_CHECKING

from flextrans_rule_generator.flex_model.source_flex_data import SourceFLExData
from flextrans_rule_generator.flex_model.target_flex_data import TargetFLExData
from flextrans_rule_generator.flex_model.flex_category import FLExCategory
from flextrans_rule_generator.flex_model.flex_feature import FLExFeature
from flextrans_rule_generator.model.phrase import PhraseType

if TYPE_CHECKING:
    from flextrans_rule_generator.model.category import Category


class FLExData:
    def __init__(self):
        self.source_data: SourceFLExData = SourceFLExData()
        self.target_data: TargetFLExData = TargetFLExData()

    def clear(self) -> None:
        self.source_data.clear()
        self.target_data.clear()

    def set_feature_in_feature_values(self) -> None:
        self.source_data.set_feature_in_feature_values()
        self.target_data.set_feature_in_feature_values()

    def get_flex_categories_for_phrase(self, phrase_type: PhraseType) -> list[FLExCategory]:
        if phrase_type == PhraseType.SOURCE:
            return self.source_data.categories
        else:
            return self.target_data.categories

    def get_features_in_phrase_for_category(self, phrase_type: PhraseType, cat: Category) -> list[FLExFeature]:
        if phrase_type == PhraseType.SOURCE:
            return self.source_data.get_features_for_category(cat)
        else:
            return self.target_data.get_features_for_category(cat)
