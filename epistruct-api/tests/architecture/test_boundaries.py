import ast
import pathlib

import pytest

MODULES = ["auth", "knowledge", "space", "ai_pipeline"]


@pytest.mark.parametrize("module", MODULES)
def test_module_does_not_import_other_internals(module: str) -> None:
    module_path = pathlib.Path(f"src/modules/{module}")
    for py_file in module_path.rglob("*.py"):
        if py_file.name == "__init__.py":
            continue
        tree = ast.parse(py_file.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                for other in MODULES:
                    if other == module:
                        continue
                    if node.module.startswith(f"src.modules.{other}."):
                        pytest.fail(
                            f"{py_file}: '{other}' 내부 직접 import 금지. "
                            f"'src.modules.{other}' 공개 API(__init__)만 사용."
                        )
