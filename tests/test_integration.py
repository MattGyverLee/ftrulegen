"""End-to-end integration test simulating FlexTools usage"""

import unittest
import tempfile
import os
import sys
from pathlib import Path

# Ensure src_py is in path
src_py = Path(__file__).parent.parent / "src_py"
if str(src_py) not in sys.path:
    sys.path.insert(0, str(src_py))

from src_py.model.flex_trans_rule_generator import FLExTransRuleGenerator
from src_py.model.flex_trans_rule import FLExTransRule
from src_py.model.source_target import Source, Target
from src_py.model.feature import Feature
from src_py.model.enums import HeadValue, AffixType
from src_py.model.affix import Affix
from src_py.service.xml_backend_provider import XMLBackEndProvider
from src_py.service.rule_id_parent_setter import RuleIdentifierAndParentSetter
from src_py.service.validity_checker import ValidityChecker
from src_py.service.web_page_producer import WebPageProducer
from src_py.service.constituent_finder import ConstituentFinder


class TestIntegrationWorkflow(unittest.TestCase):
    """Integration test simulating a complete FlexTools workflow"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test files"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_complete_workflow(self):
        """Test a complete rule creation and save/load workflow"""
        
        # 1. Create a FLExTransRuleGenerator (empty rule set)
        generator = FLExTransRuleGenerator()
        self.assertEqual(len(generator.flex_trans_rules), 0)
        
        # 2. Create a complex rule with multiple words, features, and affixes
        source = Source()
        target = Target()
        
        # Add source: verb with prefix
        source_word = source.insert_new_word_at(0)
        source_word.word_category = "v"
        source_prefix = Affix(affix_type=AffixType.prefix)
        source_prefix.features.append(Feature(label="tense", value="past"))
        source_word.affixes.append(source_prefix)
        
        # Add target: two words (adj + noun), with head marking and features
        target_adj = target.insert_new_word_at(0)
        target_adj.word_category = "adj"
        target_adj.head = HeadValue.yes
        target_adj.features.append(Feature(label="gender", value="masculine"))
        
        target_noun = target.insert_new_word_at(1)
        target_noun.word_category = "n"
        target_noun.head = HeadValue.no
        target_noun.features.append(Feature(label="number", value="pl"))
        
        rule = FLExTransRule(
            name="ComplexRule",
            description="A complex transformation rule",
            source=source,
            target=target
        )
        
        # 3. Validate the rule
        is_valid, error_msg = ValidityChecker.validate_rule(rule)
        self.assertTrue(is_valid, f"Rule validation failed: {error_msg}")
        
        # 4. Assign identifiers (required for HTML generation and constituent finding)
        setter = RuleIdentifierAndParentSetter()
        setter.set_identifiers_and_parents(rule)
        
        # Verify identifiers are sequential and all components are assigned
        self.assertGreater(rule.source.identifier, 0)
        self.assertGreater(rule.target.identifier, 0)
        self.assertGreater(source_word.identifier, 0)
        self.assertGreater(target_adj.identifier, 0)
        self.assertGreater(target_noun.identifier, 0)
        
        # 5. Test constituent finding (critical for context menu handling)
        finder = ConstituentFinder()
        found_word = finder.find_constituent(rule, source_word.identifier)
        self.assertEqual(found_word, source_word)
        
        found_target_adj = finder.find_constituent(rule, target_adj.identifier)
        self.assertEqual(found_target_adj, target_adj)
        
        # 6. Generate HTML grammar tree
        producer = WebPageProducer()
        html = producer.produce_web_page(rule)
        
        # Verify HTML structure
        self.assertIn("<!DOCTYPE html", html)
        self.assertIn("qwebchannel", html)  # QWebChannel JS bridge
        self.assertIn("toApp", html)  # Click handler function
        self.assertIn("onmousedown", html)  # Event handler
        self.assertIn("ComplexRule", html)  # Rule name in title
        
        # 7. Save rule to XML
        generator.flex_trans_rules.append(rule)
        filepath = os.path.join(self.temp_dir, "integration_test.xml")
        XMLBackEndProvider.save_data_to_file(generator, filepath)
        
        # Verify file was created
        self.assertTrue(os.path.exists(filepath))
        
        # 8. Load rule back from XML (round-trip test)
        loaded_generator = XMLBackEndProvider.load_data_from_file(filepath)
        
        # Verify data integrity
        self.assertEqual(len(loaded_generator.flex_trans_rules), 1)
        loaded_rule = loaded_generator.flex_trans_rules[0]
        self.assertEqual(loaded_rule.name, "ComplexRule")
        self.assertEqual(loaded_rule.description, "A complex transformation rule")
        self.assertEqual(len(loaded_rule.source.words), 1)
        self.assertEqual(len(loaded_rule.target.words), 2)
        self.assertEqual(len(loaded_rule.source.words[0].affixes), 1)
        
        # 9. Re-validate loaded rule
        is_valid, error_msg = ValidityChecker.validate_rule(loaded_rule)
        self.assertTrue(is_valid)
        
        # 10. Re-generate HTML from loaded rule
        html2 = producer.produce_web_page(loaded_rule)
        self.assertGreater(len(html2), 100)
        self.assertIn("ComplexRule", html2)

    def test_multiple_rules_workflow(self):
        """Test managing multiple rules in a generator"""
        generator = FLExTransRuleGenerator()
        
        # Create 3 different rules
        for i in range(3):
            source = Source()
            target = Target()
            
            sw = source.insert_new_word_at(0)
            sw.word_category = "v"
            
            tw = target.insert_new_word_at(0)
            tw.head = HeadValue.yes
            tw.features.append(Feature(label="number", value="sg"))
            
            rule = FLExTransRule(
                name=f"Rule{i+1}",
                source=source,
                target=target
            )
            generator.flex_trans_rules.append(rule)
        
        # Save and load
        filepath = os.path.join(self.temp_dir, "multi_rules.xml")
        XMLBackEndProvider.save_data_to_file(generator, filepath)
        loaded = XMLBackEndProvider.load_data_from_file(filepath)
        
        # Verify all rules loaded
        self.assertEqual(len(loaded.flex_trans_rules), 3)
        for i, rule in enumerate(loaded.flex_trans_rules):
            self.assertEqual(rule.name, f"Rule{i+1}")
        
        # Test duplication (inserts at same index, pushing original down)
        generator.duplicate_rule(0)
        self.assertEqual(len(generator.flex_trans_rules), 4)
        # Index 0 is now the duplicate (inserted before original)
        self.assertEqual(generator.flex_trans_rules[0].name, "Rule1 (duplicate)")
        # Index 1 is the original
        self.assertEqual(generator.flex_trans_rules[1].name, "Rule1")


if __name__ == "__main__":
    unittest.main()
