from __future__ import annotations
from enum import Enum
from flextrans_rule_generator.model.rule_constituent import RuleConstituent
from flextrans_rule_generator.model.source import Source
from flextrans_rule_generator.model.target import Target
from flextrans_rule_generator.model.phrase import PhraseType
from flextrans_rule_generator.model import strings


class PermutationsValue(Enum):
    NO = "no"
    NOT_HEAD = "not_head"
    WITH_HEAD = "with_head"

    def get_string(self) -> str:
        _strings = {
            PermutationsValue.NO: "No",
            PermutationsValue.NOT_HEAD: "Omitting head-only rule",
            PermutationsValue.WITH_HEAD: "Including head-only rule",
        }
        return _strings.get(self, "??")


class OverwriteRulesValue(Enum):
    NO = "no"
    YES = "yes"


class FLExTransRule(RuleConstituent):
    def __init__(self):
        super().__init__()
        self.source: Source = Source()
        self.target: Target = Target()
        self.name: str = ""
        self.description: str = ""
        self.create_permutations: PermutationsValue = PermutationsValue.WITH_HEAD

    def duplicate(self) -> FLExTransRule:
        new_rule = FLExTransRule()
        new_rule.name = self.name + strings.RULE_DUPLICATED
        new_rule.description = self.description
        new_source = self.source.duplicate()
        new_rule.source = new_source
        new_target = self.target.duplicate()
        new_rule.target = new_target
        # need to be sure to set this phrase as target
        new_target.phrase.type = PhraseType.TARGET
        new_rule.create_permutations = self.create_permutations
        return new_rule

    def __str__(self) -> str:
        if len(self.name) > 0:
            return self.name
        return strings.NAME_MISSING

    def __hash__(self):
        return hash((self.name, self.description,
                      hash(self.source), hash(self.target),
                      self.create_permutations))

    def __eq__(self, obj):
        if self is obj:
            return True
        if obj is None or not isinstance(obj, FLExTransRule):
            return False
        if self.name != obj.name:
            return False
        if self.description != obj.description:
            return False
        if self.source != obj.source:
            return False
        if self.target != obj.target:
            return False
        if self.create_permutations != obj.create_permutations:
            return False
        return True
