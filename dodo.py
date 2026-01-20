"""
Doit build file for CDS-Bond Basis pipeline.

Run with: doit
"""

import platform
import shutil
import subprocess
import sys
from pathlib import Path

import chartbook

sys.path.insert(1, "./src/")

BASE_DIR = chartbook.env.get_project_root()
DATA_DIR = BASE_DIR / "_data"
OUTPUT_DIR = BASE_DIR / "_output"
OS_TYPE = "nix" if platform.system() != "Windows" else "windows"


def jupyter_execute_notebook(notebook):
    """Execute a Jupyter notebook and save output."""
    return (
        f"jupyter nbconvert --execute --to notebook "
        f'--ClearMetadataPreprocessor.enabled=True --inplace "{notebook}"'
    )


def jupyter_to_html(notebook, output_dir):
    """Convert notebook to HTML."""
    return (
        f'jupyter nbconvert --to html --output-dir="{output_dir}" "{notebook}"'
    )


def task_config():
    """Create necessary directories."""
    return {
        "actions": [
            f'mkdir -p "{DATA_DIR}"' if OS_TYPE == "nix" else f'if not exist "{DATA_DIR}" mkdir "{DATA_DIR}"',
            f'mkdir -p "{OUTPUT_DIR}"' if OS_TYPE == "nix" else f'if not exist "{OUTPUT_DIR}" mkdir "{OUTPUT_DIR}"',
            f'mkdir -p "{OUTPUT_DIR}/_notebook_build"' if OS_TYPE == "nix" else f'if not exist "{OUTPUT_DIR}/_notebook_build" mkdir "{OUTPUT_DIR}/_notebook_build"',
        ],
        "verbosity": 2,
    }


def task_pull_open_source_bond():
    """Pull Open Source Bond data (public)."""
    targets = [
        DATA_DIR / "treasury_bond_returns.parquet",
        DATA_DIR / "treasury_bond_returns_README.pdf",
        DATA_DIR / "corporate_bond_returns.parquet",
        DATA_DIR / "corporate_bond_returns_README.txt",
    ]
    return {
        "actions": ["python src/pull_open_source_bond.py"],
        "verbosity": 2,
        "task_dep": ["config"],
        "targets": targets,
        "uptodate": [all(t.exists() for t in targets)],
    }


def task_pull_markit_mapping():
    """Pull RED-ISIN mapping from WRDS."""
    targets = [
        DATA_DIR / "RED_and_ISIN_mapping.parquet",
    ]
    return {
        "actions": ["python src/pull_markit_mapping.py"],
        "verbosity": 2,
        "task_dep": ["config"],
        "targets": targets,
        "uptodate": [all(t.exists() for t in targets)],
    }


def task_pull_wrds_markit():
    """Pull Markit CDS data from WRDS."""
    targets = [
        DATA_DIR / "markit_cds.parquet",
        DATA_DIR / "markit_red_crsp_link.parquet",
        DATA_DIR / "markit_cds_subsetted_to_crsp.parquet",
    ]
    return {
        "actions": ["python src/pull_wrds_markit.py"],
        "verbosity": 2,
        "task_dep": ["config"],
        "targets": targets,
        "uptodate": [all(t.exists() for t in targets)],
    }


def task_calc():
    """Calculate CDS-bond basis and create FTSFR datasets."""
    return {
        "actions": ["python src/create_ftsfr_datasets.py"],
        "verbosity": 2,
        "task_dep": ["pull_open_source_bond", "pull_markit_mapping", "pull_wrds_markit"],
        "file_dep": [
            DATA_DIR / "corporate_bond_returns.parquet",
            DATA_DIR / "RED_and_ISIN_mapping.parquet",
            DATA_DIR / "markit_cds.parquet",
            BASE_DIR / "src" / "create_ftsfr_datasets.py",
            BASE_DIR / "src" / "merge_cds_bond.py",
            BASE_DIR / "src" / "process_final_product.py",
        ],
        "targets": [
            DATA_DIR / "ftsfr_cds_bond_basis_aggregated.parquet",
            DATA_DIR / "ftsfr_cds_bond_basis_non_aggregated.parquet",
        ],
    }


def task_run_notebooks():
    """Execute summary notebooks."""
    notebooks = [
        "src/summary_cds_bond_basis_ipynb.py",
    ]

    actions = []
    for nb_py in notebooks:
        nb_name = Path(nb_py).stem
        nb_ipynb = OUTPUT_DIR / "_notebook_build" / f"{nb_name}.ipynb"

        # Convert py to ipynb
        actions.append(f'ipynb-py-convert "{nb_py}" "{nb_ipynb}"')
        # Execute notebook
        actions.append(jupyter_execute_notebook(nb_ipynb))
        # Convert to HTML
        actions.append(jupyter_to_html(nb_ipynb, OUTPUT_DIR / "_notebook_build"))

    return {
        "actions": actions,
        "verbosity": 2,
        "task_dep": ["calc"],
        "file_dep": [
            DATA_DIR / "ftsfr_cds_bond_basis_aggregated.parquet",
            DATA_DIR / "ftsfr_cds_bond_basis_non_aggregated.parquet",
            BASE_DIR / "src" / "summary_cds_bond_basis_ipynb.py",
        ],
        "targets": [
            OUTPUT_DIR / "_notebook_build" / "summary_cds_bond_basis_ipynb.ipynb",
            OUTPUT_DIR / "_notebook_build" / "summary_cds_bond_basis_ipynb.html",
        ],
    }


def task_generate_pipeline_site():
    """Generate pipeline documentation site."""
    return {
        "actions": ["chartbook build -f"],
        "verbosity": 2,
        "task_dep": ["run_notebooks"],
        "file_dep": [
            OUTPUT_DIR / "_notebook_build" / "summary_cds_bond_basis_ipynb.html",
            BASE_DIR / "chartbook.toml",
        ],
        "targets": [
            BASE_DIR / "docs" / "index.html",
        ],
    }
