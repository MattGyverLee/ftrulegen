from __future__ import annotations
from flextrans_rule_generator.model.rule_constituent import RuleConstituent
from flextrans_rule_generator.model.phrase import Phrase, PhraseType


class ConstituentWithPhrase(RuleConstituent):
    """Base class for Source and Target, which contain a Phrase."""

    def __init__(self):
        super().__init__()
        self.phrase: Phrase = Phrase()


class Source(ConstituentWithPhrase):
    def __init__(self):
        super().__init__()
        self.phrase.type = PhraseType.SOURCE

    def duplicate(self) -> Source:
        new_source = Source()
        new_source.phrase = self.phrase.duplicate()
        return new_source
