"""Generate interactive HTML chart for CDS-Bond Basis."""

import pandas as pd
import plotly.express as px
import os
from pathlib import Path

# Get the project root (one level up from src/)
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "_data"
OUTPUT_DIR = PROJECT_ROOT / "_output"


def generate_cds_bond_basis_chart():
    """Generate CDS-Bond basis time series chart."""
    # Load aggregated CDS-Bond basis data
    df = pd.read_parquet(DATA_DIR / "ftsfr_cds_bond_basis_aggregated.parquet")

    # Convert to wide format for plotting
    df_pivot = df.pivot(index="ds", columns="unique_id", values="y").reset_index()

    # Create line chart
    fig = px.line(
        df.sort_values("ds"),
        x="ds",
        y="y",
        color="unique_id",
        title="CDS-Bond Basis by Rating Category",
        labels={
            "ds": "Date",
            "y": "Implied Risk-Free Rate (%)",
            "unique_id": "Rating Category"
        }
    )

    # Update layout
    fig.update_layout(
        template="plotly_white",
        hovermode="x unified"
    )

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Save chart
    output_path = OUTPUT_DIR / "cds_bond_basis_replication.html"
    fig.write_html(str(output_path))
    print(f"Chart saved to {output_path}")

    return fig


if __name__ == "__main__":
    generate_cds_bond_basis_chart()
