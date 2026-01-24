import datetime as datetime

import pandas as pd
from merge_cds_bond import *
from process_final_product import *


def test_process_cb_spread():
    """
    Unit test for process_cb_spread() function.
    This test ensures that:
    - The function correctly calculates the FR, CB, and rfr columns.
    - The output DataFrame contains the expected additional columns.
    - The calculations follow the expected formulas.
    """

    # Create a mock dataframe with the columns expected by process_cb_spread
    # Expected: cusip, date, mat_days, BOND_YIELD, CS, size_ig, size_jk, par_spread
    test_df = pd.DataFrame(
        {
            "cusip": ["001957AM1", "001957AM2"],
            "date": pd.to_datetime(["2024-01-01", "2024-01-01"]),
            "mat_days": [730, 1460],
            "BOND_YIELD": [0.05, 0.06],
            "CS": [0.03, 0.035],  # Z-spread
            "size_ig": [1.0, 0.0],
            "size_jk": [0.0, 1.0],
            "par_spread": [0.04, 0.05],
        }
    )

    # Apply the function
    result_df = process_cb_spread(test_df)

    # Check that the new columns exist
    assert "FR" in result_df.columns, "FR column is missing!"
    assert "CB" in result_df.columns, "CB column is missing!"
    assert "rfr" in result_df.columns, "rfr column is missing!"
    assert "c_rating" in result_df.columns, "c_rating column is missing!"

    # Validate calculations based on the function's logic:
    # FR = CS
    # CB = par_spread - FR
    # rfr = (BOND_YIELD - CS - CB) * 100
    for _, row in result_df.iterrows():
        expected_FR = row["CS"]
        expected_CB = row["par_spread"] - expected_FR
        expected_rfr = (row["BOND_YIELD"] - row["CS"] - expected_CB) * 100

        assert row["FR"] == expected_FR, f"FR mismatch: {row['FR']} != {expected_FR}"
        assert row["CB"] == expected_CB, f"CB mismatch: {row['CB']} != {expected_CB}"
        assert abs(row["rfr"] - expected_rfr) < 0.001, f"rfr mismatch: {row['rfr']} != {expected_rfr}"

    print("All tests passed successfully!")
