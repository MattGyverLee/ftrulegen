"""Main Window for FLExTrans Rule Assistant"""

from typing import Optional, NamedTuple
from pathlib import Path

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QLabel, QListWidget, QListWidgetItem, QLineEdit, QPlainTextEdit,
    QCheckBox, QPushButton, QMenu, QAction, QComboBox, QMessageBox,
    QWebEngineView, QButtonBar, QInputDialog, QDialog
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtCore import Qt, QUrl, QPoint, QSize
from PyQt6.QtGui import QKeySequence, QShortcut

from ..model.flex_trans_rule_generator import FLExTransRuleGenerator
from ..model.enums import PhraseType, HeadValue, PermutationsValue
from ..model.word import Word
from ..flexmodel.flex_data import FLExData
from ..service.xml_backend_provider import XMLBackEndProvider
from ..service.xml_flex_data_provider import XMLFLExDataBackEndProvider
from ..service.rule_id_parent_setter import RuleIdentifierAndParentSetter
from ..service.constituent_finder import ConstituentFinder
from ..service.validity_checker import ValidityChecker
from ..service.web_page_producer import WebPageProducer
from ..service.web_page_interactor import WebPageInteractor
from ..service.application_preferences import ApplicationPreferences
from .category_chooser import CategoryChooserDialog
from .feature_value_chooser import FeatureValueChooserDialog
from .disjoint_features_editor import DisjointFeaturesEditorDialog


class WindowResult(NamedTuple):
    """Result returned from main window."""
    saved: bool
    rule_index: Optional[int]
    launch_lrt: bool


class RuleAssistantWindow(QMainWindow):
    """Main window for the Rule Assistant application.

    Displays rules in a tree format, manages editing and generation.
    """

    def __init__(self, rule_file: str, flex_data_file: str, test_data_file: str,
                 came_from_lrt: bool = False, ui_lang_code: str = "en", parent=None):
        """Initialize the main window.

        Args:
            rule_file: Path to rule XML file
            flex_data_file: Path to FLEx metadata XML file
            test_data_file: Path to test data HTML file
            came_from_lrt: Whether launched from Live Rule Tester
            ui_lang_code: UI language code
            parent: Parent widget
        """
        super().__init__(parent)

        self.rule_file = rule_file
        self.flex_data_file = flex_data_file
        self.test_data_file = test_data_file
        self.came_from_lrt = came_from_lrt
        self.ui_lang_code = ui_lang_code

        # Data and state
        self._generator: Optional[FLExTransRuleGenerator] = None
        self._flex_data: Optional[FLExData] = None
        self._current_rule_index = 0
        self._dirty = False
        self._result = WindowResult(saved=False, rule_index=None, launch_lrt=False)

        # Services
        self._producer = WebPageProducer()
        self._finder = ConstituentFinder()
        self._preferences = ApplicationPreferences()

        # Selected constituents for context menu operations
        self._selected_word: Optional[Word] = None
        self._selected_category = None
        self._selected_feature = None
        self._selected_affix = None

        # Setup UI
        self._create_ui()
        self._create_context_menus()
        self._setup_keyboard_shortcuts()

        # Setup WebView
        self._setup_webview()

        # Load data
        self._load_data()

        # Restore window state
        self._restore_window_state()

        self.setWindowTitle("FLExTrans Rule Assistant")

    def _create_ui(self) -> None:
        """Create the main UI layout."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)

        # Create splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # Left pane: rules list
        left_pane = self._create_left_pane()
        splitter.addWidget(left_pane)

        # Right pane: editor and browser
        right_pane = self._create_right_pane()
        splitter.addWidget(right_pane)

        # Set initial splitter sizes (30% left, 70% right)
        splitter.setSizes([200, 460])
        splitter.setResizableWithParent(False)

        self.resize(660, 1000)

    def _create_left_pane(self) -> QWidget:
        """Create the left pane (rules list).

        Returns:
            QWidget containing the rules list
        """
        pane = QWidget()
        layout = QVBoxLayout(pane)

        # Title
        title = QLabel("Rules:")
        layout.addWidget(title)

        # Hint label
        hint = QLabel("(right-click to edit)")
        hint.setStyleSheet("font-style: italic; color: gray;")
        layout.addWidget(hint)

        # Rules list
        self.rule_list = QListWidget()
        self.rule_list.itemSelectionChanged.connect(self._on_rule_selected)
        self.rule_list.customContextMenuRequested.connect(self._on_rule_list_context_menu)
        self.rule_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        layout.addWidget(self.rule_list)

        # Overwrite rules checkbox
        self.overwrite_checkbox = QCheckBox("Overwrite Rules")
        self.overwrite_checkbox.toggled.connect(self._on_overwrite_toggled)
        layout.addWidget(self.overwrite_checkbox)

        # Disjoint features button
        self.disjoint_button = QPushButton("Disjoint Features...")
        self.disjoint_button.clicked.connect(self._on_disjoint_features)
        layout.addWidget(self.disjoint_button)

        return pane

    def _create_right_pane(self) -> QWidget:
        """Create the right pane (editor and browser).

        Returns:
            QWidget containing the editor controls and webviews
        """
        pane = QWidget()
        layout = QVBoxLayout(pane)

        # Top section: rule name, description, test data
        top_layout = QHBoxLayout()

        # Left: name and description
        left_top = QVBoxLayout()

        rule_name_label = QLabel("Rule Name:")
        self.rule_name_field = QLineEdit()
        self.rule_name_field.textChanged.connect(self._on_rule_name_changed)
        left_top.addWidget(rule_name_label)
        left_top.addWidget(self.rule_name_field)

        rule_desc_label = QLabel("Rule Description:")
        self.rule_description_field = QPlainTextEdit()
        self.rule_description_field.setMaximumHeight(82)
        self.rule_description_field.textChanged.connect(self._on_rule_description_changed)
        left_top.addWidget(rule_desc_label)
        left_top.addWidget(self.rule_description_field)

        perm_layout = QHBoxLayout()
        perm_label = QLabel("Create Permutations:")
        self.permutations_combo = QComboBox()
        self.permutations_combo.addItems(["no", "with head", "not head"])
        self.permutations_combo.currentIndexChanged.connect(self._on_permutations_changed)
        perm_layout.addWidget(perm_label)
        perm_layout.addWidget(self.permutations_combo)
        left_top.addLayout(perm_layout)

        top_layout.addLayout(left_top, 1)

        # Right: test data webview
        self.test_data_view = QWebEngineView()
        self.test_data_view.setMinimumWidth(300)
        top_layout.addWidget(self.test_data_view)

        layout.addLayout(top_layout, 0)

        # Button bar
        button_layout = QHBoxLayout()
        self.test_lrt_button = QPushButton("Test In LRT")
        self.test_lrt_button.clicked.connect(self._on_test_in_lrt)
        if self.came_from_lrt:
            self.test_lrt_button.setEnabled(False)
        button_layout.addWidget(self.test_lrt_button)

        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self._on_save)
        button_layout.addWidget(self.save_button)

        self.save_create_button = QPushButton("Save/Create")
        self.save_create_button.clicked.connect(self._on_save_create)
        button_layout.addWidget(self.save_create_button)

        self.save_all_button = QPushButton("Save/Create All")
        self.save_all_button.clicked.connect(self._on_save_create_all)
        button_layout.addWidget(self.save_all_button)

        self.help_button = QPushButton("Help")
        self.help_button.clicked.connect(self._on_help)
        button_layout.addWidget(self.help_button)

        layout.addLayout(button_layout, 0)

        # Main tree view
        self.tree_view = QWebEngineView()
        layout.addWidget(self.tree_view, 1)

        return pane

    def _setup_webview(self) -> None:
        """Setup QWebEngineView with QWebChannel bridge."""
        # Disable context menu on webview
        self.tree_view.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)

        # Create web channel
        self._channel = QWebChannel(self.tree_view.page())

        # Create interactor and register it
        self._interactor = WebPageInteractor(self)
        self._channel.registerObject("ftRuleGenApp", self._interactor)

        # Attach channel to page
        self.tree_view.page().setWebChannel(self._channel)

    def _create_context_menus(self) -> None:
        """Create all context menus."""
        # Word context menu
        self._word_menu = QMenu()
        self._word_menu.addAction("Duplicate", self._on_word_duplicate)
        self._word_menu.addSeparator()
        self._word_menu.addAction("Change Number", self._on_word_change_number)
        self._word_menu.addAction("Mark As Head", self._on_word_mark_as_head)
        self._word_menu.addAction("Remove Head Marking", self._on_word_remove_head)
        self._word_menu.addSeparator()
        self._word_menu.addAction("Insert Before", self._on_word_insert_before)
        self._word_menu.addAction("Insert After", self._on_word_insert_after)
        self._word_menu.addSeparator()
        self._word_menu.addAction("Insert Prefix", self._on_word_insert_prefix)
        self._word_menu.addAction("Insert Suffix", self._on_word_insert_suffix)
        self._word_menu.addAction("Insert Category", self._on_word_insert_category)
        self._word_menu.addAction("Insert Feature", self._on_word_insert_feature)
        self._word_menu.addSeparator()
        self._word_menu.addAction("Move Left", self._on_word_move_left)
        self._word_menu.addAction("Move Right", self._on_word_move_right)
        self._word_menu.addSeparator()
        self._word_menu.addAction("Delete", self._on_word_delete)

        # Category context menu
        self._category_menu = QMenu()
        self._category_menu.addAction("Edit", self._on_category_edit)
        self._category_menu.addSeparator()
        self._category_menu.addAction("Delete", self._on_category_delete)

        # Feature context menu
        self._feature_menu = QMenu()
        self._feature_menu.addAction("Edit", self._on_feature_edit)
        self._feature_menu.addAction("Edit Unmarked", self._on_feature_edit_unmarked)
        self._feature_menu.addAction("Edit Ranking", self._on_feature_edit_ranking)
        self._feature_menu.addSeparator()
        self._feature_menu.addAction("Delete", self._on_feature_delete)
        self._feature_menu.addAction("Delete Unmarked", self._on_feature_delete_unmarked)
        self._feature_menu.addAction("Delete Ranking", self._on_feature_delete_ranking)

        # Affix context menu
        self._affix_menu = QMenu()
        self._affix_menu.addAction("Duplicate", self._on_affix_duplicate)
        self._affix_menu.addSeparator()
        self._affix_menu.addAction("Toggle Affix Type", self._on_affix_toggle_type)
        self._affix_menu.addSeparator()
        self._affix_menu.addAction("Insert Feature", self._on_affix_insert_feature)
        self._affix_menu.addSeparator()
        self._affix_menu.addAction("Insert Prefix Before", self._on_affix_insert_prefix_before)
        self._affix_menu.addAction("Insert Prefix After", self._on_affix_insert_prefix_after)
        self._affix_menu.addAction("Insert Suffix Before", self._on_affix_insert_suffix_before)
        self._affix_menu.addAction("Insert Suffix After", self._on_affix_insert_suffix_after)
        self._affix_menu.addSeparator()
        self._affix_menu.addAction("Move Left", self._on_affix_move_left)
        self._affix_menu.addAction("Move Right", self._on_affix_move_right)
        self._affix_menu.addSeparator()
        self._affix_menu.addAction("Delete", self._on_affix_delete)

        # Rule list context menu
        self._rule_menu = QMenu()
        self._rule_menu.addAction("Duplicate", self._on_rule_duplicate)
        self._rule_menu.addAction("Insert Before", self._on_rule_insert_before)
        self._rule_menu.addAction("Insert After", self._on_rule_insert_after)
        self._rule_menu.addSeparator()
        self._rule_menu.addAction("Move Up", self._on_rule_move_up)
        self._rule_menu.addAction("Move Down", self._on_rule_move_down)
        self._rule_menu.addSeparator()
        self._rule_menu.addAction("Delete", self._on_rule_delete)

    def _setup_keyboard_shortcuts(self) -> None:
        """Setup keyboard shortcuts."""
        QShortcut(QKeySequence("Ctrl+S"), self, self._on_save)

    def _load_data(self) -> None:
        """Load rule and FLEx data files."""
        try:
            # Load rules
            self._generator = XMLBackEndProvider.load_data_from_file(self.rule_file)

            # Load FLEx data
            self._flex_data = XMLFLExDataBackEndProvider.load_data_from_file(self.flex_data_file)

            # Populate rule list
            self._populate_rule_list()

            # Load test data
            if Path(self.test_data_file).exists():
                self.test_data_view.load(QUrl.fromLocalFile(self.test_data_file))

            self._dirty = False
        except Exception as e:
            QMessageBox.critical(self, "Error Loading Data", f"Failed to load data: {e}")

    def _populate_rule_list(self) -> None:
        """Populate the rule list from generator."""
        self.rule_list.clear()
        if self._generator:
            for i, rule in enumerate(self._generator.flex_trans_rules):
                item = QListWidgetItem(rule.name or f"Rule {i+1}")
                self.rule_list.addItem(item)

        # Select first rule
        if self.rule_list.count() > 0:
            self.rule_list.setCurrentRow(0)

    def _show_rule(self, index: int) -> None:
        """Show a rule in the editor.

        Args:
            index: Rule index
        """
        if not self._generator or index < 0 or index >= len(self._generator.flex_trans_rules):
            return

        self._current_rule_index = index
        rule = self._generator.flex_trans_rules[index]

        # Update fields
        self.rule_name_field.setText(rule.name)
        self.rule_description_field.setPlainText(rule.description)
        self.permutations_combo.setCurrentText(
            {
                PermutationsValue.no: "no",
                PermutationsValue.not_head: "not head",
                PermutationsValue.with_head: "with head",
            }.get(rule.create_permutations, "with head")
        )

        # Generate and show HTML
        html = self._producer.produce_web_page(rule)
        self.tree_view.setHtml(html, QUrl("qrc:///"))

        # Update overwrite checkbox
        self.overwrite_checkbox.setChecked(
            self._generator.overwrite_rules.value == "yes"
        )

    def _refresh_rule_view(self) -> None:
        """Refresh the current rule display after editing."""
        if self._generator and 0 <= self._current_rule_index < len(self._generator.flex_trans_rules):
            rule = self._generator.flex_trans_rules[self._current_rule_index]
            # Update list item text
            item = self.rule_list.item(self._current_rule_index)
            if item:
                item.setText(rule.name or f"Rule {self._current_rule_index + 1}")
            # Re-render HTML
            html = self._producer.produce_web_page(rule)
            self.tree_view.setHtml(html, QUrl("qrc:///"))

    def _restore_window_state(self) -> None:
        """Restore window size and position from preferences."""
        x = self._preferences.get_window_position_x()
        y = self._preferences.get_window_position_y()
        w = self._preferences.get_window_width()
        h = self._preferences.get_window_height()
        maximized = self._preferences.get_window_maximized()

        self.setGeometry(x, y, w, h)
        if maximized:
            self.showMaximized()
        else:
            self.show()

        # Restore selected rule
        last_rule = self._preferences.get_last_selected_rule()
        if 0 <= last_rule < self.rule_list.count():
            self.rule_list.setCurrentRow(last_rule)

    def _save_window_state(self) -> None:
        """Save window state to preferences."""
        self._preferences.set_window_position_x(self.x())
        self._preferences.set_window_position_y(self.y())
        self._preferences.set_window_width(self.width())
        self._preferences.set_window_height(self.height())
        self._preferences.set_window_maximized(self.isMaximized())
        self._preferences.set_last_selected_rule(self._current_rule_index)
        self._preferences.sync()

    def process_item_clicked_on(self, item: str, x: int, y: int) -> None:
        """Process a click on a tree element.

        Args:
            item: Element identifier (e.g., "w.5")
            x: Screen X coordinate
            y: Screen Y coordinate
        """
        if not self._generator:
            return

        rule = self._generator.flex_trans_rules[self._current_rule_index]
        type_code = item[0]
        try:
            identifier = int(item[2:])
        except (ValueError, IndexError):
            return

        # Find the constituent
        constituent = self._finder.find_constituent(rule, identifier)
        if not constituent:
            return

        pos = QPoint(x, y)

        # Show appropriate context menu based on type
        if type_code == "w":
            self._selected_word = constituent
            self._word_menu.exec(pos)
        elif type_code == "c":
            self._selected_category = constituent
            self._category_menu.exec(pos)
        elif type_code == "f":
            self._selected_feature = constituent
            self._feature_menu.exec(pos)
        elif type_code == "a":
            self._selected_affix = constituent
            self._affix_menu.exec(pos)
        elif type_code == "p":
            # Phrase click does nothing
            pass

    def _mark_dirty(self) -> None:
        """Mark the document as changed."""
        if not self._dirty:
            self._dirty = True
            # Update title with asterisk
            current_title = self.windowTitle()
            if not current_title.endswith("*"):
                self.setWindowTitle(current_title + "*")

    # Signal handlers
    def _on_rule_selected(self) -> None:
        """Handle rule selection in list."""
        row = self.rule_list.currentRow()
        if row >= 0:
            self._show_rule(row)

    def _on_rule_name_changed(self) -> None:
        """Handle rule name text change."""
        if self._generator and 0 <= self._current_rule_index < len(self._generator.flex_trans_rules):
            self._generator.flex_trans_rules[self._current_rule_index].name = self.rule_name_field.text()
            # Update list
            item = self.rule_list.item(self._current_rule_index)
            if item:
                item.setText(self.rule_name_field.text())
            self._mark_dirty()

    def _on_rule_description_changed(self) -> None:
        """Handle rule description text change."""
        if self._generator and 0 <= self._current_rule_index < len(self._generator.flex_trans_rules):
            self._generator.flex_trans_rules[self._current_rule_index].description = (
                self.rule_description_field.toPlainText()
            )
            self._mark_dirty()

    def _on_permutations_changed(self) -> None:
        """Handle permutations combo change."""
        if self._generator and 0 <= self._current_rule_index < len(self._generator.flex_trans_rules):
            text_to_enum = {
                "no": PermutationsValue.no,
                "with head": PermutationsValue.with_head,
                "not head": PermutationsValue.not_head,
            }
            self._generator.flex_trans_rules[self._current_rule_index].create_permutations = (
                text_to_enum.get(self.permutations_combo.currentText(), PermutationsValue.with_head)
            )
            self._mark_dirty()

    def _on_overwrite_toggled(self) -> None:
        """Handle overwrite checkbox toggle."""
        from ..model.enums import OverwriteRulesValue
        if self._generator:
            self._generator.overwrite_rules = (
                OverwriteRulesValue.yes if self.overwrite_checkbox.isChecked()
                else OverwriteRulesValue.no
            )
            self._mark_dirty()

    def _on_save(self) -> None:
        """Handle Save button."""
        if self._generator:
            XMLBackEndProvider.save_data_to_file(self._generator, self.rule_file)
            self._dirty = False
            # Update title
            current_title = self.windowTitle()
            if current_title.endswith("*"):
                self.setWindowTitle(current_title[:-1])
            QMessageBox.information(self, "Saved", "Rules saved successfully")

    def _on_save_create(self) -> None:
        """Handle Save/Create button."""
        if not self._generator:
            return
        rule = self._generator.flex_trans_rules[self._current_rule_index]
        is_valid, error_msg = ValidityChecker.validate_rule(rule)
        if not is_valid:
            QMessageBox.critical(self, f"Invalid Rule: {rule.name}", error_msg)
            return
        self._on_save()
        self._result = WindowResult(saved=True, rule_index=self._current_rule_index, launch_lrt=False)
        self.close()

    def _on_save_create_all(self) -> None:
        """Handle Save/Create All button."""
        if not self._generator:
            return
        for i, rule in enumerate(self._generator.flex_trans_rules):
            is_valid, error_msg = ValidityChecker.validate_rule(rule)
            if not is_valid:
                QMessageBox.critical(self, f"Invalid Rule: {rule.name}", error_msg)
                return
        self._on_save()
        self._result = WindowResult(saved=True, rule_index=None, launch_lrt=False)
        self.close()

    def _on_test_in_lrt(self) -> None:
        """Handle Test In LRT button."""
        # TODO: Implement with a confirmation dialog
        pass

    def _on_help(self) -> None:
        """Handle Help button."""
        QMessageBox.information(self, "Help", "See documentation for help")

    def _on_disjoint_features(self) -> None:
        """Handle Disjoint Features button."""
        if not self._generator or not self._flex_data:
            QMessageBox.warning(self, "Error", "No data loaded")
            return

        dialog = DisjointFeaturesEditorDialog(self._generator, self._flex_data, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._mark_dirty()
            self._refresh_rule_view()

    def _on_rule_list_context_menu(self, pos: QPoint) -> None:
        """Handle rule list context menu."""
        item = self.rule_list.itemAt(pos)
        if item:
            self._rule_menu.exec(self.rule_list.mapToGlobal(pos))

    # Word menu handlers
    def _on_word_duplicate(self) -> None:
        """Duplicate selected word."""
        if not self._selected_word or not self._generator:
            return

        from copy import deepcopy
        phrase = self._find_phrase_containing_word(
            self._generator.flex_trans_rules[self._current_rule_index],
            self._selected_word
        )
        if not phrase:
            return

        index = phrase.words.index(self._selected_word)
        new_word = deepcopy(self._selected_word)
        phrase.words.insert(index + 1, new_word)
        self._mark_dirty()
        self._refresh_rule_view()

    def _on_word_change_number(self) -> None:
        """Change selected word's number."""
        if not self._selected_word:
            return

        new_id, ok = QInputDialog.getText(
            self, "Change Word Number",
            "Enter new word number:",
            text=self._selected_word.word_id
        )
        if ok and new_id:
            old_id = self._selected_word.word_id
            # Update in both source and target phrases
            if self._generator:
                rule = self._generator.flex_trans_rules[self._current_rule_index]
                # Find and update source
                for word in rule.source.phrase.words:
                    if word.word_id == old_id:
                        word.word_id = new_id
                # Find and update target
                for word in rule.target.phrase.words:
                    if word.word_id == old_id:
                        word.word_id = new_id
            self._mark_dirty()
            self._refresh_rule_view()

    def _on_word_mark_as_head(self) -> None:
        """Mark selected word as head."""
        if not self._selected_word or not self._generator:
            return

        phrase = self._find_phrase_containing_word(
            self._generator.flex_trans_rules[self._current_rule_index],
            self._selected_word
        )
        if phrase:
            phrase.mark_word_as_head(self._selected_word)
            self._mark_dirty()
            self._refresh_rule_view()

    def _on_word_remove_head(self) -> None:
        """Remove head marking from selected word."""
        if not self._selected_word:
            return

        from ..model.enums import HeadValue
        self._selected_word.head = HeadValue.no
        self._mark_dirty()
        self._refresh_rule_view()

    def _on_word_insert_before(self) -> None:
        """Insert word before selected word."""
        if not self._selected_word or not self._generator:
            return

        phrase = self._find_phrase_containing_word(
            self._generator.flex_trans_rules[self._current_rule_index],
            self._selected_word
        )
        if not phrase:
            return

        index = phrase.words.index(self._selected_word)
        phrase.insert_new_word_at(index)
        self._mark_dirty()
        self._refresh_rule_view()

    def _on_word_insert_after(self) -> None:
        """Insert word after selected word."""
        if not self._selected_word or not self._generator:
            return

        phrase = self._find_phrase_containing_word(
            self._generator.flex_trans_rules[self._current_rule_index],
            self._selected_word
        )
        if not phrase:
            return

        index = phrase.words.index(self._selected_word)
        phrase.insert_new_word_at(index + 1)
        self._mark_dirty()
        self._refresh_rule_view()

    def _on_word_insert_prefix(self) -> None:
        """Insert prefix on selected word."""
        if not self._selected_word:
            return

        from ..model.affix import Affix
        from ..model.enums import AffixType
        new_affix = Affix(affix_type=AffixType.prefix)
        self._selected_word.affixes.append(new_affix)
        self._mark_dirty()
        self._refresh_rule_view()

    def _on_word_insert_suffix(self) -> None:
        """Insert suffix on selected word."""
        if not self._selected_word:
            return

        from ..model.affix import Affix
        from ..model.enums import AffixType
        new_affix = Affix(affix_type=AffixType.suffix)
        self._selected_word.affixes.append(new_affix)
        self._mark_dirty()
        self._refresh_rule_view()

    def _on_word_insert_category(self) -> None:
        """Insert category on selected word."""
        if not self._selected_word or not self._flex_data:
            return

        # Get all available categories
        all_categories = []
        if self._flex_data.source_data:
            all_categories.extend(self._flex_data.source_data.categories)
        if self._flex_data.target_data:
            all_categories.extend(self._flex_data.target_data.categories)

        # Remove duplicates and sort
        seen = set()
        unique_categories = []
        for cat in all_categories:
            if cat.abbreviation not in seen:
                unique_categories.append(cat)
                seen.add(cat.abbreviation)

        if not unique_categories:
            QMessageBox.warning(self, "Error", "No categories available")
            return

        # Get current category for pre-selection
        from ..model.category import Category
        current_category = Category(name=self._selected_word.word_category) if self._selected_word.word_category else None

        dialog = CategoryChooserDialog(unique_categories, current_category, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            chosen = dialog.get_chosen_category()
            if chosen:
                self._selected_word.word_category = chosen.abbreviation
                self._selected_word.category_constituent = Category(name=chosen.abbreviation)
                self._mark_dirty()
                self._refresh_rule_view()

    def _on_word_insert_feature(self) -> None:
        """Insert feature on selected word."""
        if not self._selected_word or not self._flex_data:
            return

        # Get all available features
        all_features = []
        if self._flex_data.source_data:
            all_features.extend(self._flex_data.source_data.features)
        if self._flex_data.target_data:
            all_features.extend(self._flex_data.target_data.features)

        if not all_features:
            QMessageBox.warning(self, "Error", "No features available")
            return

        dialog = FeatureValueChooserDialog(all_features, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            result = dialog.get_chosen_value()
            if result:
                flex_feature, flex_value = result
                from ..model.feature import Feature
                new_feature = Feature(
                    label=flex_feature.name,
                    value=flex_value.abbreviation
                )
                self._selected_word.features.append(new_feature)
                self._mark_dirty()
                self._refresh_rule_view()

    def _on_word_move_left(self) -> None:
        """Move selected word left."""
        if not self._selected_word or not self._generator:
            return

        phrase = self._find_phrase_containing_word(
            self._generator.flex_trans_rules[self._current_rule_index],
            self._selected_word
        )
        if not phrase:
            return

        index = phrase.words.index(self._selected_word)
        if index > 0:
            phrase.swap_position_of_words(index, index - 1)
            self._mark_dirty()
            self._refresh_rule_view()

    def _on_word_move_right(self) -> None:
        """Move selected word right."""
        if not self._selected_word or not self._generator:
            return

        phrase = self._find_phrase_containing_word(
            self._generator.flex_trans_rules[self._current_rule_index],
            self._selected_word
        )
        if not phrase:
            return

        index = phrase.words.index(self._selected_word)
        if index < len(phrase.words) - 1:
            phrase.swap_position_of_words(index, index + 1)
            self._mark_dirty()
            self._refresh_rule_view()

    def _on_word_delete(self) -> None:
        """Delete selected word."""
        if not self._selected_word or not self._generator:
            return

        phrase = self._find_phrase_containing_word(
            self._generator.flex_trans_rules[self._current_rule_index],
            self._selected_word
        )
        if phrase:
            index = phrase.words.index(self._selected_word)
            phrase.words.pop(index)
            self._mark_dirty()
            self._refresh_rule_view()

    # Category menu handlers
    def _on_category_edit(self) -> None:
        """Edit selected category."""
        if not self._selected_category or not self._flex_data:
            return

        # Get all available categories
        all_categories = []
        if self._flex_data.source_data:
            all_categories.extend(self._flex_data.source_data.categories)
        if self._flex_data.target_data:
            all_categories.extend(self._flex_data.target_data.categories)

        # Remove duplicates
        seen = set()
        unique_categories = []
        for cat in all_categories:
            if cat.abbreviation not in seen:
                unique_categories.append(cat)
                seen.add(cat.abbreviation)

        if not unique_categories:
            return

        from ..model.category import Category
        current_category = Category(name=self._selected_category.name) if self._selected_category.name else None

        dialog = CategoryChooserDialog(unique_categories, current_category, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            chosen = dialog.get_chosen_category()
            if chosen:
                self._selected_category.name = chosen.abbreviation
                self._mark_dirty()
                self._refresh_rule_view()

    def _on_category_delete(self) -> None:
        """Delete selected category."""
        if not self._selected_category or not self._generator:
            return

        rule = self._generator.flex_trans_rules[self._current_rule_index]
        # Find parent word and clear its category
        self._find_and_clear_category(rule, self._selected_category)
        self._mark_dirty()
        self._refresh_rule_view()

    # Feature menu handlers
    def _on_feature_edit(self) -> None:
        """Edit selected feature."""
        if not self._selected_feature or not self._flex_data:
            return

        # Get all available features
        all_features = []
        if self._flex_data.source_data:
            all_features.extend(self._flex_data.source_data.features)
        if self._flex_data.target_data:
            all_features.extend(self._flex_data.target_data.features)

        if not all_features:
            return

        from ..model.feature import Feature
        # Pre-select current feature for dialog
        current_feature = Feature(
            label=self._selected_feature.label,
            value=self._selected_feature.value
        ) if self._selected_feature.label else None

        dialog = FeatureValueChooserDialog(all_features, current_feature, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            result = dialog.get_chosen_value()
            if result:
                flex_feature, flex_value = result
                self._selected_feature.label = flex_feature.name
                self._selected_feature.value = flex_value.abbreviation
                self._selected_feature.match = ""
                self._mark_dirty()
                self._refresh_rule_view()

    def _on_feature_edit_unmarked(self) -> None:
        """Edit unmarked value of selected feature."""
        if not self._selected_feature:
            return

        text, ok = QInputDialog.getText(
            self, "Edit Unmarked Value",
            "Enter unmarked value:",
            text=self._selected_feature.unmarked
        )
        if ok:
            self._selected_feature.unmarked = text
            self._mark_dirty()
            self._refresh_rule_view()

    def _on_feature_edit_ranking(self) -> None:
        """Edit ranking of selected feature."""
        if not self._selected_feature:
            return

        value, ok = QInputDialog.getInt(
            self, "Edit Ranking",
            "Enter ranking (0 = no ranking):",
            self._selected_feature.ranking,
            0, 9999, 1
        )
        if ok:
            self._selected_feature.ranking = value
            self._mark_dirty()
            self._refresh_rule_view()

    def _on_feature_delete(self) -> None:
        """Delete selected feature."""
        if not self._selected_feature or not self._generator:
            return

        rule = self._generator.flex_trans_rules[self._current_rule_index]
        # Find parent word or affix and remove feature
        self._find_and_remove_feature(rule, self._selected_feature)
        self._mark_dirty()
        self._refresh_rule_view()

    def _on_feature_delete_unmarked(self) -> None:
        """Delete unmarked value from selected feature."""
        if not self._selected_feature:
            return
        self._selected_feature.unmarked = ""
        self._mark_dirty()
        self._refresh_rule_view()

    def _on_feature_delete_ranking(self) -> None:
        """Delete ranking from selected feature."""
        if not self._selected_feature:
            return
        self._selected_feature.ranking = 0
        self._mark_dirty()
        self._refresh_rule_view()

    # Affix menu handlers
    def _on_affix_duplicate(self) -> None:
        """Duplicate selected affix."""
        if not self._selected_affix or not self._selected_word:
            return

        from copy import deepcopy
        index = self._selected_word.affixes.index(self._selected_affix)
        new_affix = deepcopy(self._selected_affix)
        self._selected_word.affixes.insert(index + 1, new_affix)
        self._mark_dirty()
        self._refresh_rule_view()

    def _on_affix_toggle_type(self) -> None:
        """Toggle affix type (prefix <-> suffix)."""
        if not self._selected_affix:
            return

        from ..model.enums import AffixType
        self._selected_affix.affix_type = (
            AffixType.suffix if self._selected_affix.affix_type == AffixType.prefix
            else AffixType.prefix
        )
        self._mark_dirty()
        self._refresh_rule_view()

    def _on_affix_insert_feature(self) -> None:
        """Insert feature on selected affix."""
        if not self._selected_affix or not self._flex_data:
            return

        # Get all available features
        all_features = []
        if self._flex_data.source_data:
            all_features.extend(self._flex_data.source_data.features)
        if self._flex_data.target_data:
            all_features.extend(self._flex_data.target_data.features)

        if not all_features:
            QMessageBox.warning(self, "Error", "No features available")
            return

        dialog = FeatureValueChooserDialog(all_features, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            result = dialog.get_chosen_value()
            if result:
                flex_feature, flex_value = result
                from ..model.feature import Feature
                new_feature = Feature(
                    label=flex_feature.name,
                    value=flex_value.abbreviation
                )
                self._selected_affix.features.append(new_feature)
                self._mark_dirty()
                self._refresh_rule_view()

    def _on_affix_insert_prefix_before(self) -> None:
        """Insert prefix before selected affix."""
        if not self._selected_affix or not self._selected_word:
            return

        from ..model.affix import Affix
        from ..model.enums import AffixType
        index = self._selected_word.affixes.index(self._selected_affix)
        new_affix = Affix(affix_type=AffixType.prefix)
        self._selected_word.affixes.insert(index, new_affix)
        self._mark_dirty()
        self._refresh_rule_view()

    def _on_affix_insert_prefix_after(self) -> None:
        """Insert prefix after selected affix."""
        if not self._selected_affix or not self._selected_word:
            return

        from ..model.affix import Affix
        from ..model.enums import AffixType
        index = self._selected_word.affixes.index(self._selected_affix)
        new_affix = Affix(affix_type=AffixType.prefix)
        self._selected_word.affixes.insert(index + 1, new_affix)
        self._mark_dirty()
        self._refresh_rule_view()

    def _on_affix_insert_suffix_before(self) -> None:
        """Insert suffix before selected affix."""
        if not self._selected_affix or not self._selected_word:
            return

        from ..model.affix import Affix
        from ..model.enums import AffixType
        index = self._selected_word.affixes.index(self._selected_affix)
        new_affix = Affix(affix_type=AffixType.suffix)
        self._selected_word.affixes.insert(index, new_affix)
        self._mark_dirty()
        self._refresh_rule_view()

    def _on_affix_insert_suffix_after(self) -> None:
        """Insert suffix after selected affix."""
        if not self._selected_affix or not self._selected_word:
            return

        from ..model.affix import Affix
        from ..model.enums import AffixType
        index = self._selected_word.affixes.index(self._selected_affix)
        new_affix = Affix(affix_type=AffixType.suffix)
        self._selected_word.affixes.insert(index + 1, new_affix)
        self._mark_dirty()
        self._refresh_rule_view()

    def _on_affix_move_left(self) -> None:
        """Move selected affix left."""
        if not self._selected_affix or not self._selected_word:
            return

        index = self._selected_word.affixes.index(self._selected_affix)
        if index > 0:
            self._selected_word.affixes[index], self._selected_word.affixes[index - 1] = \
                self._selected_word.affixes[index - 1], self._selected_word.affixes[index]
            self._mark_dirty()
            self._refresh_rule_view()

    def _on_affix_move_right(self) -> None:
        """Move selected affix right."""
        if not self._selected_affix or not self._selected_word:
            return

        index = self._selected_word.affixes.index(self._selected_affix)
        if index < len(self._selected_word.affixes) - 1:
            self._selected_word.affixes[index], self._selected_word.affixes[index + 1] = \
                self._selected_word.affixes[index + 1], self._selected_word.affixes[index]
            self._mark_dirty()
            self._refresh_rule_view()

    def _on_affix_delete(self) -> None:
        """Delete selected affix."""
        if not self._selected_affix or not self._selected_word:
            return

        index = self._selected_word.affixes.index(self._selected_affix)
        self._selected_word.affixes.pop(index)
        self._mark_dirty()
        self._refresh_rule_view()

    # Rule menu handlers
    def _on_rule_duplicate(self) -> None:
        """Duplicate selected rule."""
        if self._generator:
            self._generator.duplicate_rule(self._current_rule_index)
            self._populate_rule_list()
            self._mark_dirty()

    def _on_rule_insert_before(self) -> None:
        """Insert new rule before selected."""
        if not self._generator:
            return

        from ..model.flex_trans_rule import FLExTransRule
        from ..model.source_target import Source, Target
        from ..model.phrase import Phrase

        new_rule = FLExTransRule(
            name=f"Rule {len(self._generator.flex_trans_rules) + 1}",
            source=Source(phrase=Phrase()),
            target=Target(phrase=Phrase())
        )
        self._generator.flex_trans_rules.insert(self._current_rule_index, new_rule)
        self._populate_rule_list()
        self._mark_dirty()

    def _on_rule_insert_after(self) -> None:
        """Insert new rule after selected."""
        if not self._generator:
            return

        from ..model.flex_trans_rule import FLExTransRule
        from ..model.source_target import Source, Target
        from ..model.phrase import Phrase

        new_rule = FLExTransRule(
            name=f"Rule {len(self._generator.flex_trans_rules) + 1}",
            source=Source(phrase=Phrase()),
            target=Target(phrase=Phrase())
        )
        self._generator.flex_trans_rules.insert(self._current_rule_index + 1, new_rule)
        self._populate_rule_list()
        self._mark_dirty()

    def _on_rule_move_up(self) -> None:
        """Move selected rule up."""
        if not self._generator or self._current_rule_index <= 0:
            return

        rules = self._generator.flex_trans_rules
        rules[self._current_rule_index], rules[self._current_rule_index - 1] = \
            rules[self._current_rule_index - 1], rules[self._current_rule_index]
        self._current_rule_index -= 1
        self._populate_rule_list()
        self.rule_list.setCurrentRow(self._current_rule_index)
        self._mark_dirty()

    def _on_rule_move_down(self) -> None:
        """Move selected rule down."""
        if not self._generator or self._current_rule_index >= len(self._generator.flex_trans_rules) - 1:
            return

        rules = self._generator.flex_trans_rules
        rules[self._current_rule_index], rules[self._current_rule_index + 1] = \
            rules[self._current_rule_index + 1], rules[self._current_rule_index]
        self._current_rule_index += 1
        self._populate_rule_list()
        self.rule_list.setCurrentRow(self._current_rule_index)
        self._mark_dirty()

    def _on_rule_delete(self) -> None:
        """Delete selected rule."""
        if not self._generator or self._current_rule_index < 0:
            return

        if len(self._generator.flex_trans_rules) == 1:
            QMessageBox.warning(self, "Error", "Cannot delete the last rule")
            return

        self._generator.flex_trans_rules.pop(self._current_rule_index)
        self._populate_rule_list()
        if self._current_rule_index >= len(self._generator.flex_trans_rules):
            self._current_rule_index = len(self._generator.flex_trans_rules) - 1
        if self._current_rule_index >= 0:
            self.rule_list.setCurrentRow(self._current_rule_index)
        self._mark_dirty()

    # Helper methods
    def _find_phrase_containing_word(self, rule, word) -> Optional["Phrase"]:
        """Find which phrase contains the given word.

        Args:
            rule: The current FLExTransRule
            word: The Word to find

        Returns:
            The Phrase containing the word, or None
        """
        if word in rule.source.phrase.words:
            return rule.source.phrase
        if word in rule.target.phrase.words:
            return rule.target.phrase
        return None

    def _find_and_remove_feature(self, rule, feature) -> None:
        """Find and remove a feature from a word or affix.

        Args:
            rule: The current FLExTransRule
            feature: The Feature to remove
        """
        for word in rule.source.phrase.words + rule.target.phrase.words:
            if feature in word.features:
                word.features.remove(feature)
                return
            for affix in word.affixes:
                if feature in affix.features:
                    affix.features.remove(feature)
                    return

    def _find_and_clear_category(self, rule, category) -> None:
        """Find and clear a category from its parent word.

        Args:
            rule: The current FLExTransRule
            category: The Category to clear
        """
        for word in rule.source.phrase.words + rule.target.phrase.words:
            # Compare by name since category objects may not be the same instance
            if word.category_constituent and word.category_constituent.name == category.name:
                word.word_category = ""
                from ..model.category import Category
                word.category_constituent = Category(name="")
                return

    def get_result(self) -> WindowResult:
        """Get the result from the window.

        Returns:
            WindowResult tuple with (saved, rule_index, launch_lrt)
        """
        return self._result

    def closeEvent(self, event) -> None:
        """Handle window close event."""
        if self._dirty:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "You have unsaved changes. Save before closing?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._on_save()

        self._save_window_state()
        event.accept()
