# Plan: Update Python Code to Mirror Java Version

## Summary of Differences Found

The Python port (from the old C# version) is structurally sound but has significant gaps
compared to the current Java version. Below is the prioritized plan to bring it into parity.

---

## Phase 1: Model Layer — Missing Properties, Methods & Enums

### 1.1 Add missing enums as proper Python Enums
- **PermutationsValue**: Java has `no`, `not_head`, `with_head` — Python currently uses a plain string `"no"` in `FLExTransRule.create_permutations`. Need a proper enum with a `get_string()` helper.
- **OverwriteRulesValue**: Java has `no`, `yes` enum — Python uses `bool`. Need an enum to match XML serialization.
- **HeadValue**: Python has `YES`/`NO` (uppercase) vs Java `yes`/`no` (lowercase). Needs to match for XML serialization.

### 1.2 `RuleConstituent` — update `produce_span` / `produce_to_app`
- Java uses `onmousedown` event, Python uses `onclick` + `oncontextmenu` — **update to match Java's `onmousedown` only**
- Java passes `event` arg in `toApp('...', event)`, Python only passes `msg` — **add event param**
- Add `bundle`/locale support (or a Python equivalent for i18n resource strings)
- Add `ensure_bundle_exists()` equivalent

### 1.3 `Feature` — major gaps
- **Missing fields**: `value`, `unmarked_default` (`unmarked`), `ranking` — Python only has `match` and `label`
- **Missing methods**:
  - `get_match_or_value()` — returns match if set, else value
  - `get_phrase()` — navigates parent chain to find containing Phrase
  - `get_word()` — navigates parent chain to find containing Word
  - `assign_rankings_to_sister_features_without_a_ranking(max_rankings)`
  - `sister_feature_has_a_ranking()`
  - `swap_ranking_of_sister_feature_with_ranking(new_ranking, old_ranking)`
  - `remove_rankings_from_sister_features()`
  - `format_unmarked()` for HTML
- **`produce_html`** — completely different: Java takes `(bundle, isHead)`, renders ranking, unmarked default, uses `<table>` structure; Python produces a simplified version with `<li>` wrapper
- **`duplicate`** — must also copy `value`, `unmarked`, `ranking`

### 1.4 `ConstituentWithFeatures` — HTML structure
- Java `produce_html_for_features` takes `(bundle, sb, isHead)` and wraps features in `<li><table>` with `<tr><td>` per feature
- Python version is flat concatenation — **needs to match Java's table structure**

### 1.5 `Word` — missing methods and HTML differences
- **Missing methods**:
  - `get_category_of_word_or_corresponding_source_word()` — looks up source word by ID
  - `get_all_features_in_word()` — collects word + affix features
  - `has_more_than_one_feature()`
  - `ranking_is_available(ranking)`
- **`produce_html`** — major structural differences:
  - Java uses `<table class="tf-nc">` with `<tr><td>` rows for word and category
  - Java has `produceHtmlOfCategory()` helper that handles source vs target category display
  - Java orders: prefixes first, then features, then suffixes (using stream filter on AffixType)
  - Python has a simpler flat structure
- **`duplicate`** — Java takes `boolean assignNewId` param, Python doesn't

### 1.6 `Category` — missing methods
- **Missing**: `get_phrase()` — navigates parent chain
- **Missing**: `produce_html_target(bundle, word_id)` — special HTML for target categories
- **Missing**: `produce_span_for_target()` helper
- **`produce_html`** — Java uses `produceSpan("category", "c")` (no `tf-nc`), Python adds `tf-nc`

### 1.7 `Phrase` — missing methods
- **Missing methods**:
  - `get_features_in_use()` — collects used FLEx features across words
  - `get_features_in_use_for_category(categories, cat)` — with category validation
  - `get_id_of_newly_added_word()` — finds next available ID
  - `insert_word_at(word, index)` — insert existing word (not just new)
  - `change_id_of_word(index, old_id, new_id)` — swap IDs
  - `get_category_of_word_with_id(word_id)` — look up source word category
- **`insert_new_word_at`** — Java allows index == size (append), Python uses `>=` check (rejects append)
- **`duplicate`** — Java calls `word.duplicate(false)`, Python calls `word.duplicate()` (no assignNewId param)

### 1.8 `FLExTransRule` — missing methods
- **Missing**: `hashCode`/`equals` equivalents (`__hash__`, `__eq__`)
- **`duplicate`** — Java appends localized " - duplicated" suffix to name, sets target phrase type; Python just copies name as-is
- **`__str__`** — Java uses bundle for "name missing" string

### 1.9 `FLExTransRuleGenerator` — type mismatch
- `overwrite_rules`: Python uses `bool`, Java uses `OverwriteRulesValue` enum

### 1.10 `DisjointFeatureSet` — missing methods
- **Missing**: `has_flex_feature_in_list(flex_features)` — checks if all pairings have matching FLEx features
- **Missing**: `remove_pairings_from(index)` — removes pairings from given index
- **Missing**: JavaFX property support (StringProperty, etc.) — need equivalent for UI binding

### 1.11 `Source` and `Target` — missing inheritance
- Java extends `ConstituentWithPhrase`; Python uses standalone classes with `self.phrase` attribute — works but doesn't inherit `RuleConstituent` properties (identifier, parent)

---

## Phase 2: Service Layer — Missing Classes and Logic

### 2.1 Create `validity_checker.py` (ENTIRELY MISSING)
Port `ValidityChecker.java` with:
- `check_source_words_have_categories()`
- `check_target_has_feature()`
- `check_target_word_marked_as_head()`

### 2.2 Update `web_page_producer.py`
- Add ResourceBundle/locale parameter support to `produce_web_page()` and downstream
- Fix JavaScript bridge: add `event` parameter to `toApp()` calls
- Fix CSS path: `treeflex.css` → match Java's path convention or keep if deployed differently
- Fix container element: `<div>` → `<span>` for `tf-tree tf-gap-sm`

### 2.3 Update `xml_backend_provider.py`
- Add file-not-found bootstrapping: create default rule file when file doesn't exist (Java lines 46-66)
- Add error handling (try/except) for load/save operations
- Verify `setCategoryConstituentInWords` equivalent is working correctly

### 2.4 Add `xml_backend_provider_flex_data.py` improvements
- Add error handling
- Verify `set_feature_in_feature_values()` is called correctly after loading

---

## Phase 3: FLEx Model Layer

### 3.1 `FLExData` — missing methods
- `clear()` — clears source and target data
- `get_flex_categories_for_phrase(phrase_type)` — returns categories by phrase type
- `get_features_in_phrase_for_category(phrase_type, cat)` — returns features for category

### 3.2 `FLExFeature` — missing methods
- `set_feature_in_feature_values()` — sets back-reference from values to feature
- Constructor with `(name, values)` parameters
- `__eq__` and `__hash__`

### 3.3 `FLExFeatureValue` — check for `feature` back-reference
- Java has `setFeature(FLExFeature)` on each value; verify Python equivalent exists

### 3.4 `FLExDataBase` — missing `getFeaturesForCategory` method
- Java has `getFeaturesForCategory(Category cat)` that filters features by valid features for a category

---

## Phase 4: Controller/View Layer

### 4.1 Verify `MainController` ↔ `RuleGeneratorControl` parity
The controller is the largest file (~1300 lines Java). Key methods to verify:
- `processItemClickedOn` — context menu handler
- All context menu actions (insert/delete word, affix, feature, category)
- Feature ranking operations
- Disjoint feature handling
- Permutations and overwrite rules UI
- Rule duplicate/delete operations

### 4.2 Verify dialog controllers
- `CategoryChooser` ↔ `FLExCategoryChooserController`
- `FeatureValueChooser` ↔ `FLExFeatureValueChooserController`
- `DisjointFeaturesDialog` ↔ `DisjointFeaturesEditorController`

---

## Phase 5: Localization / i18n

### 5.1 Implement a localization strategy
Java uses `ResourceBundle` throughout. Options for Python:
- Use `gettext` for standard Python i18n
- Use a simple dictionary-based approach matching the Java `.properties` files
- Port the Java `.properties` files to Python format

### 5.2 Update all `produce_html()` methods to use localized strings
Currently Python uses hardcoded strings in `model/strings.py`. These need to either:
- Be connected to a proper i18n system, OR
- At minimum, all string constants need to match Java's resource bundle values

---

## Phase 6: Testing

### 6.1 Port Java unit tests to Python
Java tests exist in `/test/` directory covering model, flexmodel, and service layers.
Create Python equivalents using pytest.

---

## Execution Order

1. **Phase 1** (Model) — Foundation; everything else depends on correct models
2. **Phase 2** (Services) — Core business logic
3. **Phase 3** (FLEx Model) — Data layer
4. **Phase 4** (Controller) — UI alignment (verify after model/service changes)
5. **Phase 5** (i18n) — Can be stubbed initially, refined later
6. **Phase 6** (Testing) — Validate everything works
