"""
This script pulls the Markit CDS data from WRDS.
Code by Kausthub Kesheva, Alex Wang, and Vincent Xu
"""

import sys
from pathlib import Path

sys.path.insert(1, "./src/")

import pandas as pd
import wrds
from thefuzz import fuzz
import chartbook

BASE_DIR = chartbook.env.get_project_root()
DATA_DIR = BASE_DIR / "_data"
WRDS_USERNAME = chartbook.env.get("WRDS_USERNAME")
START_DATE = pd.Timestamp("1925-01-01")
END_DATE = pd.Timestamp("2024-01-01")


def get_cds_data_as_dict(wrds_username=WRDS_USERNAME):
    """
    Connects to a WRDS (Wharton Research Data Services) database and fetches Credit Default Swap (CDS) data
    for each year from 2001 to 2023 from tables named `markit.CDS{year}`. The data fetched includes the date,
    ticker, and parspread where the tenor is '5Y' and the country is 'United States'. The fetched data for each
    year is stored in a dictionary with the year as the key. The function finally returns this dictionary.

    Returns:
        dict: A dictionary where each key is a year from 2001 to 2023 and each value is a DataFrame containing
        the date, ticker, and parspread for that year.
    """
    db = wrds.Connection(wrds_username=wrds_username)
    cds_data = {}
    for year in range(2001, 2024):  # Loop from 2001 to 2023
        table_name = f"markit.CDS{year}"  # Generate table name dynamically
        query = f"""
        SELECT DISTINCT
            date, -- The date on which points on a curve were calculated
            ticker, -- The Markit ticker for the organization.
            RedCode, -- The RED Code for identification of the entity.
            parspread, -- The par spread associated to the contributed CDS curve.
            tenor,
            country
        FROM
            {table_name}
        WHERE
            country = 'United States' AND
            currency = 'USD' AND
            tier = 'SNRFOR' AND -- Senior Unsecured Debt
            tenor IN ('1Y', '3Y', '5Y', '7Y', '10Y')
        """
        cds_data[year] = db.raw_sql(query, date_cols=["date"])
    return cds_data


def combine_cds_data(cds_data: dict) -> pd.DataFrame:
    """
    Combines the CDS data stored in a dictionary into a single DataFrame.

    For each key-value pair in `cds_data`, a new column "year" is added to the
    DataFrame containing the value of the key (i.e., the year). Then, all
    DataFrames are concatenated.

    Args:
        cds_data (dict): A dictionary where each key is a year and its value is
        a DataFrame with CDS data for that year.

    Returns:
        pd.DataFrame: A single concatenated DataFrame with an additional "year"
        column.
    """
    dataframes = []
    for year, df in cds_data.items():
        # Create a copy to avoid modifying the original DataFrame
        df_with_year = df.copy()
        df_with_year["year"] = year
        dataframes.append(df_with_year)

    combined_df = pd.concat(dataframes, ignore_index=True)
    return combined_df


def pull_cds_data(wrds_username=WRDS_USERNAME):
    cds_data = get_cds_data_as_dict(wrds_username=wrds_username)
    combined_df = combine_cds_data(cds_data)
    return combined_df


def get_value_counts(variable, wrds_username=WRDS_USERNAME):
    """
    Retrieves all unique values across all Markit CDS tables
    and counts their total frequency of occurrence.
    """
    db = wrds.Connection(wrds_username=wrds_username)
    yearly_counts = []

    for year in range(2001, 2024):
        query = f"""
        SELECT
            {variable},
            COUNT(*) as count
        FROM
            markit.CDS{year}
        GROUP BY
            {variable}
        """
        result = db.raw_sql(query)
        yearly_counts.append(result)

    # Concatenate all the yearly counts
    all_counts = pd.concat(yearly_counts)

    # Sum the counts for each docclause across all years
    total_counts = all_counts.groupby(variable)["count"].sum().reset_index()

    return total_counts.sort_values("count", ascending=False)


def pull_markit_red_crsp_link(wrds_username=WRDS_USERNAME):
    """
    Link Markit RED data with CRSP data.

    This returns a table that can be used to link Markit CDS data with CRSP data.
    You'll link the Markit RED Code with the CRSP Permno. It contains a column called flg
    that indicates the type of link. It can be either 'cusip' or 'ticker'.
    When these are matched by ticket, you should double check that the
    company names are roughly the same. You can do this by looking at the nameRatio column,
    which is a fuzzy match between the two company names. A nameRatio of 100 is a perfect match.
    I recommend that you at least require a nameRatio of 50.
    """
    conn = wrds.Connection(wrds_username=wrds_username)

    ### Get red entity information
    redent = conn.get_table(library="markit", table="redent")

    # Quick check to confirm that it is the header information
    redcnt = (
        redent.groupby(["redcode"])["entity_cusip"]
        .count()
        .reset_index()
        .rename(columns={"entity_cusip": "cusipCnt"})
    )
    assert redcnt.cusipCnt.max() == 1, (
        "Each redcode should be mapped to only one entity"
    )

    ### Get information from CRSP header table
    crspHdr = conn.raw_sql(
        """SELECT
            permno, permco, hdrcusip, ticker, issuernm
        FROM
            crsp.stksecurityinfohdr
        """
    )
    crspHdr["cusip6"] = crspHdr.hdrcusip.str[:6]
    crspHdr = crspHdr.rename(columns={"ticker": "crspTicker"})

    ### First Route - Link with 6-digit cusip
    _cdscrsp1 = pd.merge(
        redent, crspHdr, how="left", left_on="entity_cusip", right_on="cusip6"
    )

    # store linked results through CUSIP
    _cdscrsp_cusip = _cdscrsp1.loc[_cdscrsp1.permno.notna()].copy()
    _cdscrsp_cusip["flg"] = "cusip"

    # continue to work with non-linked records
    _cdscrsp2 = (
        _cdscrsp1.loc[_cdscrsp1.permno.isna()]
        .copy()
        .drop(
            columns=["permno", "permco", "hdrcusip", "crspTicker", "issuernm", "cusip6"]
        )
    )

    ### Second Route - Link with Ticker
    _cdscrsp3 = pd.merge(
        _cdscrsp2, crspHdr, how="left", left_on="ticker", right_on="crspTicker"
    )
    _cdscrsp_ticker = _cdscrsp3.loc[_cdscrsp3.permno.notna()].copy()
    _cdscrsp_ticker["flg"] = "ticker"

    ### Consolidate Output and Company Name Distance Check
    cdscrsp = pd.concat([_cdscrsp_cusip, _cdscrsp_ticker], ignore_index=True, axis=0)

    # Check similarity ratio of company names
    crspNameLst = cdscrsp.issuernm.str.upper().tolist()
    redNameLst = cdscrsp.shortname.str.upper().tolist()

    nameRatio = []  # blank list to store fuzzy ratio

    for i in range(len(redNameLst)):
        ratio = fuzz.partial_ratio(redNameLst[i], crspNameLst[i])
        nameRatio.append(ratio)

    cdscrsp["nameRatio"] = nameRatio
    return cdscrsp


def right_merge_cds_crsp(
    cds_data: pd.DataFrame, cds_crsp_link: pd.DataFrame, ratio_threshold: int = 50
):
    """
    Right merge the CDS data with the CRSP data.
    """
    columns_to_keep = ["redcode", "permno", "permco", "flg", "nameRatio"]
    merged_df = pd.merge(
        cds_data, cds_crsp_link[columns_to_keep], how="right", on="redcode"
    )
    merged_df = merged_df[merged_df["nameRatio"] >= ratio_threshold]
    return merged_df


def load_cds_data(data_dir=DATA_DIR):
    path = data_dir / "markit_cds.parquet"
    return pd.read_parquet(path)


def load_cds_crsp_link(data_dir=DATA_DIR):
    path = data_dir / "markit_red_crsp_link.parquet"
    return pd.read_parquet(path)


def load_cds_subsetted_to_crsp(data_dir=DATA_DIR):
    path = data_dir / "markit_cds_subsetted_to_crsp.parquet"
    return pd.read_parquet(path)


if __name__ == "__main__":
    cds_data = pull_cds_data(wrds_username=WRDS_USERNAME)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    cds_data.to_parquet(DATA_DIR / "markit_cds.parquet")

    cds_crsp_link = pull_markit_red_crsp_link(wrds_username=WRDS_USERNAME)
    cds_crsp_link.to_parquet(DATA_DIR / "markit_red_crsp_link.parquet")

    cds_crsp_merged = right_merge_cds_crsp(cds_data, cds_crsp_link, ratio_threshold=50)
    cds_crsp_merged.to_parquet(DATA_DIR / "markit_cds_subsetted_to_crsp.parquet")
