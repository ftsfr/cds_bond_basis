# CDS-Bond Basis

CDS-Bond basis measuring implied arbitrage returns from the CDS and corporate bond markets.

## Overview

Based on Siriwardane, Sunderam, and Wallen's "Segmented Arbitrage" paper, this pipeline calculates the implied risk-free rate from CDS-bond arbitrage trades.

The CDS basis (CB) is defined as:

```
CB = CDS par spread - Floating Rate spread (Z-spread)
```

The implied risk-free rate is:

```
rfr = Treasury yield - CB
```

A negative basis implies an investor could earn a positive arbitrage profit by going long the bond and purchasing CDS protection.

## Interpretation

- **Positive implied rfr**: Arbitrage opportunity exists
- **Investment Grade vs High Yield**: Compares arbitrage opportunities across rating categories

## Data Sources

- **WRDS Markit**: CDS par spreads and RED-CUSIP mapping
- **Open Source Bond Asset Pricing**: Corporate bond yields and credit spreads

## Tenors

CDS tenors used for cubic spline interpolation:
- 1-year
- 3-year
- 5-year
- 7-year
- 10-year

## Outputs

- `ftsfr_cds_bond_basis_aggregated.parquet`: Aggregated by rating category (Investment Grade, High Yield)
- `ftsfr_cds_bond_basis_non_aggregated.parquet`: Bond-level implied risk-free rates

## Requirements

- WRDS account (for Markit CDS data)
- Python 3.10+

## Setup

1. Configure WRDS credentials in `~/.pgpass`
2. Install dependencies: `pip install -r requirements.txt`
3. Run pipeline: `doit`

## Academic References

This module replicates methodology from:

### Primary Papers

- **Siriwardane, Sunderam, and Wallen** - "Segmented Arbitrage"
  - Identifies financial constraints explaining persistence of arbitrage opportunities

- **Nozawa (2017)** - "What Drives the Cross-Section of Credit Spreads?"
  - Analyzes cross-sectional drivers of CDS-bond basis

### Key Findings Replicated

- CDS-bond basis can exceed 200 basis points during financial stress
- Arbitrage spreads are correlated across fixed-income markets
- Balance sheet costs explain persistence of arbitrage opportunities
