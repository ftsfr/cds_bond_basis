"""
Doit build file for CDS-Bond Basis pipeline.

Run with: doit
"""

import os
import platform
import sys
from pathlib import Path

import chartbook

sys.path.insert(1, "./src/")

BASE_DIR = chartbook.env.get_project_root()
DATA_DIR = BASE_DIR / "_data"
OUTPUT_DIR = BASE_DIR / "_output"
OS_TYPE = "nix" if platform.system() != "Windows" else "windows"



## Helpers for handling Jupyter Notebook tasks
os.environ["PYDEVD_DISABLE_FILE_VALIDATION"] = "1"


# fmt: off
def jupyter_execute_notebook(notebook_path):
    return f"jupyter nbconvert --execute --to notebook --ClearMetadataPreprocessor.enabled=True --inplace {notebook_path}"
def jupyter_to_html(notebook_path, output_dir=OUTPUT_DIR):
    return f"jupyter nbconvert --to html --output-dir={output_dir} {notebook_path}"
# fmt: on


def mv(from_path, to_path):
    from_path = Path(from_path)
    to_path = Path(to_path)
    to_path.mkdir(parents=True, exist_ok=True)
    if OS_TYPE == "nix":
        command = f"mv {from_path} {to_path}"
    else:
        command = f"move {from_path} {to_path}"
    return command


def task_config():
    """Create necessary directories."""
    def create_dirs():
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return {
        "actions": [create_dirs],
        "targets": [DATA_DIR, OUTPUT_DIR],
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


notebook_tasks = {
    "summary_cds_bond_basis_ipynb": {
        "path": "./src/summary_cds_bond_basis_ipynb.py",
        "file_dep": [
            DATA_DIR / "ftsfr_cds_bond_basis_aggregated.parquet",
            DATA_DIR / "ftsfr_cds_bond_basis_non_aggregated.parquet",
        ],
        "targets": [],
    },
}
notebook_files = []
for notebook in notebook_tasks.keys():
    pyfile_path = Path(notebook_tasks[notebook]["path"])
    notebook_files.append(pyfile_path)


def task_run_notebooks():
    """Execute summary notebooks."""
    for notebook in notebook_tasks.keys():
        pyfile_path = Path(notebook_tasks[notebook]["path"])
        notebook_path = pyfile_path.with_suffix(".ipynb")
        yield {
            "name": notebook,
            "actions": [
                f"jupytext --to notebook --output {notebook_path} {pyfile_path}",
                jupyter_execute_notebook(notebook_path),
                jupyter_to_html(notebook_path),
                mv(notebook_path, OUTPUT_DIR),
            ],
            "file_dep": [
                pyfile_path,
                *notebook_tasks[notebook]["file_dep"],
            ],
            "targets": [
                OUTPUT_DIR / f"{notebook}.html",
                *notebook_tasks[notebook]["targets"],
            ],
            "clean": True,
            "task_dep": ["calc"],
        }


def task_generate_charts():
    """Generate interactive HTML charts."""
    return {
        "actions": ["python src/generate_chart.py"],
        "file_dep": [
            "src/generate_chart.py",
            DATA_DIR / "ftsfr_cds_bond_basis_aggregated.parquet",
        ],
        "targets": [
            OUTPUT_DIR / "cds_bond_basis_replication.html",
        ],
        "verbosity": 2,
        "task_dep": ["calc"],
    }


def task_generate_pipeline_site():
    """Generate pipeline documentation site."""
    return {
        "actions": ["chartbook build -f"],
        "verbosity": 2,
        "task_dep": ["run_notebooks", "generate_charts"],
        "file_dep": [
            BASE_DIR / "chartbook.toml",
            *notebook_files,
            OUTPUT_DIR / "cds_bond_basis_replication.html",
        ],
        "targets": [
            BASE_DIR / "docs" / "index.html",
        ],
    }
