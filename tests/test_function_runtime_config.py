from __future__ import annotations

import ast
import json
from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_durable_task_scheduler_uses_supported_extension_contract():
    host = json.loads((ROOT / "src" / "host.json").read_text(encoding="utf-8"))
    provider = host["extensions"]["durableTask"]["storageProvider"]

    assert host["extensionBundle"]["version"] == "[4.32.0, 5.0.0)"
    assert provider == {
        "type": "azureManaged",
        "connectionStringName": "DURABLE_TASK_SCHEDULER_CONNECTION_STRING",
    }


def test_python_trigger_bindings_use_runtime_compatible_parameters():
    tree = ast.parse((ROOT / "src" / "function_app.py").read_text(encoding="utf-8"))
    functions = {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }

    assert functions["healthz"].args.args[0].arg == "req"
    partition_annotation = functions["collect_partition"].args.args[0].annotation
    assert isinstance(partition_annotation, ast.Name)
    assert partition_annotation.id == "dict"
