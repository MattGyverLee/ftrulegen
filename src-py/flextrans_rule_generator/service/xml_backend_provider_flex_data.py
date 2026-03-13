import traceback
import xml.etree.ElementTree as ET

from flextrans_rule_generator.flex_model.flex_data import FLExData
from flextrans_rule_generator.flex_model.flex_data_base import FLExDataBase
from flextrans_rule_generator.flex_model.flex_category import FLExCategory
from flextrans_rule_generator.flex_model.flex_feature import FLExFeature
from flextrans_rule_generator.flex_model.flex_feature_value import FLExFeatureValue
from flextrans_rule_generator.flex_model.valid_feature import ValidFeature


class XmlBackEndProviderFLExData:
    def __init__(self):
        self.flex_data: FLExData | None = None

    def load_data_from_file(self, file_name: str):
        try:
            tree = ET.parse(file_name)
            root = tree.getroot()

            data = FLExData()

            source_elem = root.find("SourceData")
            if source_elem is not None:
                data.source_data.name = source_elem.get("name", "")
                self._parse_data_section(source_elem, data.source_data)

            target_elem = root.find("TargetData")
            if target_elem is not None:
                data.target_data.name = target_elem.get("name", "")
                self._parse_data_section(target_elem, data.target_data)

            data.set_feature_in_feature_values()
            self.flex_data = data
        except Exception as e:
            traceback.print_exc()
            raise

    def _parse_data_section(self, elem: ET.Element, data_base: FLExDataBase):
        categories_elem = elem.find("Categories")
        if categories_elem is not None:
            for cat_elem in categories_elem.findall("FLExCategory"):
                cat = FLExCategory()
                cat.abbreviation = cat_elem.get("abbr", "")
                # Parse valid features
                valid_features_elem = cat_elem.find("ValidFeatures")
                if valid_features_elem is not None:
                    for vf_elem in valid_features_elem.findall("ValidFeature"):
                        vf = ValidFeature()
                        vf.name = vf_elem.get("name", "")
                        vf_type = vf_elem.get("type", "stem")
                        vf.set_s_type(vf_type)
                        cat.valid_features.append(vf)
                data_base.categories.append(cat)

        features_elem = elem.find("Features")
        if features_elem is not None:
            for feat_elem in features_elem.findall("FLExFeature"):
                feat = FLExFeature()
                feat.name = feat_elem.get("name", "")
                values_elem = feat_elem.find("Values")
                if values_elem is not None:
                    for val_elem in values_elem.findall("FLExFeatureValue"):
                        val = FLExFeatureValue(val_elem.get("abbr", ""))
                        feat.values.append(val)
                data_base.features.append(feat)
