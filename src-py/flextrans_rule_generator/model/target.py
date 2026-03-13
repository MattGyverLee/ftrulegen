from __future__ import annotations
from flextrans_rule_generator.model.source import ConstituentWithPhrase
from flextrans_rule_generator.model.phrase import PhraseType


class Target(ConstituentWithPhrase):
    def __init__(self):
        super().__init__()
        self.phrase.type = PhraseType.TARGET

    def duplicate(self) -> Target:
        new_target = Target()
        new_target.phrase = self.phrase.duplicate()
        return new_target
