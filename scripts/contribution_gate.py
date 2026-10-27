#!/usr/bin/env python3
"""Check the automation delete --all specimen on this fork.

The check is narrow. It looks at the diff against a base revision, the
mirrored test, the delete --all loop, and one pytest. It is not a general
reviewer.

    python3 scripts/contribution_gate.py
    python3 scripts/contribution_gate.py main
"""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {
    "src/prefect/cli/automation.py",
    "tests/events/client/cli/test_automations.py",
}
CODE = ROOT / "src/prefect/cli/automation.py"
TEST = ROOT / "tests/events/client/cli/test_automations.py"
TEST_NAME = "test_deleting_all_automations_continues_past_the_first_page"
PYTEST_ARGS = [
    "uv",
    "run",
    "pytest",
    "tests/events/client/cli/test_automations.py",
    "-k",
    "continues_past_the_first_page",
    "--tb=short",
    "-q",
]


def changed_files(base: str) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", base],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def mirrored_test_present() -> bool:
    tree = ast.parse(TEST.read_text(), filename=str(TEST))
    return any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == TEST_NAME
        for node in ast.walk(tree)
    )


def _reads_automations_from_start(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call):
        return False
    if not isinstance(node.func, ast.Attribute) or node.func.attr != "read_automations":
        return False
    for keyword in node.keywords:
        if keyword.arg == "offset":
            return isinstance(keyword.value, ast.Constant) and keyword.value.value == 0
    return True


def _loop_rereads(node: ast.AST, inside_loop: bool) -> bool:
    if isinstance(node, (ast.While, ast.For, ast.AsyncFor)):
        inside_loop = True
    if inside_loop and _reads_automations_from_start(node):
        return True
    return any(
        _loop_rereads(child, inside_loop) for child in ast.iter_child_nodes(node)
    )


def delete_all_rereads() -> bool:
    tree = ast.parse(CODE.read_text(), filename=str(CODE))
    for node in ast.walk(tree):
        if not isinstance(node, ast.AsyncFunctionDef) or node.name != "delete":
            continue
        for child in ast.walk(node):
            test = getattr(child, "test", None)
            if (
                isinstance(child, ast.If)
                and isinstance(test, ast.Name)
                and test.id == "all"
                and _loop_rereads(child, False)
            ):
                return True
    return False


def run_pytest() -> int:
    return subprocess.run(PYTEST_ARGS, cwd=ROOT).returncode


def report(message: str, *, error: bool = False) -> None:
    print(message, file=sys.stderr if error else sys.stdout, flush=True)


def main() -> int:
    base = sys.argv[1] if len(sys.argv) > 1 else "main"
    failures: list[str] = []

    try:
        changed = changed_files(base)
    except subprocess.CalledProcessError as error:
        report(error.stderr, error=True)
        return 1

    extra = sorted(set(changed) - ALLOWED)
    if extra:
        failures.append("Changed files outside the allowed paths: " + ", ".join(extra))
    else:
        listed = ", ".join(changed) if changed else "none"
        report(f"Allowed paths: {listed}")

    if mirrored_test_present():
        report(f"Mirrored test: {TEST_NAME}")
    else:
        failures.append(f"Missing mirrored test {TEST_NAME}")

    if delete_all_rereads():
        report("Offset loop: delete --all re-reads from the start inside a loop")
    else:
        failures.append(
            "delete --all does not re-read automations from the start inside a loop"
        )

    pytest_code = run_pytest()
    if pytest_code == 0:
        report("Targeted pytest: passed")
    else:
        failures.append(f"Targeted pytest exited {pytest_code}")

    for failure in failures:
        report(f"Failed: {failure}", error=True)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
