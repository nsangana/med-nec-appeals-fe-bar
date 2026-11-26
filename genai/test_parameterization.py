"""Static guards for the catalog/schema parameterization (job parameters :catalog / :schema, notebook widgets).

SQL
- No pipeline/dashboards/genie/governance SQL file hard-codes the build schema outside comments.
- Every SQL file that is a SQL task starts with USE CATALOG / USE SCHEMA IDENTIFIER(...) before any object is touched.
- Only the agreed parameter markers appear in SQL code: :catalog, :schema, :max_appeals.
- The generation cap is LIMIT CAST(:max_appeals AS INT) (a plain LIMIT :n fails when the value is a string).

Notebooks
- No notebook interpolates catalog/schema values into quoted SQL text.
- The identifier validation in each parameterized notebook is executed (extracted from the AST, run with a fake
  dbutils) and rejects anything that is not a plain identifier, and it accepts the live defaults.
"""
import ast
import pathlib
import re

import pytest

from test_sql_quotes import _strip_comments  # genai/ is on sys.path under pytest's default import mode

ROOT = pathlib.Path(__file__).resolve().parents[1]
SQL_GLOBS = ("pipeline", "dashboards", "genie", "governance")
SQL_FILES = sorted(p for d in SQL_GLOBS for p in (ROOT / d).glob("*.sql"))
LIVE_LITERAL = "appeals_hackathon_catalog.fe_bar_appeals"
ALLOWED_MARKERS = {"catalog", "schema", "max_appeals"}
# 03_lineage reads system tables with plain predicates and has no USE; every other SQL file is a SQL task that sets the session.
NO_USE_FILES = {"governance/03_lineage.sql"}

NOTEBOOKS = sorted((ROOT / "pipeline").glob("[0-9][0-9]_*.py"))
PARAMETERIZED_NOTEBOOKS = [ROOT / "pipeline" / n for n in (
    "00_bootstrap.py", "10_generate_raw_data.py", "40_render_pdfs.py", "50_lakebase_sync.py",
    "60_evaluate.py", "65_genai_evaluate.py")]


def _rel(p):
    return str(p.relative_to(ROOT))


def _code(p):
    """SQL text with comments removed and string-literal contents blanked (markers are never bound inside literals)."""
    body = _strip_comments(p.read_text())
    body = re.sub(r"'(?:[^']|'')*'", "''", body)
    return body


def _code_with_literals(p):
    return _strip_comments(p.read_text())


# ----------------------------------------------------------------------------------------------- SQL

def test_sql_files_discovered():
    assert len(SQL_FILES) >= 10, [ _rel(p) for p in SQL_FILES]


@pytest.mark.parametrize("path", SQL_FILES, ids=_rel)
def test_no_hard_coded_build_schema_in_sql(path):
    code = _code_with_literals(path)
    assert LIVE_LITERAL not in code, f"{_rel(path)} hard-codes {LIVE_LITERAL} outside comments"
    assert "'appeals_hackathon_catalog'" not in code, f"{_rel(path)} hard-codes the catalog name as a literal"


@pytest.mark.parametrize("path", SQL_FILES, ids=_rel)
def test_only_agreed_parameter_markers(path):
    markers = set(re.findall(r"(?<![:\w]):([A-Za-z_][A-Za-z0-9_]*)", _code(path)))
    assert markers <= ALLOWED_MARKERS, f"{_rel(path)} uses unexpected parameter markers {sorted(markers - ALLOWED_MARKERS)}"


@pytest.mark.parametrize("path", [p for p in SQL_FILES if _rel(p) not in NO_USE_FILES], ids=_rel)
def test_sql_task_sets_catalog_and_schema_before_first_statement(path):
    code = _code(path)
    literal_code = _code_with_literals(path)  # the schema-creation line has a '.' literal
    use_cat = code.find("USE CATALOG IDENTIFIER(:catalog)")
    use_sch = code.find("USE SCHEMA IDENTIFIER(:schema)")
    assert use_cat >= 0, f"{_rel(path)}: missing USE CATALOG IDENTIFIER(:catalog)"
    assert use_sch > use_cat, f"{_rel(path)}: USE SCHEMA IDENTIFIER(:schema) must follow USE CATALOG"
    # Everything before USE SCHEMA may only be the schema-creation statement (cost_views creates the schema first).
    before = literal_code[:literal_code.find("USE SCHEMA IDENTIFIER(:schema)")]
    stripped = re.sub(r"CREATE SCHEMA IF NOT EXISTS IDENTIFIER\(:catalog \|\| '\.' \|\| :schema\);?", "", before)
    assert not re.search(r"\b(CREATE|ALTER|MERGE|DELETE|GRANT|SELECT|INSERT|DROP|WITH|SHOW)\b", stripped), (
        f"{_rel(path)}: an object statement runs before USE SCHEMA")


def test_no_fixed_limit_on_generation_cap():
    code = _code(ROOT / "pipeline" / "30_generate_appeals.sql")
    assert not re.search(r"\bLIMIT\s+\d+\b", code), "a numeric LIMIT is left in 30_generate_appeals.sql"
    assert re.search(r"LIMIT\s+CAST\(\s*:max_appeals\s+AS\s+INT\s*\)", code), "LIMIT CAST(:max_appeals AS INT) missing"


def test_metric_view_sources_are_unqualified():
    code = _code_with_literals(ROOT / "genie" / "01_appeals_metrics.sql")
    assert "source: gold_denial_worklist" in code
    assert "FROM cost_assumptions" in code or "FROM cost_assumptions c" in code


# ----------------------------------------------------------------------------------------- notebooks

LITERAL_DEFAULT_LINE = re.compile(r'(_DEFAULT\s*=|_param\(\s*"(catalog|schema)"\s*,)')


@pytest.mark.parametrize("path", NOTEBOOKS, ids=_rel)
def test_notebook_parses(path):
    ast.parse(path.read_text(), filename=str(path))


@pytest.mark.parametrize("path", NOTEBOOKS, ids=_rel)
def test_notebook_has_no_hard_coded_build_names(path):
    bad = []
    for n, line in enumerate(path.read_text().splitlines(), 1):
        if line.lstrip().startswith("#"):
            continue
        if ("appeals_hackathon_catalog" in line or '"fe_bar_appeals"' in line) and not LITERAL_DEFAULT_LINE.search(line):
            bad.append(n)
    assert not bad, f"{_rel(path)}: hard-coded catalog/schema outside the default line, lines {bad}"


@pytest.mark.parametrize("path", NOTEBOOKS, ids=_rel)
def test_notebook_does_not_quote_values_into_sql(path):
    text = path.read_text()
    assert not re.search(r"'\{(CAT|SCH|CATALOG|SCHEMA|FQ)\}'", text), f"{_rel(path)} quotes a build name into SQL text"


@pytest.mark.parametrize("path", PARAMETERIZED_NOTEBOOKS, ids=_rel)
def test_parameterized_notebook_validates_identifiers(path):
    text = path.read_text()
    assert 'fullmatch(r"[A-Za-z0-9_]+"' in text, f"{_rel(path)} has no identifier regex"
    assert "_param(" in text or "widgets.get(" in text, f"{_rel(path)} reads no widgets"


def _validation_namespace(path, widget_values=None, dbutils_present=True):
    """Execute only the parameter block of a notebook: `import re`, `_param`, the default/validated assignments,
    and the validation `if`/`for` statements. Everything else (Spark, SDK, MLflow) is left out on purpose."""
    tree = ast.parse(path.read_text(), filename=str(path))
    keep_assign = {"CATALOG_DEFAULT", "SCHEMA_DEFAULT", "CATALOG", "SCHEMA", "CAT", "SCH",
                   "ENABLE_LAKEBASE_SYNC_RAW", "ENABLE_LAKEBASE_SYNC"}
    nodes = []
    for node in tree.body:
        src = ast.unparse(node)
        if isinstance(node, ast.Import) and any(a.name == "re" for a in node.names):
            nodes.append(node)
        elif isinstance(node, ast.FunctionDef) and node.name == "_param":
            nodes.append(node)
        elif isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in keep_assign for t in node.targets):
            nodes.append(node)
        elif isinstance(node, (ast.For, ast.If)) and ("fullmatch" in src or "ENABLE_LAKEBASE_SYNC_RAW" in src):
            nodes.append(node)
    module = ast.Module(body=nodes, type_ignores=[])
    ast.fix_missing_locations(module)

    class _Widgets:
        """Widget semantics: text() declares the widget with its default; get() returns the job-supplied value if any."""
        def __init__(self):
            self.declared = {}

        def text(self, name, default):
            self.declared[name] = default

        def get(self, name):
            return (widget_values or {}).get(name, self.declared[name])

    ns = {}
    if dbutils_present:
        class _DBU:
            widgets = _Widgets()
        ns["dbutils"] = _DBU()
    exec(compile(module, str(path), "exec"), ns)  # noqa: S102 - trusted repo source, parameter block only
    return ns


@pytest.mark.parametrize("path", PARAMETERIZED_NOTEBOOKS, ids=_rel)
def test_live_defaults_when_no_widgets(path):
    ns = _validation_namespace(path, dbutils_present=False)
    assert (ns["CATALOG"] if "CATALOG" in ns else ns["CAT"]) == "appeals_hackathon_catalog"
    assert (ns["SCHEMA"] if "SCHEMA" in ns else ns["SCH"]) == "fe_bar_appeals"


@pytest.mark.parametrize("path", PARAMETERIZED_NOTEBOOKS, ids=_rel)
def test_accepts_plain_identifiers(path):
    ns = _validation_namespace(path, {"catalog": "my_cat_01", "schema": "Schema_2"})
    assert (ns.get("CATALOG") or ns.get("CAT")) == "my_cat_01"
    assert (ns.get("SCHEMA") or ns.get("SCH")) == "Schema_2"


@pytest.mark.parametrize("bad", ["", "a.b", "bad-name", "x; DROP TABLE y", "tab le", "a'b", "a`b"])
@pytest.mark.parametrize("path", PARAMETERIZED_NOTEBOOKS, ids=_rel)
def test_rejects_non_identifiers(path, bad):
    with pytest.raises(ValueError):
        _validation_namespace(path, {"catalog": bad, "schema": "fe_bar_appeals"})
    with pytest.raises(ValueError):
        _validation_namespace(path, {"catalog": "appeals_hackathon_catalog", "schema": bad})


@pytest.mark.parametrize("flag,ok", [("true", True), ("false", False), ("TRUE", True), (" False ", False)])
def test_lakebase_flag_values(flag, ok):
    path = ROOT / "pipeline" / "50_lakebase_sync.py"
    ns = _validation_namespace(path, {"catalog": "appeals_hackathon_catalog", "schema": "fe_bar_appeals",
                                      "enable_lakebase_sync": flag})
    assert ns["ENABLE_LAKEBASE_SYNC"] is ok


@pytest.mark.parametrize("flag", ["yes", "1", "", "true;"])
def test_lakebase_flag_rejects_other_values(flag):
    path = ROOT / "pipeline" / "50_lakebase_sync.py"
    with pytest.raises(ValueError):
        _validation_namespace(path, {"catalog": "appeals_hackathon_catalog", "schema": "fe_bar_appeals",
                                     "enable_lakebase_sync": flag})


def test_lakebase_sync_skips_lakebase_steps_when_disabled():
    text = (ROOT / "pipeline" / "50_lakebase_sync.py").read_text()
    # the synced-table refresh and the review_state copy are both guarded by the flag
    assert text.count("if ENABLE_LAKEBASE_SYNC:") == 2
    assert "trigger_synced_refresh()" in text
    # the Delta MERGE of worklist_serving is NOT guarded (it has no Lakebase dependency)
    merge_idx = text.index("MERGE WITH SCHEMA EVOLUTION")
    assert text.rfind("if ENABLE_LAKEBASE_SYNC:", 0, merge_idx) == -1


def test_review_state_uc_exists_when_lakebase_sync_disabled():
    """The metric view and Genie read review_state_uc; the flag-off branch must create it (empty) if missing,
    and only the flag-on branch may replace it."""
    text = (ROOT / "pipeline" / "50_lakebase_sync.py").read_text()
    else_idx = text.index("\nelse:", text.index("if ENABLE_LAKEBASE_SYNC:", text.index("3. Copy Lakebase review_state")))
    true_branch, false_branch = text[:else_idx], text[else_idx:]
    assert "CREATE OR REPLACE TABLE {REVIEW_STATE_UC}" in true_branch
    assert "CREATE OR REPLACE TABLE {REVIEW_STATE_UC}" not in false_branch
    assert "CREATE TABLE IF NOT EXISTS {REVIEW_STATE_UC}" in false_branch
    for col in ("facility_id", "patient_control_number", "encounter_nbr", "status", "last_reviewer",
                "last_action_at", "submitted_at", "deadline_met", "copied_at"):
        assert col in false_branch
