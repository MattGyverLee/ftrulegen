# Copyright (c) 2024-2026 SIL International
# This software is licensed under the LGPL, version 2.1 or later
# (http://www.gnu.org/licenses/lgpl-2.1.html)

from __future__ import annotations
from enum import Enum


class ValidFeatureType(Enum):
    PREFIX = "prefix"
    PREFIX_STEM = "prefix|stem"
    PREFIX_STEM_SUFFIX = "prefix|stem|suffix"
    PREFIX_SUFFIX = "prefix|suffix"
    STEM = "stem"
    STEM_SUFFIX = "stem|suffix"
    SUFFIX = "suffix"


class ValidFeature:
    def __init__(self, name: str = "", feature_type: ValidFeatureType = ValidFeatureType.STEM):
        self.name: str = name
        self.type: ValidFeatureType = feature_type
        self.s_type: str = feature_type.value

    def set_s_type(self, value: str) -> None:
        self.s_type = value
        type_map = {
            "prefix": ValidFeatureType.PREFIX,
            "prefix|stem": ValidFeatureType.PREFIX_STEM,
            "prefix|stem|suffix": ValidFeatureType.PREFIX_STEM_SUFFIX,
            "prefix|suffix": ValidFeatureType.PREFIX_SUFFIX,
            "stem": ValidFeatureType.STEM,
            "stem|suffix": ValidFeatureType.STEM_SUFFIX,
            "suffix": ValidFeatureType.SUFFIX,
        }
        self.type = type_map.get(value, ValidFeatureType.STEM)

    def __str__(self) -> str:
        return self.name + str(self.type.value)

    def __hash__(self):
        return hash((self.name, self.type))

    def __eq__(self, obj):
        if self is obj:
            return True
        if obj is None or not isinstance(obj, ValidFeature):
            return False
        return self.name == obj.name and self.type == obj.type
