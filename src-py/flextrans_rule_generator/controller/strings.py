# Controller/view strings (matching Java RuleGen_en.properties)
# Copyright (c) 2024-2026 SIL International
# This software is licensed under the LGPL, version 2.1 or later
# (http://www.gnu.org/licenses/lgpl-2.1.html)

# Main form
FORM_TITLE = "Rule Assistant for FLExTrans"
RULE_NAME = "Rule Name:"
DESCRIPTION = "Description:"
CREATE_PERMUTATIONS = "Create permutations:"
SOURCE_TEXT = "(Right-click to edit)"
OVERWRITE_RULES = "Overwrite rules(s)"
SET_DISJOINT_FEATURES = "Set disjoint features"
YES = "Yes"
NO = "No"

# Chooser titles
CATEGORY_CHOOSER_TITLE = "FLEx Category Chooser"
FEATURE_CHOOSER_TITLE = "FLEx Feature Value Chooser"
FEATURE_VALUE_CHOOSER_TITLE = "FLEx Feature Value Chooser"
CHOOSER_UNMARKED_NOTICE = "When this feature is absent,\n use the following feature : value by default."

# Context menu items
CM_DELETE = "Delete"
CM_DUPLICATE = "Duplicate"
CM_EDIT = "Edit"
CM_INSERT_AFTER = "Insert new after"
CM_INSERT_BEFORE = "Insert new before"
CM_INSERT_CATEGORY = "Insert category"
CM_INSERT_FEATURE = "Insert feature"
CM_INSERT_PREFIX = "Insert prefix"
CM_INSERT_PREFIX_AFTER = "Insert new prefix after"
CM_INSERT_PREFIX_BEFORE = "Insert new prefix before"
CM_INSERT_SUFFIX = "Insert suffix"
CM_INSERT_SUFFIX_AFTER = "Insert new suffix after"
CM_INSERT_SUFFIX_BEFORE = "Insert new suffix before"
CM_MARK_AS_HEAD = "Mark as head"
CM_REMOVE_HEAD_MARKING = "Remove head marking"
CM_CHANGE_NUMBER = "Change number"
CM_MOVE_DOWN = "Move down"
CM_MOVE_LEFT = "Move left"
CM_MOVE_RIGHT = "Move right"
CM_MOVE_UP = "Move up"
CM_EDIT_UNMARKED = "Edit unmarked"
CM_DELETE_UNMARKED = "Delete unmarked"
CM_EDIT_RANKING = "Edit ranking"
CM_DELETE_RANKING = "Delete ranking"
CM_TOGGLE_AFFIX_TYPE = "Toggle affix type"

# Toolbar buttons
BTN_TEST_IN_LRT = "Test in LRT"
BTN_SAVE = "Save"
BTN_SAVE_AND_WRITE = "Save && Write"
BTN_SAVE_AND_WRITE_ALL = "Save && Write All"
BTN_HELP = "Help"

# Validity messages (matching Java RuleGen_en.properties)
VALIDITY_HEADER = "Problem with rule"
VALIDITY_CATEGORY = 'Missing category in rule "{0}"'
VALIDITY_FEATURE = 'No features mentioned in rule "{0}"'
VALIDITY_HEAD = 'No word marked as head in rule "{0}"'
VALIDITY_SOURCE_WORD_MISSING_CATEGORY = "One or more source words do not have a category.  Please insert a category for every source word."
VALIDITY_NO_FEATURES = "No word or affix in the target has a feature.  Please insert at least one feature."
VALIDITY_NO_HEAD = "No word has been marked as the head in the target phrase.  Please mark one word as the head."

# Feature ranking dialog
FEATURE_RANKING_HEADER = "Ranking for Feature"
FEATURE_RANKING_CONTENT = "Feature ranking"
FEATURE_RANKING_CHOOSE = "Choose ranking:"

# Word number chooser dialog
ID_CHOOSER_HEADER = "Word Number"
ID_CHOOSER_CONTENT = "Word number"
ID_CHOOSER_CHOOSE = "Choose word number:"

# Disjoint features validity
DISJOINT_VALIDITY_HEADER = "Missing required FLEx feature"
DISJOINT_VALIDITY_HEADERTEXT = "Missing FLEx feature"
DISJOINT_VALIDITY_MESSAGE = ('The target language is missing a FLEx feature named "number" '
    'and/or that feature does not have both a "sg" value and a "pl" value.  '
    'This feature and these two values must be spelled exactly this way.\n'
    'You must have such a feature in order to use this editor.\n'
    'Add this feature to your target FLEx project and then re-run the Rule Assistant.')

# LRT dialog
LRT_TITLE = "Test in the Live Rule Tester"
LRT_HEADER = "Choose which save option you want."
LRT_CONTENT = "Choose your option."

# Create permutations values
PERM_NO = "No"
PERM_NOT_HEAD = "Omitting head-only rule"
PERM_WITH_HEAD = "Including head-only rule"

# Disjoint feature constants
DISJOINT_NUMBER = "number"
DISJOINT_SG = "sg"
DISJOINT_PL = "pl"

# File loading/saving
FILE_ASK_SAVE_HEADER = "Changes may have been made."
FILE_ASK_SAVE_CONTENT = "Do you want to save any changes?"
FILE_ERROR_LOAD_CONTENT = "Could not load data from file:\n"
FILE_ERROR_LOAD_HEADER = "Could not load data"
FILE_ERROR_SAVE_CONTENT = "Could not save data to file:\n"
FILE_ERROR_SAVE_HEADER = "Could not save data"
FILE_ERROR = "Error"

# About dialog
ABOUT_HEADER = "About FLExTrans Rule Assistant"
VERSION_NUMBER = "1.6.0"
