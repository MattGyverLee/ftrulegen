from PyQt6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QDialogButtonBox, QLabel
from PyQt6.QtCore import Qt
from flextrans_rule_generator.flex_model.flex_feature import FLExFeature
from flextrans_rule_generator.flex_model.flex_feature_value import FLExFeatureValue
from flextrans_rule_generator.controller import strings


class FeatureValueChooser(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._feature_value_chosen: FLExFeatureValue | None = None
        self._all_values: list[FLExFeatureValue] = []

        self.setWindowTitle(strings.FEATURE_VALUE_CHOOSER_TITLE)
        self.resize(800, 450)

        layout = QVBoxLayout(self)
        self.unmarked_label = QLabel("Unmarked default:")
        self.unmarked_label.setVisible(False)
        layout.addWidget(self.unmarked_label)

        self.list_widget = QListWidget()
        self.list_widget.setMinimumSize(764, 364)
        layout.addWidget(self.list_widget)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._handle_ok)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def set_features(self, features: list[FLExFeature]):
        self.list_widget.clear()
        self._all_values = []
        for feat in features:
            for val in feat.values:
                self.list_widget.addItem(str(val))
                self._all_values.append(val)

    def select_flex_feature_value(self, feature):
        """Select the matching feature value in the list, matching by feature name and abbreviation."""
        if feature is None:
            return
        label = feature.label if hasattr(feature, "label") else ""
        match_or_value = feature.get_match_or_value() if hasattr(feature, "get_match_or_value") else ""
        for i, val in enumerate(self._all_values):
            if (val.feature and val.feature.name == label
                    and val.abbreviation == match_or_value):
                self.list_widget.setCurrentRow(i)
                self.list_widget.scrollToItem(self.list_widget.item(i))
                return
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def show_unmarked_label(self, show: bool):
        self.unmarked_label.setVisible(show)

    def get_feature_value_chosen(self) -> FLExFeatureValue | None:
        return self._feature_value_chosen

    def _handle_ok(self):
        row = self.list_widget.currentRow()
        if 0 <= row < len(self._all_values):
            self._feature_value_chosen = self._all_values[row]
        self.accept()
