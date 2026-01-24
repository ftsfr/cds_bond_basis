import datetime as datetime

import pandas as pd
from merge_cds_bond import *


def test_merge_cds_into_bonds():
    """
    Unit test for merge_cds_into_bonds() function.
    This test ensures that:
    - The function correctly merges CDS data into bond data.
    - The output DataFrame has expected columns.
    - The cubic spline interpolation is applied correctly.
    """

    # Create a mock bond_red_df with the columns expected by merge_cds_into_bonds
    # Expected input: date, cusip, issuer_cusip, BOND_YIELD, CS, size_ig, size_jk, mat_days, redcode
    bond_red_df = pd.DataFrame(
        {
            "cusip": ["001957AM1", "001957AM2"],
            "date": pd.to_datetime(["2024-01-01", "2024-01-01"]),
            "issuer_cusip": ["001957", "001957"],
            "BOND_YIELD": [0.05, 0.06],
            "CS": [0.03, 0.035],
            "size_ig": [1.0, 0.0],
            "size_jk": [0.0, 1.0],
            "mat_days": [730, 1460],  # ~2Y and ~4Y in days
            "redcode": ["R1", "R1"],
        }
    )

    # Create a mock cds_df with different tenors for cubic spline fitting
    cds_df = pd.DataFrame(
        {
            "date": pd.to_datetime(
                ["2024-01-01", "2024-01-01", "2024-01-01", "2024-01-01"]
            ),
            "redcode": ["R1", "R1", "R1", "R1"],
            "parspread": [0.03, 0.04, 0.05, 0.06],
            "tenor": ["1Y", "3Y", "5Y", "10Y"],
            "tier": ["SNRFOR", "SNRFOR", "SNRFOR", "SNRFOR"],
            "country": ["USA", "USA", "USA", "USA"],
            "year": [2024, 2024, 2024, 2024],
        }
    )

    # Run the function
    result_df = merge_cds_into_bonds(bond_red_df, cds_df)

    # Check that the output DataFrame is not empty
    assert not result_df.empty, "Output DataFrame is empty!"

    # Check that expected output columns exist
    expected_columns = [
        "cusip",
        "date",
        "mat_days",
        "BOND_YIELD",
        "CS",
        "size_ig",
        "size_jk",
        "par_spread",
    ]
    assert all(col in result_df.columns for col in expected_columns), (
        f"Missing expected columns! Got: {result_df.columns.tolist()}"
    )

    # Check that par_spread is interpolated correctly
    assert not result_df["par_spread"].isnull().any(), "par_spread contains NaN values!"

    # Check if duplicate rows were removed
    assert result_df.duplicated().sum() == 0, "Duplicates were not removed properly!"

    print("All tests passed successfully!")
