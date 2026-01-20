# %%
"""
# CDS-Bond Basis Summary

This notebook summarizes the CDS-Bond Basis dataset, which measures the implied
arbitrage return from the CDS and corporate bond markets as specified in
Siriwardane, Sunderam, and Wallen's "Segmented Arbitrage" paper.

## Methodology

The CDS basis (CB) is defined as:

$$
CB_{i, t, \\tau} = CDS_{i, t, \\tau} - FR_{i, t, \\tau}
$$

Where:
- $FR_{i, t, \\tau}$ = floating rate spread implied by a corporate bond (approximated by Z-spread/credit spread)
- $CDS_{i, t, \\tau}$ = CDS par spread (interpolated using cubic spline)

The implied risk-free rate is:

$$
rfr^{CDS}_{i, t, \\tau} = y_{t, \\tau} - CB_{i , t, \\tau}
$$

Where $y_{t, \\tau}$ is the duration-matched treasury yield.
"""

# %%
import sys
from pathlib import Path

sys.path.insert(1, "./src/")

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import chartbook

BASE_DIR = chartbook.env.get_project_root()
DATA_DIR = BASE_DIR / "_data"

# %%
"""
## Load Data
"""

# %%
# Load FTSFR datasets
agg_df = pd.read_parquet(DATA_DIR / "ftsfr_cds_bond_basis_aggregated.parquet")
non_agg_df = pd.read_parquet(DATA_DIR / "ftsfr_cds_bond_basis_non_aggregated.parquet")

print("=== Aggregated Dataset ===")
print(f"Shape: {agg_df.shape}")
print(f"Date range: {agg_df['ds'].min()} to {agg_df['ds'].max()}")
print(f"Unique IDs: {agg_df['unique_id'].unique().tolist()}")

print("\n=== Non-Aggregated Dataset ===")
print(f"Shape: {non_agg_df.shape}")
print(f"Date range: {non_agg_df['ds'].min()} to {non_agg_df['ds'].max()}")
print(f"Unique CUSIPs: {non_agg_df['unique_id'].nunique()}")

# %%
"""
## Summary Statistics - Aggregated Data
"""

# %%
# Pivot to wide format for statistics
agg_wide = agg_df.pivot(index="ds", columns="unique_id", values="y")
print("Aggregated CDS-Bond Basis (Implied Risk-Free Rate, percent)")
print(agg_wide.describe().T)

# %%
"""
## Summary Statistics - Non-Aggregated Data (Bond-Level)
"""

# %%
print("Non-Aggregated CDS-Bond Basis Statistics")
print(non_agg_df["y"].describe())

# %%
"""
## Time Series Plot - Aggregated by Rating
"""

# %%
fig, ax = plt.subplots(figsize=(12, 6))

for uid in agg_df["unique_id"].unique():
    subset = agg_df[agg_df["unique_id"] == uid].sort_values("ds")
    ax.plot(subset["ds"], subset["y"], label=uid, linewidth=0.8)

ax.axhline(0, color="black", linewidth=0.8, linestyle="--")
ax.set_xlabel("Date")
ax.set_ylabel("Implied Risk-Free Rate (percent)")
ax.set_title("CDS-Bond Basis by Rating Category")
ax.legend(loc="best")
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()

# %%
"""
## Distribution of Implied Risk-Free Rates
"""

# %%
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Aggregated data
for uid in agg_df["unique_id"].unique():
    subset = agg_df[agg_df["unique_id"] == uid]
    axes[0].hist(subset["y"], bins=50, alpha=0.5, label=uid)
axes[0].set_xlabel("Implied Risk-Free Rate (percent)")
axes[0].set_ylabel("Frequency")
axes[0].set_title("Aggregated by Rating")
axes[0].legend()

# Non-aggregated data
axes[1].hist(non_agg_df["y"], bins=100, alpha=0.7, color="steelblue")
axes[1].set_xlabel("Implied Risk-Free Rate (percent)")
axes[1].set_ylabel("Frequency")
axes[1].set_title("Bond-Level Distribution")

plt.tight_layout()
plt.show()

# %%
"""
## Correlation Between Rating Categories
"""

# %%
if len(agg_wide.columns) > 1:
    corr_matrix = agg_wide.corr()
    print("Correlation Matrix:")
    print(corr_matrix)

    fig, ax = plt.subplots(figsize=(6, 5))
    sns.heatmap(corr_matrix, annot=True, cmap="coolwarm", center=0, ax=ax)
    ax.set_title("Correlation: Implied Risk-Free Rates by Rating")
    plt.tight_layout()
    plt.show()

# %%
"""
## Monthly Statistics Over Time
"""

# %%
# Create monthly summary
agg_df["ds"] = pd.to_datetime(agg_df["ds"])
agg_df["month"] = agg_df["ds"].dt.to_period("M")

monthly_stats = agg_df.groupby(["month", "unique_id"])["y"].agg(["mean", "std", "count"]).reset_index()
print("Monthly statistics by rating:")
print(monthly_stats.tail(20))

# %%
"""
## Data Quality Check
"""

# %%
print("=== Aggregated Dataset ===")
print(f"Missing values: {agg_df['y'].isna().sum()}")
print(f"Infinite values: {(~agg_df['y'].apply(lambda x: -1e10 < x < 1e10)).sum()}")

print("\n=== Non-Aggregated Dataset ===")
print(f"Missing values: {non_agg_df['y'].isna().sum()}")
print(f"Infinite values: {(~non_agg_df['y'].apply(lambda x: -1e10 < x < 1e10)).sum()}")
