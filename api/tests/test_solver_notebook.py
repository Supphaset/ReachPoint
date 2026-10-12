"""Runs the split-solver notebook end to end; its asserts are checks (a)–(d) from the design doc."""

from pathlib import Path

import pytest

nbformat = pytest.importorskip("nbformat")
nbclient = pytest.importorskip("nbclient")
pytest.importorskip("ortools")

NOTEBOOK = Path(__file__).resolve().parents[1] / "notebooks" / "split-solver.ipynb"


def test_notebook_runs_and_its_checks_pass():
    nb = nbformat.read(NOTEBOOK, as_version=4)
    nbclient.NotebookClient(nb, kernel_name="python3", timeout=120,
                            resources={"metadata": {"path": str(NOTEBOOK.parent)}}).execute()
