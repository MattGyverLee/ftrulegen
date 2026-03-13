from __future__ import annotations
from typing import Optional


class RuleConstituent:
    def __init__(self):
        self.identifier: int = 0
        self.parent: Optional[RuleConstituent] = None

    def produce_span(self, s_class: str, s_type: str) -> str:
        sb = []
        sb.append('<span class="')
        sb.append(s_class)
        sb.append('" id="')
        sb.append(s_type)
        sb.append(".")
        sb.append(str(self.identifier))
        # switching to onmousedown only so both left and right click will work
        sb.append('" onmousedown=')
        sb.append(self._produce_to_app(s_type))
        sb.append(">")
        return "".join(sb)

    def _produce_to_app(self, s_type: str) -> str:
        sb = []
        sb.append('"toApp(\'')
        sb.append(s_type)
        sb.append(".")
        sb.append(str(self.identifier))
        sb.append("',event)\"")
        return "".join(sb)
