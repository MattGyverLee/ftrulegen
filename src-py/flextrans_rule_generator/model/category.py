from __future__ import annotations
from typing import Optional
from flextrans_rule_generator.model.rule_constituent import RuleConstituent
from flextrans_rule_generator.model import strings


class Category(RuleConstituent):
    def __init__(self, name: str = ""):
        super().__init__()
        self.name: str = name

    def get_phrase(self):
        """Navigate parent chain to find containing Phrase."""
        from flextrans_rule_generator.model.word import Word
        word = self.parent
        if isinstance(word, Word):
            return word.parent
        return None

    def find_constituent(self, identifier: int) -> Optional[RuleConstituent]:
        if self.identifier == identifier:
            return self
        return None

    def produce_html(self) -> str:
        sb = []
        sb.append(self.produce_span("category", "c"))
        self._produce_html_cat_value(sb)
        return "".join(sb)

    def produce_html_target(self, word_id: int) -> str:
        sb = []
        sb.append(self._produce_span_for_target("categorytgt", "w", word_id))
        self._produce_html_cat_value(sb)
        return "".join(sb)

    def _produce_span_for_target(self, s_class: str, s_type: str, word_id: int) -> str:
        sb = []
        sb.append('<span class="')
        sb.append(s_class)
        sb.append('" id="')
        sb.append(s_type)
        sb.append(".")
        sb.append(str(word_id))
        sb.append('" onclick=')
        sb.append('"toApp(\'')
        sb.append(s_type)
        sb.append(".")
        sb.append(str(word_id))
        sb.append("',event)\"")
        sb.append(">")
        return "".join(sb)

    def _produce_html_cat_value(self, sb: list) -> None:
        sb.append(strings.CAT)
        sb.append(":")
        sb.append(self.name)
        sb.append("</span>\n")

    def duplicate(self) -> Category:
        return Category(self.name)
