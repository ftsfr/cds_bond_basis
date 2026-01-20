"""
This module creates FTSFR-standardized datasets from CDS-bond basis data.

Outputs:
- ftsfr_cds_bond_basis_aggregated.parquet: Aggregated by rating (unique_id, ds, y)
- ftsfr_cds_bond_basis_non_aggregated.parquet: Individual bonds (unique_id, ds, y)
"""

import sys
from pathlib import Path

sys.path.insert(1, "./src/")

import pandas as pd
import merge_cds_bond
import process_final_product
import chartbook

BASE_DIR = chartbook.env.get_project_root()
DATA_DIR = BASE_DIR / "_data"


def main():
    """Create FTSFR datasets from CDS-bond basis data."""
    print("Loading data...")
    RED_CODE_FILE_NAME = "RED_and_ISIN_mapping.parquet"
    CORPORATES_MONTHLY_FILE_NAME = "corporate_bond_returns.parquet"
    CDS_FILE_NAME = "markit_cds.parquet"

    corp_bonds_data = pd.read_parquet(DATA_DIR / CORPORATES_MONTHLY_FILE_NAME)
    red_data = pd.read_parquet(DATA_DIR / RED_CODE_FILE_NAME)
    cds_data = pd.read_parquet(DATA_DIR / CDS_FILE_NAME)

    print("Merging RED codes into bond data...")
    corp_red_data = merge_cds_bond.merge_red_code_into_bond_treas(corp_bonds_data, red_data)

    print("Merging CDS data into bonds...")
    final_data = merge_cds_bond.merge_cds_into_bonds(corp_red_data, cds_data)

    print("Processing CDS-bond spread...")
    df_all = process_final_product.process_cb_spread(final_data)

    print("Creating final products...")
    agg_df, non_agg_df = process_final_product.output_cb_final_products(df_all)

    # Create aggregated FTSFR dataset
    print("Creating aggregated FTSFR dataset...")
    agg_df_indexed = agg_df.set_index(["c_rating", "date"])
    df_stacked = agg_df_indexed.stack().reset_index()
    df_stacked.columns = ["c_rating", "date", "variable", "value"]
    df_stacked["unique_id"] = df_stacked["c_rating"].astype(str)
    df_stacked = df_stacked[["unique_id", "date", "value"]].rename(
        columns={"date": "ds", "value": "y"}
    )
    df_stacked.reset_index(drop=True, inplace=True)
    df_stacked = df_stacked.dropna()
    df_stacked.to_parquet(DATA_DIR / "ftsfr_cds_bond_basis_aggregated.parquet")
    print(f"Aggregated dataset: {len(df_stacked)} records, {df_stacked['unique_id'].nunique()} unique IDs")

    # Create non-aggregated FTSFR dataset
    print("Creating non-aggregated FTSFR dataset...")
    non_agg_df_indexed = non_agg_df.set_index(["cusip", "date"])
    df_stacked2 = non_agg_df_indexed.stack().reset_index()
    df_stacked2.columns = ["cusip", "date", "variable", "value"]
    df_stacked2["unique_id"] = df_stacked2["cusip"]
    df_stacked2 = df_stacked2[["unique_id", "date", "value"]].rename(
        columns={"date": "ds", "value": "y"}
    )

    # Check for duplicates
    duplicates = df_stacked2.duplicated(subset=["unique_id", "ds"])
    num_duplicates = duplicates.sum()
    if num_duplicates > 0:
        print(f"Warning: Found {num_duplicates} duplicate (unique_id, ds) pairs. Removing duplicates...")
        df_stacked2.drop_duplicates(subset=["unique_id", "ds"], inplace=True)

    df_stacked2.reset_index(drop=True, inplace=True)
    df_stacked2 = df_stacked2.dropna()
    df_stacked2.to_parquet(DATA_DIR / "ftsfr_cds_bond_basis_non_aggregated.parquet")
    print(f"Non-aggregated dataset: {len(df_stacked2)} records, {df_stacked2['unique_id'].nunique()} unique IDs")

    print("\nDone!")


if __name__ == "__main__":
    main()
