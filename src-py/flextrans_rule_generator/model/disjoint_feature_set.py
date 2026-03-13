# Copyright (c) 2023 SIL International
# This software is licensed under the LGPL, version 2.1 or later
# (http://www.gnu.org/licenses/lgpl-2.1.html)

from __future__ import annotations
from flextrans_rule_generator.model.disjoint_feature_value_pairing import DisjointFeatureValuePairing


class DisjointFeatureSet:
    """Represents a set of mutually exclusive features (disjoint features).

    Used for languages like Bantu where a single feature (like "number") needs
    to be split into separate features for singular and plural forms.

    Attributes:
        co_feature_name: The source feature being split (e.g., "number")
        language: "source" or "target" - which language this applies to
        disjoint_name: The name of the merged/disjoint feature (e.g., "BantuNounClass")
        feature_value_pairings: List of value mappings
    """

    def __init__(
        self,
        co_feature_name: str = "",
        language: str = "target",
        disjoint_name: str = "",
    ):
        self.co_feature_name: str = co_feature_name
        self.language: str = language
        self.disjoint_name: str = disjoint_name
        self.feature_value_pairings: list[DisjointFeatureValuePairing] = []

    def add_pairing(self, pairing: DisjointFeatureValuePairing) -> None:
        """Add a feature value pairing."""
        if pairing not in self.feature_value_pairings:
            self.feature_value_pairings.append(pairing)

    def remove_pairing(self, pairing: DisjointFeatureValuePairing) -> None:
        """Remove a feature value pairing."""
        if pairing in self.feature_value_pairings:
            self.feature_value_pairings.remove(pairing)

    def get_pairing_by_co_value(self, co_feature_value: str) -> DisjointFeatureValuePairing | None:
        """Find a pairing by its co-feature value."""
        for pairing in self.feature_value_pairings:
            if pairing.co_feature_value == co_feature_value:
                return pairing
        return None

    def has_flex_feature_in_list(self, flex_features: list) -> bool:
        """Check if all pairings have a matching FLEx feature in the given list."""
        for pairing in self.feature_value_pairings:
            s_flex_feature_name = pairing.flex_feature_name
            found = any(f.name == s_flex_feature_name for f in flex_features)
            if not found:
                return False
        return True

    def remove_pairings_from(self, index: int) -> None:
        """Remove pairings from given index onwards (valid range: 3-6)."""
        if index < 3 or index > 6:
            return
        i_size = len(self.feature_value_pairings)
        for i in range(i_size, index - 1, -1):
            if i - 1 < len(self.feature_value_pairings):
                del self.feature_value_pairings[i - 1]

    def get_values_as_list_of_strings(self) -> list[str]:
        """Get a string representation of all pairings."""
        sb = []
        for i, pairing in enumerate(self.feature_value_pairings):
            sb.append(pairing.flex_feature_name)
            sb.append(" / ")
            sb.append(pairing.co_feature_value)
            if i < len(self.feature_value_pairings) - 1:
                sb.append("\n")
        return ["".join(sb)]

    def __repr__(self) -> str:
        return (
            f"DisjointFeatureSet(co_feature_name='{self.co_feature_name}', "
            f"language='{self.language}', disjoint_name='{self.disjoint_name}', "
            f"pairings={len(self.feature_value_pairings)})"
        )

    def __eq__(self, other) -> bool:
        if not isinstance(other, DisjointFeatureSet):
            return False
        return (
            self.co_feature_name == other.co_feature_name
            and self.language == other.language
            and self.disjoint_name == other.disjoint_name
            and self.feature_value_pairings == other.feature_value_pairings
        )
