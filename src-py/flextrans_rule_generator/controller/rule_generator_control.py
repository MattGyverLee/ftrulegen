from pathlib import Path
from typing import Optional
import sys

from PyQt6.QtCore import Qt, QCoreApplication

# Try to import WebEngine; fall back gracefully if unavailable
QWebEngineView = None
QWebChannel = None
WEBENGINE_AVAILABLE = False

# Check if imports were cached by RuleAssistantPY.py (before flextoolslib import)
_webengine_cache = sys.modules.get('__webengine_cache__', {})

if 'QWebEngineView' in _webengine_cache and 'QWebChannel' in _webengine_cache:
    QWebEngineView = _webengine_cache['QWebEngineView']
    QWebChannel = _webengine_cache['QWebChannel']
    WEBENGINE_AVAILABLE = True
else:
    # Otherwise, try normal import
    try:
        from PyQt6.QtWebEngineWidgets import QWebEngineView
        from PyQt6.QtWebChannel import QWebChannel
        WEBENGINE_AVAILABLE = True
    except ImportError:
        QWebEngineView = None
        QWebChannel = None
        WEBENGINE_AVAILABLE = False

# NOW import the rest of PyQt6
from PyQt6.QtCore import QSettings, QUrl
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QMainWindow,
    QSplitter,
    QListWidget,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QComboBox,
    QCheckBox,
    QMenu,
    QMessageBox,
    QDialog,
    QPushButton,
    QAction,
    QTextBrowser,
)

from flextrans_rule_generator.controller import strings
from flextrans_rule_generator.controller.web_bridge import WebBridge
from flextrans_rule_generator.controller.category_chooser import CategoryChooser
from flextrans_rule_generator.controller.feature_value_chooser import FeatureValueChooser
from flextrans_rule_generator.controller.disjoint_features_dialog import DisjointFeaturesDialog
from flextrans_rule_generator.model.rule_generator import FLExTransRuleGenerator
from flextrans_rule_generator.model.rule import FLExTransRule, PermutationsValue
from flextrans_rule_generator.model.rule_constituent import RuleConstituent
from flextrans_rule_generator.model.phrase import Phrase, PhraseType
from flextrans_rule_generator.model.word import Word, HeadValue
from flextrans_rule_generator.model.category import Category
from flextrans_rule_generator.model.feature import Feature
from flextrans_rule_generator.model.affix import Affix, AffixType
from flextrans_rule_generator.flex_model.flex_data import FLExData
from flextrans_rule_generator.flex_model.flex_feature import FLExFeature
from flextrans_rule_generator.flex_model.flex_feature_value import FLExFeatureValue
from flextrans_rule_generator.service.web_page_producer import WebPageProducer
from flextrans_rule_generator.service.constituent_finder import ConstituentFinder
from flextrans_rule_generator.service.rule_identifier_setter import RuleIdentifierAndParentSetter
from flextrans_rule_generator.service.validity_checker import ValidityChecker


class RuleGeneratorControl(QMainWindow):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle(strings.FORM_TITLE)

        # --- Model references (set externally after construction) ---
        self.rule_generator: Optional[FLExTransRuleGenerator] = None
        self.provider = None  # XmlBackEndProvider, kept for saving
        self.rule_file_path: str = ""
        self.flex_data: Optional[FLExData] = None
        self.max_variables: int = 4

        # --- Services ---
        self.producer: WebPageProducer = WebPageProducer()
        self.finder: ConstituentFinder = ConstituentFinder()
        self.setter: RuleIdentifierAndParentSetter = RuleIdentifierAndParentSetter()

        # --- Currently-selected constituents ---
        self.selected_rule: Optional[FLExTransRule] = None
        self.phrase: Optional[Phrase] = None
        self.word: Optional[Word] = None
        self.category: Optional[Category] = None
        self.feature: Optional[Feature] = None
        self.affix: Optional[Affix] = None

        # --- Tracking ---
        self.last_selected_rule: int = 0
        self._is_dirty: bool = False

        # --- Integration with calling script ---
        self.from_lrt: bool = False
        self.exit_code: str = ""  # "1 <rule_number>" or "2"
        self.request_lrt: bool = False
        self._test_data_file: str = ""

        # --- Build UI ---
        self._build_ui()
        self._build_context_menus()
        self._retrieve_settings()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # Toolbar row
        toolbar_layout = QHBoxLayout()
        toolbar_layout.addStretch()
        self.btn_test_lrt = QPushButton(strings.BTN_TEST_IN_LRT)
        self.btn_test_lrt.clicked.connect(self._on_test_in_lrt)
        toolbar_layout.addWidget(self.btn_test_lrt)
        self.btn_save = QPushButton(strings.BTN_SAVE)
        self.btn_save.clicked.connect(self._on_save_clicked)
        toolbar_layout.addWidget(self.btn_save)
        self.btn_save_write = QPushButton(strings.BTN_SAVE_AND_WRITE)
        self.btn_save_write.clicked.connect(self._on_save_and_write)
        toolbar_layout.addWidget(self.btn_save_write)
        self.btn_save_write_all = QPushButton(strings.BTN_SAVE_AND_WRITE_ALL)
        self.btn_save_write_all.clicked.connect(self._on_save_and_write_all)
        toolbar_layout.addWidget(self.btn_save_write_all)
        self.btn_help = QPushButton(strings.BTN_HELP)
        self.btn_help.clicked.connect(self._on_help)
        toolbar_layout.addWidget(self.btn_help)
        main_layout.addLayout(toolbar_layout)

        # Main 2-pane layout: left pane (rules) | right pane (form + tree)
        main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # LEFT PANE: Rules list with checkbox and button
        left_pane = QWidget()
        left_layout = QVBoxLayout(left_pane)
        left_layout.setContentsMargins(0, 0, 0, 0)

        self.rules_list = QListWidget()
        self.rules_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.rules_list.customContextMenuRequested.connect(self._show_rule_context_menu)
        self.rules_list.currentRowChanged.connect(self._on_rule_selected)
        left_layout.addWidget(self.rules_list)

        # Checkbox and button at bottom of left pane
        bottom_layout = QHBoxLayout()
        self.overwrite_rules_check = QCheckBox(strings.OVERWRITE_RULES)
        self.overwrite_rules_check.stateChanged.connect(self._on_overwrite_rules_changed)
        bottom_layout.addWidget(self.overwrite_rules_check)
        self.btn_set_disjoint = QPushButton(strings.SET_DISJOINT_FEATURES)
        self.btn_set_disjoint.clicked.connect(self._on_set_disjoint_features)
        bottom_layout.addWidget(self.btn_set_disjoint)
        left_layout.addLayout(bottom_layout)

        main_splitter.addWidget(left_pane)

        # RIGHT PANE: Vertical splitter with form fields at top and tree at bottom
        right_pane = QSplitter(Qt.Orientation.Vertical)

        # Top section: form fields on left, source text on right
        top_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Form fields (Rule name, Description, Create permutations)
        form_pane = QWidget()
        form_layout = QVBoxLayout(form_pane)
        form_layout.setContentsMargins(0, 0, 0, 0)

        # Rule name row
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel(strings.RULE_NAME))
        self.rule_name_edit = QLineEdit()
        self.rule_name_edit.textEdited.connect(self._on_rule_name_changed)
        name_layout.addWidget(self.rule_name_edit)
        form_layout.addLayout(name_layout)

        # Description row
        desc_layout = QHBoxLayout()
        desc_layout.addWidget(QLabel(strings.DESCRIPTION))
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(60)
        self.description_edit.textChanged.connect(self._on_description_changed)
        desc_layout.addWidget(self.description_edit)
        form_layout.addLayout(desc_layout)

        # Create permutations row
        perm_layout = QHBoxLayout()
        perm_layout.addWidget(QLabel(strings.CREATE_PERMUTATIONS))
        self.create_permutations_combo = QComboBox()
        for pv in PermutationsValue:
            self.create_permutations_combo.addItem(pv.get_string(), pv)
        self.create_permutations_combo.currentIndexChanged.connect(self._on_create_permutations_changed)
        perm_layout.addWidget(self.create_permutations_combo)
        perm_layout.addStretch()
        form_layout.addLayout(perm_layout)

        form_layout.addStretch()
        top_splitter.addWidget(form_pane)

        # Source text display
        source_pane = QWidget()
        source_layout = QVBoxLayout(source_pane)
        source_layout.setContentsMargins(0, 0, 0, 0)
        source_layout.addWidget(QLabel(strings.SOURCE_TEXT))
        self.source_text_view = QWebEngineView()
        source_layout.addWidget(self.source_text_view)
        top_splitter.addWidget(source_pane)

        top_splitter.setStretchFactor(0, 1)
        top_splitter.setStretchFactor(1, 1)
        top_splitter.setSizes([500, 500])  # 50/50 split
        right_pane.addWidget(top_splitter)

        # Bottom section: tree diagram
        self.web_view = QWebEngineView()
        self.bridge = WebBridge()
        channel = QWebChannel(self.web_view.page())
        channel.registerObject("bridge", self.bridge)
        self.web_view.page().setWebChannel(channel)
        self.bridge.message_received.connect(self._process_web_message)
        right_pane.addWidget(self.web_view)

        right_pane.setStretchFactor(0, 1)
        right_pane.setStretchFactor(1, 1)

        main_splitter.addWidget(right_pane)

        main_splitter.setStretchFactor(0, 1)
        main_splitter.setStretchFactor(1, 3)
        main_layout.addWidget(main_splitter)

    # ------------------------------------------------------------------
    # Context menu definitions
    # ------------------------------------------------------------------

    def _build_context_menus(self):
        # --- Rule context menu (C# order: Duplicate, Insert Before, Insert After, -, Move Up, Move Down, -, Delete) ---
        self.rule_menu = QMenu(self)
        self.rule_act_duplicate = self._add_action(self.rule_menu, strings.CM_DUPLICATE, self._rule_duplicate)
        self.rule_act_insert_before = self._add_action(self.rule_menu, strings.CM_INSERT_BEFORE, self._rule_insert_before)
        self.rule_act_insert_after = self._add_action(self.rule_menu, strings.CM_INSERT_AFTER, self._rule_insert_after)
        self.rule_menu.addSeparator()
        self.rule_act_move_up = self._add_action(self.rule_menu, strings.CM_MOVE_UP, self._rule_move_up)
        self.rule_act_move_down = self._add_action(self.rule_menu, strings.CM_MOVE_DOWN, self._rule_move_down)
        self.rule_menu.addSeparator()
        self.rule_act_delete = self._add_action(self.rule_menu, strings.CM_DELETE, self._rule_delete)

        # --- Word context menu (Java order: Duplicate, -, ChangeNumber, MarkAsHead, RemoveHeadMarking, -, InsertBefore, InsertAfter, -, InsertPrefix, InsertSuffix, InsertCategory, InsertFeature, -, MoveLeft, MoveRight, -, Delete) ---
        self.word_menu = QMenu(self)
        self.word_act_duplicate = self._add_action(self.word_menu, strings.CM_DUPLICATE, self._word_duplicate)
        self.word_menu.addSeparator()
        self.word_act_change_number = self._add_action(self.word_menu, strings.CM_CHANGE_NUMBER, self._word_change_number)
        self.word_act_mark_as_head = self._add_action(self.word_menu, strings.CM_MARK_AS_HEAD, self._word_mark_as_head)
        self.word_act_remove_head_marking = self._add_action(self.word_menu, strings.CM_REMOVE_HEAD_MARKING, self._word_remove_head_marking)
        self.word_menu.addSeparator()
        self.word_act_insert_before = self._add_action(self.word_menu, strings.CM_INSERT_BEFORE, self._word_insert_before)
        self.word_act_insert_after = self._add_action(self.word_menu, strings.CM_INSERT_AFTER, self._word_insert_after)
        self.word_menu.addSeparator()
        self.word_act_insert_prefix = self._add_action(self.word_menu, strings.CM_INSERT_PREFIX, self._word_insert_prefix)
        self.word_act_insert_suffix = self._add_action(self.word_menu, strings.CM_INSERT_SUFFIX, self._word_insert_suffix)
        self.word_act_insert_category = self._add_action(self.word_menu, strings.CM_INSERT_CATEGORY, self._word_insert_category)
        self.word_act_insert_feature = self._add_action(self.word_menu, strings.CM_INSERT_FEATURE, self._word_insert_feature)
        self.word_menu.addSeparator()
        self.word_act_move_left = self._add_action(self.word_menu, strings.CM_MOVE_LEFT, self._word_move_left)
        self.word_act_move_right = self._add_action(self.word_menu, strings.CM_MOVE_RIGHT, self._word_move_right)
        self.word_menu.addSeparator()
        self.word_act_delete = self._add_action(self.word_menu, strings.CM_DELETE, self._word_delete)

        # --- Category context menu (C# order: Edit, -, Delete) ---
        self.category_menu = QMenu(self)
        self._add_action(self.category_menu, strings.CM_EDIT, self._category_edit)
        self.category_menu.addSeparator()
        self._add_action(self.category_menu, strings.CM_DELETE, self._category_delete)

        # --- Feature context menu (Java order: Edit, EditUnmarked, EditRanking, -, Delete, DeleteUnmarked, DeleteRanking) ---
        self.feature_menu = QMenu(self)
        self._add_action(self.feature_menu, strings.CM_EDIT, self._feature_edit)
        self.feature_act_edit_unmarked = self._add_action(self.feature_menu, strings.CM_EDIT_UNMARKED, self._feature_edit_unmarked)
        self.feature_act_edit_ranking = self._add_action(self.feature_menu, strings.CM_EDIT_RANKING, self._feature_edit_ranking)
        self.feature_menu.addSeparator()
        self._add_action(self.feature_menu, strings.CM_DELETE, self._feature_delete)
        self.feature_act_delete_unmarked = self._add_action(self.feature_menu, strings.CM_DELETE_UNMARKED, self._feature_delete_unmarked)
        self.feature_act_delete_ranking = self._add_action(self.feature_menu, strings.CM_DELETE_RANKING, self._feature_delete_ranking)

        # --- Affix context menu (Java order: Duplicate, -, ToggleAffixType, InsertPrefixBefore/After, InsertSuffixBefore/After, InsertFeature, -, MoveLeft, MoveRight, -, Delete) ---
        self.affix_menu = QMenu(self)
        self._add_action(self.affix_menu, strings.CM_DUPLICATE, self._affix_duplicate)
        self.affix_menu.addSeparator()
        self._add_action(self.affix_menu, strings.CM_TOGGLE_AFFIX_TYPE, self._affix_toggle_type)
        self._add_action(self.affix_menu, strings.CM_INSERT_PREFIX_BEFORE, self._affix_insert_prefix_before)
        self._add_action(self.affix_menu, strings.CM_INSERT_PREFIX_AFTER, self._affix_insert_prefix_after)
        self._add_action(self.affix_menu, strings.CM_INSERT_SUFFIX_BEFORE, self._affix_insert_suffix_before)
        self._add_action(self.affix_menu, strings.CM_INSERT_SUFFIX_AFTER, self._affix_insert_suffix_after)
        self.affix_act_insert_feature = self._add_action(self.affix_menu, strings.CM_INSERT_FEATURE, self._affix_insert_feature)
        self.affix_menu.addSeparator()
        self.affix_act_move_left = self._add_action(self.affix_menu, strings.CM_MOVE_LEFT, self._affix_move_left)
        self.affix_act_move_right = self._add_action(self.affix_menu, strings.CM_MOVE_RIGHT, self._affix_move_right)
        self.affix_menu.addSeparator()
        self._add_action(self.affix_menu, strings.CM_DELETE, self._affix_delete)

    @staticmethod
    def _add_action(menu: QMenu, text: str, slot) -> QAction:
        action = menu.addAction(text)
        action.triggered.connect(slot)
        return action

    # ------------------------------------------------------------------
    # Populate rules list
    # ------------------------------------------------------------------

    def fill_rules_list(self):
        self.rules_list.blockSignals(True)
        self.rules_list.clear()
        if self.rule_generator:
            for rule in self.rule_generator.rules:
                self.rules_list.addItem(str(rule))
        self.rules_list.blockSignals(False)
        if self.rule_generator and self.rule_generator.rules:
            index = min(self.last_selected_rule, len(self.rule_generator.rules) - 1)
            index = max(index, 0)
            self.rules_list.setCurrentRow(index)

    # ------------------------------------------------------------------
    # Rule selection
    # ------------------------------------------------------------------

    def _on_rule_selected(self, row: int):
        if row < 0 or not self.rule_generator or row >= len(self.rule_generator.rules):
            self.selected_rule = None
            self.rule_name_edit.clear()
            return
        self.selected_rule = self.rule_generator.rules[row]
        self.last_selected_rule = row
        self.rule_name_edit.setText(self.selected_rule.name)
        # Update description field from selected rule
        self.description_edit.blockSignals(True)
        self.description_edit.setPlainText(self.selected_rule.description)
        self.description_edit.blockSignals(False)
        # Update create permutations combo from selected rule
        self.create_permutations_combo.blockSignals(True)
        pv = self.selected_rule.create_permutations
        for i in range(self.create_permutations_combo.count()):
            if self.create_permutations_combo.itemData(i) == pv:
                self.create_permutations_combo.setCurrentIndex(i)
                break
        self.create_permutations_combo.blockSignals(False)
        # Update checkbox state from rule_generator
        self.overwrite_rules_check.blockSignals(True)
        self.overwrite_rules_check.setChecked(self.rule_generator.overwrite_rules)
        self.overwrite_rules_check.blockSignals(False)
        self._enable_disable_create_permutations(self.selected_rule)
        self._show_rule_in_web_page()

    def _on_rule_name_changed(self, text: str):
        if self.selected_rule is None:
            return
        self.selected_rule.name = text
        row = self.rules_list.currentRow()
        if 0 <= row < self.rules_list.count():
            self.rules_list.item(row).setText(str(self.selected_rule))
        self._mark_dirty()

    def _on_description_changed(self):
        if self.selected_rule is None:
            return
        self.selected_rule.description = self.description_edit.toPlainText()
        self._mark_dirty()

    def _on_create_permutations_changed(self, index: int):
        if self.selected_rule is None:
            return
        pv = self.create_permutations_combo.itemData(index)
        if pv is not None:
            self.selected_rule.create_permutations = pv
        self._mark_dirty()

    def _on_overwrite_rules_changed(self, state: int):
        if self.rule_generator is None:
            return
        self.rule_generator.overwrite_rules = self.overwrite_rules_check.isChecked()
        self._mark_dirty()

    def _on_set_disjoint_features(self):
        if self.rule_generator is None:
            return
        if self.flex_data is None:
            return
        if not self._is_ok_to_show_disjoint_features_editor():
            QMessageBox.critical(
                self,
                strings.DISJOINT_VALIDITY_HEADER,
                f"{strings.DISJOINT_VALIDITY_HEADERTEXT}\n\n{strings.DISJOINT_VALIDITY_MESSAGE}"
            )
            return
        dialog = DisjointFeaturesDialog(
            self,
            self.rule_generator.disjoint_feature_sets,
            self.flex_data
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.rule_generator.disjoint_feature_sets = dialog.get_disjoint_sets()
            self._report_changes_made()

    # ------------------------------------------------------------------
    # Web page display
    # ------------------------------------------------------------------

    def _show_rule_in_web_page(self):
        if self.selected_rule is None:
            return
        html = self.producer.produce_web_page(self.selected_rule)

        if WEBENGINE_AVAILABLE:
            # Inject QWebChannel bridge before </head>
            # The Java toApp(msg,event) sends msg to the app and uses event for coords.
            # In PyQt, we pass the message via QWebChannel and capture screen coords.
            bridge_script = (
                '<script src="qrc:///qtwebchannel/qwebchannel.js"></script>\n'
                "<script>\n"
                "var bridge = null;\n"
                "new QWebChannel(qt.webChannelTransport, function(channel) {\n"
                "    bridge = channel.objects.bridge;\n"
                "});\n"
                "</script>"
            )
            # Replace the Java-style toApp function produced by WebPageProducer
            # with one that sends to the QWebChannel bridge
            html = html.replace(
                "function toApp(msg,event) {\n"
                "ftRuleGenApp.setXCoord(event.screenX);\n"
                "ftRuleGenApp.setYCoord(event.screenY);\n"
                "ftRuleGenApp.setItemClickedOn(msg);\n"
                "return false;\n"
                "}",
                "function toApp(msg,event) {\n"
                "if (bridge) { bridge.receive_message(msg); }\n"
                "return false;\n"
                "}",
            )
            html = html.replace("</head>", bridge_script + "\n</head>")

        try:
            if WEBENGINE_AVAILABLE:
                base_url = QUrl.fromLocalFile(
                    str(Path(__file__).parent.parent / "resources") + "/"
                )
                self.web_view.setHtml(html, base_url)
            else:
                self.web_view.setHtml(html)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Web message processing
    # ------------------------------------------------------------------

    def _process_web_message(self, msg: str):
        if not msg or "." not in msg:
            return
        parts = msg.split(".")
        if len(parts) != 2:
            return
        msg_type = parts[0]
        try:
            identifier = int(parts[1])
        except ValueError:
            return

        if self.selected_rule is None:
            return

        constituent = self.finder.find_constituent(self.selected_rule, identifier)
        if constituent is None:
            return

        if msg_type == "p":
            if isinstance(constituent, Phrase):
                self.phrase = constituent
        elif msg_type == "w":
            if isinstance(constituent, Word):
                self.word = constituent
                self._adjust_word_context_menu()
                self._show_menu_at_cursor(self.word_menu)
        elif msg_type == "c":
            if isinstance(constituent, Category):
                self.category = constituent
                self._show_menu_at_cursor(self.category_menu)
        elif msg_type == "f":
            if isinstance(constituent, Feature):
                self.feature = constituent
                self._adjust_feature_context_menu()
                self._show_menu_at_cursor(self.feature_menu)
        elif msg_type == "a":
            if isinstance(constituent, Affix):
                self.affix = constituent
                self._adjust_affix_context_menu()
                self._show_menu_at_cursor(self.affix_menu)

    def _show_menu_at_cursor(self, menu: QMenu):
        from PyQt6.QtGui import QCursor

        menu.popup(QCursor.pos())

    # ------------------------------------------------------------------
    # Rule context menu (shown on QListWidget right-click)
    # ------------------------------------------------------------------

    def _show_rule_context_menu(self, pos):
        if not self.rule_generator:
            return
        index = self.rules_list.currentRow()
        self._adjust_rule_context_menu(index)
        self.rule_menu.popup(self.rules_list.mapToGlobal(pos))

    def _current_rule_index(self) -> int:
        return self.rules_list.currentRow()

    def _rule_insert_before(self):
        if not self.rule_generator:
            return
        index = self._current_rule_index()
        if index < 0:
            index = 0
        self._insert_new_rule(index)

    def _rule_insert_after(self):
        if not self.rule_generator:
            return
        index = self._current_rule_index() + 1
        if index <= 0:
            index = len(self.rule_generator.rules)
        self._insert_new_rule(min(len(self.rule_generator.rules), index))

    def _insert_new_rule(self, index: int):
        new_rule = FLExTransRule()
        new_rule.source.phrase.insert_new_word_at(0)
        new_rule.target.phrase.insert_new_word_at(0)
        self.rule_generator.rules.insert(index, new_rule)
        self._mark_dirty()
        self.fill_rules_list()
        self.rules_list.setCurrentRow(index)

    def _rule_duplicate(self):
        if not self.rule_generator or self.selected_rule is None:
            return
        index = self._current_rule_index()
        if index < 0:
            return
        new_rule = self.selected_rule.duplicate()
        self.rule_generator.rules.insert(index + 1, new_rule)
        self._mark_dirty()
        self.fill_rules_list()
        self.rules_list.setCurrentRow(index + 1)

    def _rule_delete(self):
        if not self.rule_generator or self.selected_rule is None:
            return
        index = self._current_rule_index()
        if index < 0 or index >= len(self.rule_generator.rules):
            return
        del self.rule_generator.rules[index]
        if len(self.rule_generator.rules) == 0:
            # Insert a new default rule if we deleted the last one
            self._rule_insert_before()
        self._mark_dirty()
        self.fill_rules_list()
        if self.rule_generator.rules:
            new_index = min(index, len(self.rule_generator.rules) - 1)
            self.rules_list.setCurrentRow(new_index)

    def _rule_move_up(self):
        if not self.rule_generator:
            return
        index = self._current_rule_index()
        if index <= 0:
            return
        rules = self.rule_generator.rules
        rules[index], rules[index - 1] = rules[index - 1], rules[index]
        self._mark_dirty()
        self.fill_rules_list()
        self.rules_list.setCurrentRow(index - 1)

    def _rule_move_down(self):
        if not self.rule_generator:
            return
        index = self._current_rule_index()
        rules = self.rule_generator.rules
        if index < 0 or index >= len(rules) - 1:
            return
        rules[index], rules[index + 1] = rules[index + 1], rules[index]
        self._mark_dirty()
        self.fill_rules_list()
        self.rules_list.setCurrentRow(index + 1)

    # ------------------------------------------------------------------
    # Word context menu handlers
    # ------------------------------------------------------------------

    def _get_parent_phrase(self) -> Optional[Phrase]:
        """Return the Phrase that owns the currently-selected word."""
        if self.word is None:
            return None
        parent = self.word.parent
        if isinstance(parent, Phrase):
            return parent
        return None

    def _word_index_in_phrase(self, phrase: Phrase) -> int:
        try:
            return phrase.words.index(self.word)
        except ValueError:
            return -1

    def _word_insert_before(self):
        phrase = self._get_parent_phrase()
        if phrase is None or self.word is None:
            return
        index = self._word_index_in_phrase(phrase)
        if index < 0:
            return
        phrase.insert_new_word_at(index)
        self._enable_disable_create_permutations(self.selected_rule)
        self._report_changes_made()

    def _word_insert_after(self):
        phrase = self._get_parent_phrase()
        if phrase is None or self.word is None:
            return
        index = self._word_index_in_phrase(phrase)
        if index < 0:
            return
        phrase.insert_new_word_at(min(len(phrase.words), index + 1))
        self._enable_disable_create_permutations(self.selected_rule)
        self._report_changes_made()

    def _word_duplicate(self):
        phrase = self._get_parent_phrase()
        if phrase is None or self.word is None:
            return
        index = self._word_index_in_phrase(phrase)
        if index < 0:
            return
        dup = self.word.duplicate(True)
        phrase.insert_word_at(dup, min(len(phrase.words), index + 1))
        self._report_changes_made()

    def _word_delete(self):
        phrase = self._get_parent_phrase()
        if phrase is None or self.word is None:
            return
        index = self._word_index_in_phrase(phrase)
        if index < 0:
            return
        phrase.delete_word_at(index)
        self._enable_disable_create_permutations(self.selected_rule)
        self._report_changes_made()

    def _word_move_left(self):
        phrase = self._get_parent_phrase()
        if phrase is None or self.word is None:
            return
        index = self._word_index_in_phrase(phrase)
        if index <= 0:
            return
        phrase.swap_position_of_words(index, index - 1)
        self._report_changes_made()

    def _word_move_right(self):
        phrase = self._get_parent_phrase()
        if phrase is None or self.word is None:
            return
        index = self._word_index_in_phrase(phrase)
        if index < 0 or index >= len(phrase.words) - 1:
            return
        phrase.swap_position_of_words(index, index + 1)
        self._report_changes_made()

    def _word_mark_as_head(self):
        phrase = self._get_parent_phrase()
        if phrase is None or self.word is None:
            return
        for w in phrase.words:
            if w.head == HeadValue.YES:
                w.head = HeadValue.NO
        self.word.head = HeadValue.YES
        self._enable_disable_create_permutations(self.selected_rule)
        self._report_changes_made()

    def _word_remove_head_marking(self):
        if self.word is None:
            return
        self.word.head = HeadValue.NO
        self._enable_disable_create_permutations(self.selected_rule)
        self._report_changes_made()

    def _word_change_number(self):
        if self.word is None:
            return
        phrase = self._get_parent_phrase()
        if phrase is None:
            return
        index = self._word_index_in_phrase(phrase)
        if index < 0:
            return
        from PyQt6.QtWidgets import QInputDialog
        id_numbers = [str(i) for i in range(1, 21)]
        old_id = self.word.id
        chosen, ok = QInputDialog.getItem(
            self, strings.ID_CHOOSER_HEADER, strings.ID_CHOOSER_CHOOSE,
            id_numbers, id_numbers.index(old_id) if old_id in id_numbers else 0, False
        )
        if ok:
            phrase.change_id_of_word(index, old_id, chosen)
            self._report_changes_made()

    def _word_insert_category(self):
        if self.word is None or self.flex_data is None:
            return
        self.category = self.word.category_constituent
        self._process_insert_category()
        self.word.category_constituent = self.category
        self.word.category = self.category.name
        self._report_changes_made()

    def _word_insert_feature(self):
        if self.word is None or self.flex_data is None:
            return
        self.word.insert_new_feature("", "")
        self.feature = self.word.features[-1]
        self.feature.parent = self.word
        self._process_insert_feature(True)
        self._report_changes_made()

    def _word_insert_prefix(self):
        if self.word is None:
            return
        self.word.insert_new_affix_at(AffixType.PREFIX, max(0, len(self.word.affixes) - 1))
        self._report_changes_made()

    def _word_insert_suffix(self):
        if self.word is None:
            return
        self.word.insert_new_affix_at(AffixType.SUFFIX, max(0, len(self.word.affixes) - 1))
        self._report_changes_made()

    # ------------------------------------------------------------------
    # Category context menu handlers
    # ------------------------------------------------------------------

    def _category_edit(self):
        if self.category is None or self.flex_data is None:
            return
        self._process_insert_category()

    def _process_insert_category(self):
        phrase = self.category.get_phrase() if self.category else None
        if phrase is None:
            return
        rule = phrase.parent
        if rule is None:
            return
        if phrase == rule.source.phrase:
            self._launch_category_chooser(self.flex_data.source_data.categories)
        else:
            self._launch_category_chooser(self.flex_data.target_data.categories)

    def _category_delete(self):
        if self.category is None:
            return
        self.word = self._find_word_for_category()
        if self.word is None:
            return
        self.word.delete_category()
        self._report_changes_made()

    # ------------------------------------------------------------------
    # Feature context menu handlers
    # ------------------------------------------------------------------

    def _feature_edit(self):
        if self.feature is None or self.flex_data is None:
            return
        self._process_insert_feature(False)

    def _feature_delete(self):
        if self.feature is None:
            return
        constituent = self.feature.parent
        if isinstance(constituent, Word):
            self.word = constituent
            self.word.delete_feature(self.feature)
            self._report_changes_made()
        elif isinstance(constituent, Affix):
            self.affix = constituent
            self.affix.delete_feature(self.feature)
            self._report_changes_made()

    def _feature_delete_unmarked(self):
        if self.feature is not None:
            self.feature.unmarked = ""
            self._report_changes_made()

    def _feature_edit_unmarked(self):
        if self.feature is None or self.flex_data is None:
            return
        features_to_show = []
        for ff in self.flex_data.target_data.features_without_variables:
            if ff.name == self.feature.label:
                features_to_show.append(ff)
                break
        if features_to_show:
            self._launch_feature_value_chooser(features_to_show, False, True)

    def _feature_delete_ranking(self):
        if self.feature is not None:
            self.feature.ranking = 0
            self.feature.remove_rankings_from_sister_features()
            self._report_changes_made()

    def _feature_edit_ranking(self):
        if self.feature is None:
            return
        max_rankings = self._get_max_rankings()
        rankings = [str(i) for i in range(1, max_rankings + 1)]
        from PyQt6.QtWidgets import QInputDialog
        current_str = str(self.feature.ranking) if self.feature.ranking > 0 else "1"
        chosen, ok = QInputDialog.getItem(
            self, strings.FEATURE_RANKING_HEADER, strings.FEATURE_RANKING_CHOOSE,
            rankings, rankings.index(current_str) if current_str in rankings else 0, False
        )
        if ok:
            original_ranking = self.feature.ranking
            new_ranking = int(chosen)
            self.feature.ranking = new_ranking
            self.feature.swap_ranking_of_sister_feature_with_ranking(new_ranking, original_ranking)
            self.feature.assign_rankings_to_sister_features_without_a_ranking(max_rankings)
            self._report_changes_made()

    # ------------------------------------------------------------------
    # Affix context menu handlers
    # ------------------------------------------------------------------

    def _get_parent_word_for_affix(self) -> Optional[Word]:
        """Return the Word that owns the currently-selected affix."""
        if self.affix is None:
            return None
        parent = self.affix.parent
        if isinstance(parent, Word):
            return parent
        return None

    def _affix_index_in_word(self, word: Word) -> int:
        try:
            return word.affixes.index(self.affix)
        except ValueError:
            return -1

    def _affix_insert_feature(self):
        if self.affix is None or self.flex_data is None:
            return
        self.affix.insert_new_feature("", "")
        self.feature = self.affix.features[-1]
        self.feature.parent = self.affix
        self._process_insert_feature(True)
        self._report_changes_made()

    def _affix_delete(self):
        self.word = self._get_parent_word_for_affix()
        if self.word is None or self.affix is None:
            return
        index = self._affix_index_in_word(self.word)
        if index < 0:
            return
        self.word.delete_affix_at(index)
        self._report_changes_made()

    def _affix_duplicate(self):
        self.word = self._get_parent_word_for_affix()
        if self.word is None or self.affix is None:
            return
        index = self._affix_index_in_word(self.word)
        if index < 0:
            return
        dup = self.affix.duplicate()
        self.word.insert_affix_at(dup, index)
        self._report_changes_made()

    def _affix_toggle_type(self):
        if self.affix is None:
            return
        if self.affix.type == AffixType.PREFIX:
            self.affix.type = AffixType.SUFFIX
        else:
            self.affix.type = AffixType.PREFIX
        self._report_changes_made()

    def _affix_insert_prefix_before(self):
        self.word = self._get_parent_word_for_affix()
        if self.word is None or self.affix is None:
            return
        index = self._affix_index_in_word(self.word)
        if index < 0:
            return
        self._insert_new_affix(index, AffixType.PREFIX)

    def _affix_insert_prefix_after(self):
        self.word = self._get_parent_word_for_affix()
        if self.word is None or self.affix is None:
            return
        index = self._affix_index_in_word(self.word)
        if index < 0:
            return
        self._insert_new_affix(min(len(self.word.affixes), index + 1), AffixType.PREFIX)

    def _affix_insert_suffix_before(self):
        self.word = self._get_parent_word_for_affix()
        if self.word is None or self.affix is None:
            return
        index = self._affix_index_in_word(self.word)
        if index < 0:
            return
        self._insert_new_affix(index, AffixType.SUFFIX)

    def _affix_insert_suffix_after(self):
        self.word = self._get_parent_word_for_affix()
        if self.word is None or self.affix is None:
            return
        index = self._affix_index_in_word(self.word)
        if index < 0:
            return
        self._insert_new_affix(min(len(self.word.affixes), index + 1), AffixType.SUFFIX)

    def _insert_new_affix(self, index: int, affix_type: AffixType):
        new_affix = Affix()
        self.word = self._get_parent_word_for_affix()
        if self.word is not None:
            self.word.insert_affix_at(new_affix, index)
            new_affix.type = affix_type
            self._report_changes_made()

    def _affix_move_left(self):
        word = self._get_parent_word_for_affix()
        if word is None or self.affix is None:
            return
        index = self._affix_index_in_word(word)
        if index <= 0:
            return
        word.affixes[index], word.affixes[index - 1] = word.affixes[index - 1], word.affixes[index]
        self._report_changes_made()

    def _affix_move_right(self):
        word = self._get_parent_word_for_affix()
        if word is None or self.affix is None:
            return
        index = self._affix_index_in_word(word)
        if index < 0 or index >= len(word.affixes) - 1:
            return
        word.affixes[index], word.affixes[index + 1] = word.affixes[index + 1], word.affixes[index]
        self._report_changes_made()

    # ------------------------------------------------------------------
    # Dialog launchers
    # ------------------------------------------------------------------

    def _launch_category_chooser(self, categories):
        chooser = CategoryChooser(categories, self)
        if self.category and self.category.name:
            for i, cat in enumerate(categories):
                if cat.abbreviation == self.category.name:
                    chooser.select_category(i)
                    break
        if chooser.exec() == QDialog.DialogCode.Accepted and chooser.selected_category:
            cat = chooser.selected_category
            self.category.name = cat.abbreviation
            self.word = self._find_word_for_category()
            if self.word is not None:
                self.word.category = cat.abbreviation
            self._report_changes_made()

    def _process_insert_feature(self, inserting: bool):
        phrase = self.feature.get_phrase()
        if phrase is None:
            return
        rule = phrase.parent
        if rule is None:
            return
        if self.word is None:
            if isinstance(self.feature.parent, Word):
                self.word = self.feature.parent
            elif isinstance(self.feature.parent, Affix):
                affix = self.feature.parent
                self.word = affix.parent
        cat = self.word.get_category_of_word_or_corresponding_source_word()
        flex_categories = self.flex_data.get_flex_categories_for_phrase(phrase.type)
        features_in_use = phrase.get_features_in_use_for_category(flex_categories, cat)
        features_to_show = list(features_in_use)
        features_for_category = self.flex_data.get_features_in_phrase_for_category(phrase.type, cat)
        self._add_any_disjoint_features(features_to_show, features_for_category)
        features_to_show.extend(features_for_category)
        self._launch_feature_value_chooser(features_to_show, inserting, False)

    def _add_any_disjoint_features(self, features_to_show: list, features_for_category: list):
        if self.rule_generator is None:
            return
        for df_set in self.rule_generator.disjoint_feature_sets:
            if df_set.has_flex_feature_in_list(features_for_category):
                ff = FLExFeature(df_set.name)
                from flextrans_rule_generator.flex_model.flex_feature_value import GREEK_VARIABLES
                for i in range(min(self.max_variables, len(GREEK_VARIABLES))):
                    var_value = FLExFeatureValue(GREEK_VARIABLES[i])
                    var_value.feature = ff
                    ff.values.append(var_value)
                features_to_show.append(ff)

    def _launch_feature_value_chooser(self, features: list, inserting: bool, unmarked: bool):
        from flextrans_rule_generator.controller.feature_value_chooser import FeatureValueChooser
        chooser = FeatureValueChooser(self)
        chooser.setWindowTitle(strings.FEATURE_CHOOSER_TITLE)
        chooser.set_features(features)
        chooser.select_flex_feature_value(self.feature)
        chooser.show_unmarked_label(unmarked)
        if chooser.exec() == QDialog.DialogCode.Accepted:
            feat_value = chooser.get_feature_value_chosen()
            if feat_value is not None:
                if unmarked:
                    self.feature.unmarked = feat_value.abbreviation
                else:
                    self.feature.label = feat_value.feature.name if feat_value.feature else ""
                    if FLExFeatureValue.is_greek(feat_value.abbreviation):
                        self.feature.match = feat_value.abbreviation
                        self.feature.value = ""
                    else:
                        self.feature.match = ""
                        self.feature.value = feat_value.abbreviation
                if self.feature.sister_feature_has_a_ranking():
                    max_rankings = self._get_max_rankings()
                    self.feature.assign_rankings_to_sister_features_without_a_ranking(max_rankings)
                self._report_changes_made()
        elif inserting:
            # Undo addition of this feature
            rc = self.feature.parent
            if isinstance(rc, Word):
                self.word.delete_feature(self.feature)
            elif isinstance(rc, Affix):
                self.affix.delete_feature(self.feature)

    # ------------------------------------------------------------------
    # Helpers: find phrase / categories / features for a constituent
    # ------------------------------------------------------------------

    def _find_word_for_category(self) -> Optional[Word]:
        """Walk up from category to its parent Word."""
        if self.category is None:
            return None
        parent = self.category.parent
        if isinstance(parent, Word):
            return parent
        return None

    def _find_phrase_for_word(self, word: Word) -> Optional[Phrase]:
        parent = word.parent
        if isinstance(parent, Phrase):
            return parent
        return None

    def _find_phrase_for_constituent(self, constituent: RuleConstituent) -> Optional[Phrase]:
        """Walk the parent chain until we reach a Phrase."""
        current = constituent
        while current is not None:
            if isinstance(current, Phrase):
                return current
            current = getattr(current, "parent", None)
        return None

    def _get_categories_for_phrase(self, phrase: Phrase):
        if self.flex_data is None:
            return []
        if phrase.type == PhraseType.SOURCE:
            return self.flex_data.source_data.categories
        return self.flex_data.target_data.categories

    def _get_features_for_phrase(self, phrase: Phrase):
        if self.flex_data is None:
            return []
        if phrase.type == PhraseType.SOURCE:
            return self.flex_data.source_data.features
        return self.flex_data.target_data.features

    def _flex_category_has_valid_features(self, flex_categories) -> bool:
        cat = self.word.get_category_of_word_or_corresponding_source_word()
        if cat is None:
            return False
        s_cat = cat.name
        for fc in flex_categories:
            if fc.abbreviation == s_cat:
                return len(fc.valid_features) > 0
        return False

    def _get_max_rankings(self) -> int:
        self.word = self.feature.get_word()
        cat = self.word.get_category_of_word_or_corresponding_source_word()
        return self._calculate_max_rankings(cat)

    def _calculate_max_rankings(self, cat) -> int:
        max_rankings = 0
        phrase = self.feature.get_phrase()
        if phrase is not None and phrase.type == PhraseType.TARGET:
            flex_features = self.flex_data.target_data.get_features_for_category(cat)
        else:
            flex_features = self.flex_data.source_data.get_features_for_category(cat)
        max_rankings = len(flex_features)
        if self.rule_generator:
            for feature_set in self.rule_generator.disjoint_feature_sets:
                if feature_set.has_flex_feature_in_list(flex_features):
                    max_rankings += 1
        return max_rankings

    def _is_ok_to_show_disjoint_features_editor(self) -> bool:
        if self.flex_data is None:
            return False
        for f in self.flex_data.target_data.features:
            if f.name == strings.DISJOINT_NUMBER:
                has_sg = any(v.abbreviation == strings.DISJOINT_SG for v in f.values)
                has_pl = any(v.abbreviation == strings.DISJOINT_PL for v in f.values)
                if has_sg and has_pl:
                    return True
        return False

    def _enable_disable_create_permutations(self, rule):
        """Enable/disable create permutations combo based on rule state."""
        if rule is None:
            return
        # Java enables this when target phrase has > 1 word and one is marked as head
        target_phrase = rule.target.phrase
        has_head = any(w.head == HeadValue.YES for w in target_phrase.words)
        has_multiple_words = len(target_phrase.words) > 1
        self.create_permutations_combo.setEnabled(has_head and has_multiple_words)

    # ------------------------------------------------------------------
    # Context menu enable/disable adjustment
    # ------------------------------------------------------------------

    def _adjust_rule_context_menu(self, index: int):
        if not self.rule_generator:
            return
        count = len(self.rule_generator.rules)
        self.rule_act_move_up.setEnabled(index > 0)
        self.rule_act_move_down.setEnabled(index < count - 1)

    def _adjust_word_context_menu(self):
        if self.word is None:
            return
        phrase = self._get_parent_phrase()
        if phrase is None:
            return
        phrase_type = phrase.type
        index = self._word_index_in_phrase(phrase)
        if index < 0:
            return
        index_last = len(phrase.words) - 1
        self.word_act_move_left.setEnabled(index > 0)
        self.word_act_move_right.setEnabled(index < index_last)
        self.word_act_delete.setEnabled(not (index == 0 and index_last == 0))
        # Category: disable if word already has a category
        cat = self.word.get_category_of_word_or_corresponding_source_word()
        self.word_act_insert_category.setEnabled(cat is None or len(cat.name) == 0)
        # Head marking: only on target words
        if phrase_type == PhraseType.SOURCE:
            self.word_act_mark_as_head.setEnabled(False)
            self.word_act_remove_head_marking.setEnabled(False)
        else:
            self.word_act_mark_as_head.setEnabled(self.word.head != HeadValue.YES)
            self.word_act_remove_head_marking.setEnabled(self.word.head == HeadValue.YES)
        # Prefix/suffix: only if no affixes yet
        has_affixes = len(self.word.affixes) > 0
        self.word_act_insert_prefix.setEnabled(not has_affixes)
        self.word_act_insert_suffix.setEnabled(not has_affixes)
        # Feature: enable based on valid features for category
        if self.flex_data:
            flex_categories = self.flex_data.get_flex_categories_for_phrase(phrase_type)
            self.word_act_insert_feature.setEnabled(self._flex_category_has_valid_features(flex_categories))
        else:
            self.word_act_insert_feature.setEnabled(False)

    def _adjust_affix_context_menu(self):
        if self.affix is None:
            return
        word = self._get_parent_word_for_affix()
        if word is None:
            return
        index = self._affix_index_in_word(word)
        if index < 0:
            return
        index_last = len(word.affixes) - 1
        self.affix_act_move_left.setEnabled(index > 0)
        self.affix_act_move_right.setEnabled(index < index_last)
        # Insert feature: enable based on valid features
        if self.flex_data:
            phrase = self._find_phrase_for_word(word)
            if phrase:
                flex_categories = self.flex_data.get_flex_categories_for_phrase(phrase.type)
                self.affix_act_insert_feature.setEnabled(self._flex_category_has_valid_features(flex_categories))
            else:
                self.affix_act_insert_feature.setEnabled(False)
        else:
            self.affix_act_insert_feature.setEnabled(False)

    def _adjust_feature_context_menu(self):
        if self.feature is None:
            return
        this_word = Word()
        rc = self.feature.parent
        if isinstance(rc, Word):
            this_word = rc
        elif isinstance(rc, Affix):
            rc2 = rc.parent
            if isinstance(rc2, Word):
                this_word = rc2
        phrase = this_word.parent
        if phrase is not None and isinstance(phrase, Phrase) and phrase.type == PhraseType.TARGET:
            self.feature_act_edit_ranking.setEnabled(this_word.has_more_than_one_feature())
        else:
            self.feature_act_edit_ranking.setEnabled(False)
        self.feature_act_edit_unmarked.setEnabled(True)
        self.feature_act_delete_unmarked.setEnabled(len(self.feature.unmarked) > 0)
        self.feature_act_delete_ranking.setEnabled(self.feature.ranking > 0)

    # ------------------------------------------------------------------
    # Dirty tracking / save / report changes
    # ------------------------------------------------------------------

    def _mark_dirty(self):
        self._is_dirty = True
        self._show_change_status_on_form()

    def _show_change_status_on_form(self):
        title = strings.FORM_TITLE
        if self._is_dirty:
            title += "*"
        self.setWindowTitle(title)

    def _report_changes_made(self):
        self._show_rule_in_web_page()
        self._mark_dirty()

    def _save(self):
        if self.provider and self.rule_file_path:
            self.provider.save_data_to_file(self.rule_file_path)
            self._is_dirty = False
            self._show_change_status_on_form()

    # ------------------------------------------------------------------
    # Validity checking
    # ------------------------------------------------------------------

    def _rule_is_valid(self, rule: FLExTransRule) -> bool:
        checker = ValidityChecker()
        checker.rule = rule
        if not checker.check_source_words_have_categories():
            self._show_validity_message(
                strings.VALIDITY_CATEGORY.format(rule.name),
                strings.VALIDITY_SOURCE_WORD_MISSING_CATEGORY,
            )
            return False
        if not checker.check_target_has_feature():
            self._show_validity_message(
                strings.VALIDITY_FEATURE.format(rule.name),
                strings.VALIDITY_NO_FEATURES,
            )
            return False
        if not checker.check_target_word_marked_as_head():
            self._show_validity_message(
                strings.VALIDITY_HEAD.format(rule.name),
                strings.VALIDITY_NO_HEAD,
            )
            return False
        return True

    def _show_validity_message(self, header_text: str, content: str):
        QMessageBox.critical(self, strings.VALIDITY_HEADER, f"{header_text}\n\n{content}")

    def _check_validity_of_all_rules(self) -> bool:
        if not self.rule_generator:
            return True
        for rule in self.rule_generator.rules:
            if not self._rule_is_valid(rule):
                return False
        return True

    def _save_and_exit_if_valid(self, exit_code: str, is_valid: bool):
        self._save()
        if is_valid:
            self.exit_code = exit_code
            self.close()

    # ------------------------------------------------------------------
    # Toolbar button handlers
    # ------------------------------------------------------------------

    def _on_test_in_lrt(self):
        self.request_lrt = True
        self._save()
        self.close()

    def _on_save_clicked(self):
        self._save()

    def _on_save_and_write(self):
        rule_index = self._current_rule_index()
        if rule_index < 0:
            return
        rule = self.rule_generator.rules[rule_index]
        is_valid = self._rule_is_valid(rule)
        self._save_and_exit_if_valid(f"1 {rule_index}", is_valid)

    def _on_save_and_write_all(self):
        is_valid = self._check_validity_of_all_rules()
        self._save_and_exit_if_valid("2", is_valid)

    def _on_help(self):
        QMessageBox.information(
            self,
            strings.BTN_HELP,
            "FLExTrans Rule Generator\n\n"
            "Right-click on rules or tree elements to edit them.\n\n"
            "Use the toolbar buttons to save and generate transfer rules.",
        )

    # ------------------------------------------------------------------
    # Test data (source text) display
    # ------------------------------------------------------------------

    def set_test_data_file(self, file_path: str):
        self._test_data_file = file_path
        if WEBENGINE_AVAILABLE:
            url = QUrl.fromLocalFile(file_path)
            self.source_text_view.setUrl(url)
        else:
            # For QTextBrowser, read file content and display as HTML
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.source_text_view.setHtml(f"<pre>{content}</pre>")
            except Exception:
                self.source_text_view.setHtml("")

    # ------------------------------------------------------------------
    # Settings persistence
    # ------------------------------------------------------------------

    def _retrieve_settings(self):
        settings = QSettings("SIL", "FLExTransRuleGenerator")
        geometry = settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        self.last_selected_rule = int(settings.value("LastRule", 0))

    def _save_settings(self):
        settings = QSettings("SIL", "FLExTransRuleGenerator")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("LastRule", self.last_selected_rule)

    # ------------------------------------------------------------------
    # Close event
    # ------------------------------------------------------------------

    def closeEvent(self, event):
        if self._is_dirty:
            reply = QMessageBox.question(
                self,
                strings.FORM_TITLE,
                "Save changes before closing?",
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No
                | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Yes,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._save()
            elif reply == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return
        self._save_settings()
        super().closeEvent(event)
