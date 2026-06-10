# CDS-Bond Basis

The CDS-bond basis measured from the single-name CDS and corporate bond markets.

## Overview

Based on Siriwardane, Sunderam, and Wallen's "Segmented Arbitrage" paper, this
pipeline computes the **CDS-bond basis** for corporate issuers: the CDS par
spread minus the bond's Z-spread, expressed in basis points.

The basis is defined as:

```
basis (bps) = CDS par spread - bond Z-spread
```

The bond Z-spread is the constant spread that, added to the risk-free discount
curve, reprices the bond. The risk-free curve is a Nelson-Siegel-Svensson
(Gurkaynak-Sack-Wright 2006) curve fit each quote date from the CRSP Treasury
panel (with the Fed's published GSW parameters used as a sanity fallback).

A negative basis implies an investor could earn a positive arbitrage profit by
going long the bond and purchasing CDS protection.

## Interpretation

- **Negative basis**: the bond trades cheap relative to CDS — a classic
  negative-basis arbitrage opportunity (the empirical norm, especially
  post-2008).
- **Investment Grade vs High Yield**: compares the basis across rating
  categories.

## Data Sources

- **WRDS Markit**: CDS par spreads and RED-CUSIP/ISIN mapping.
- **WRDS Bond Returns** (`wrdsapps_bondret`): corporate bond prices, yields,
  and characteristics used to solve each bond's Z-spread.
- **CRSP Treasury** and the **Fed yield curve**: inputs to the NSS risk-free
  curve (see "Cross-repo inputs" below).

## Cross-repo inputs

The Z-spread step reads two parquet files produced by sibling federated repos,
and expects them under `_data/`:

- `_data/us_treasury_returns/CRSP_TFZ_with_runness.parquet`
- `_data/fed_yield_curve/fed_yield_curve_all.parquet`

Stage them (copy or symlink) from the corresponding sibling repos' `_data/`
before running `doit`.

## CDS tenors

CDS tenors used for cubic-spline interpolation onto each bond's maturity:
1-year, 3-year, 5-year, 7-year, 10-year.

## Outputs

- `ftsfr_cds_bond_basis_aggregated.parquet`: monthly CDS-bond basis (bps)
  aggregated by rating category (Investment Grade, High Yield).
- `ftsfr_cds_bond_basis_non_aggregated.parquet`: bond-level CDS-bond basis (bps).

## Requirements

- WRDS account (for Markit CDS and `wrdsapps_bondret`)
- The `finm` package (NSS curve fit / Z-spread; see `requirements.txt`)
- Python 3.10+

## Setup

1. Configure WRDS credentials in `~/.pgpass`
2. Install dependencies: `pip install -r requirements.txt`
3. Stage the cross-repo inputs (see above)
4. Run pipeline: `doit`

## Academic References

This module replicates methodology from:

### Primary Papers

- **Siriwardane, Sunderam, and Wallen** - "Segmented Arbitrage"
  - Identifies financial constraints explaining persistence of arbitrage opportunities

- **Nozawa (2017)** - "What Drives the Cross-Section of Credit Spreads?"
  - Analyzes cross-sectional drivers of CDS-bond basis

### Key Findings Replicated

- The CDS-bond basis can exceed 200 basis points during financial stress
- Arbitrage spreads are correlated across fixed-income markets
- Balance sheet costs explain persistence of arbitrage opportunities
