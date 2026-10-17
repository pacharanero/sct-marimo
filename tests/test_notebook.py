# SPDX-FileCopyrightText: 2026 Marcus Baw and Baw Medical Ltd
# SPDX-License-Identifier: AGPL-3.0-or-later

from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType

import marimo

NOTEBOOK = Path(__file__).parents[1] / "notebooks" / "concept-set-workbench.py"


def load_notebook() -> ModuleType:
    spec = spec_from_file_location("concept_set_workbench", NOTEBOOK)
    assert spec is not None
    assert spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_notebook_starts_without_running_a_terminology_query() -> None:
    module = load_notebook()

    outputs, definitions = module.app.run()

    assert isinstance(module.app, marimo.App)
    assert outputs
    assert definitions["db_path"] is None
    assert definitions["get_submission"]() is None
    assert definitions["get_result"]() is None
