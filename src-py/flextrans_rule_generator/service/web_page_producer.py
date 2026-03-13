from flextrans_rule_generator.model.rule import FLExTransRule
from flextrans_rule_generator.model.phrase import Phrase
from flextrans_rule_generator.service.rule_identifier_setter import RuleIdentifierAndParentSetter


class WebPageProducer:
    def __init__(self):
        self._setter = RuleIdentifierAndParentSetter()

    def produce_web_page(self, rule: FLExTransRule) -> str:
        self._rule = rule
        self._setter.set_identifiers_and_parents(rule)
        sb = []
        sb.append(self._html_beginning())
        sb.append(self._html_body())
        sb.append(self._html_ending())
        return "".join(sb)

    def _html_beginning(self) -> str:
        sb = []
        sb.append('<!DOCTYPE html SYSTEM "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">\n')
        sb.append('<html xmlns="http://www.w3.org/1999/xhtml">\n')
        sb.append("<head><title>")
        sb.append(self._rule.name)
        sb.append("</title>\n")
        sb.append('<meta charset="utf-8"/>\n')
        sb.append('<link rel="stylesheet" href="node_modules/treeflex/dist/css/treeflex.css"/>\n')
        sb.append('<link rel="stylesheet" href="rulegen.css"/>\n')
        sb.append("<script>\n")
        sb.append(self._javascript_contents())
        sb.append("</script>\n")
        sb.append("</head>\n")
        sb.append("<body>\n")
        return "".join(sb)

    def _javascript_contents(self) -> str:
        sb = []
        sb.append("function toApp(msg,event) {\n")
        sb.append("ftRuleGenApp.setXCoord(event.screenX);\n")
        sb.append("ftRuleGenApp.setYCoord(event.screenY);\n")
        sb.append("ftRuleGenApp.setItemClickedOn(msg);\n")
        sb.append("return false;\n")
        sb.append("}\n")
        return "".join(sb)

    def _html_body(self) -> str:
        sb = []
        sb.append("<table>\n")
        sb.append("<tr>\n")
        sb.append(self._phrase_html(self._rule.source.phrase))
        sb.append("<td>\n")
        sb.append('<span class="arrow"/>\n')
        sb.append("</td>\n")
        sb.append(self._phrase_html(self._rule.target.phrase))
        sb.append("</tr>\n")
        sb.append("</table>\n")
        return "".join(sb)

    def _phrase_html(self, phrase: Phrase) -> str:
        sb = []
        sb.append('<td valign="top">\n')
        sb.append('<span class="tf-tree tf-gap-sm">\n')
        sb.append("<ul>\n")
        sb.append(phrase.produce_html())
        sb.append("</ul>\n")
        sb.append("</span>\n")
        sb.append("</td>\n")
        return "".join(sb)

    def _html_ending(self) -> str:
        sb = []
        sb.append("</body>\n")
        sb.append("</html>\n")
        return "".join(sb)
