# SPDX-FileCopyrightText: 2026 Marcus Baw and Baw Medical Ltd
# SPDX-License-Identifier: AGPL-3.0-or-later

from __future__ import annotations

from pathlib import Path
from shutil import copy2

import pytest

SYNTHETIC_DATABASE = Path(__file__).parent / "fixtures" / "sct-v0.29.0-synthetic.db"


@pytest.fixture
def synthetic_database(tmp_path: Path) -> Path:
    """Copy the reviewed fixture so SQLite sidecars never touch the source tree."""

    destination = tmp_path / "synthetic.db"
    copy2(SYNTHETIC_DATABASE, destination)
    return destination
