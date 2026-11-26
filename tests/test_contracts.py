"""The generated files match the pinned API description, and every operation has a step."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys

import yaml
from support import BUNDLE

SPEC = json.loads((BUNDLE / "reference" / "openapi.json").read_text(encoding="utf-8"))
OPERATIONS = {
    op["operationId"]
    for item in SPEC["paths"].values()
    for method, op in item.items()
    if method in ("get", "post", "put", "patch", "delete")
}
#: Step names start with what the step does.
VERBS = {
    "Look", "Check", "List", "Get", "Calculate", "Convert", "Summarize", "Validate",
    "Estimate", "Find", "Resolve", "Verify", "Test",
}  # fmt: skip


def load(path: str):
    return yaml.safe_load((BUNDLE / path).read_text(encoding="utf-8"))


def test_the_generated_files_match_the_pinned_api_description():
    result = subprocess.run(
        [sys.executable, "scripts/build_contracts.py", "--check"],
        cwd=BUNDLE,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_every_api_operation_has_its_own_step():
    registry = json.loads((BUNDLE / "runtime" / "registry.json").read_text(encoding="utf-8"))
    pinned = hashlib.sha256((BUNDLE / "reference" / "openapi.json").read_bytes()).hexdigest()
    assert registry["source"]["sha256"] == pinned
    assert len(OPERATIONS) == registry["source"]["operations"] == 40
    called = {step["operation"] for step in registry["steps"].values()}
    assert called == OPERATIONS


def test_steps_forms_and_actions_list_the_same_inputs():
    operations = load("contracts/operation_manifest.yaml")["operations"]
    forms = {f["operation_id"]: f for f in load("contracts/step_ui_manifest.yaml")["forms"]}
    actions = {a["action_id"]: a for a in load("ui/actions/actions.yaml")["actions"]}
    assert len(operations) == len(forms) == len(actions) == 46
    for operation in operations:
        name = operation["operation_id"]
        inputs = [i["name"] for i in operation["inputs"] if i["name"] != "connection_ref"]
        fields = forms[name]["fields"]
        assert [f["name"] for f in fields] == inputs, name
        assert all(f["label"] and f["help_text"] for f in fields), name
        params = [p["name"] for p in actions[name]["parameters"] if p["name"] != "connection_ref"]
        assert params == inputs, name
        assert actions[name]["mutates_platform"] is False
        assert operation["display_name"].split()[0] in VERBS, operation["display_name"]


def test_no_step_reads_a_whole_dataset():
    for operation in load("contracts/operation_manifest.yaml")["operations"]:
        names = {i["name"] for i in operation["inputs"]}
        assert not names & {"all_pages", "export", "dump", "download"}, operation["operation_id"]


def test_the_manifest_declares_no_change_and_one_host():
    manifest = load("extension.yaml")
    assert manifest["external_effects"] == []
    assert manifest["egress"]["hosts"] == ["www.freightutils.com"]
    assert re.search(r"\b40 operations\b", manifest["description"])


def test_every_page_says_whether_it_needs_a_project():
    pages = [p["ref"] for p in load("ui/ui_manifest.yaml")["pages"]]
    for ref in pages:
        page = load(f"ui/{ref}")
        assert isinstance(page.get("project_scoped"), bool), ref
        assert page["project_scoped"] is (page["page_id"] == "connection"), ref


def test_the_api_page_is_one_tab_with_a_section_per_group():
    page = load("ui/pages/freightutils-api.yaml")
    sections = [c for c in page["components"] if c.get("collapsible")]
    assert len(sections) == 10  # everyday + 9 groups
    listed = sum(c["body"].count("\n- **") + c["body"].startswith("- **") for c in sections)
    assert listed == 46
