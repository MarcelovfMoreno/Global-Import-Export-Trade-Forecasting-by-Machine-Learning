import sqlite3
import pandas as pd
import numpy as np

database_filename = "trade_forecast.db"

print("Step 1: Connecting to SQLite database...")
connection = sqlite3.connect(database_filename)

query = """
WITH combined_trade AS (
    SELECT geo_code, geo_name, flow_code, flow_description, time_period, value_meur, year, quarter FROM clean_trade_model_ready
    UNION ALL
    SELECT geo_code, geo_name, flow_code, flow_description, time_period, value_meur, year, quarter FROM trade_forecast_predictions
),
pivoted_trade AS (
    SELECT 
        geo_code,
        geo_name,
        year,
        quarter,
        time_period,
        SUM(CASE WHEN flow_code LIKE '%EXP%' OR flow_code LIKE '%E%' OR flow_code = 'P6' THEN value_meur ELSE 0 END) AS export_meur,
        SUM(CASE WHEN flow_code LIKE '%IMP%' OR flow_code LIKE '%I%' OR flow_code = 'P7' OR flow_code NOT IN ('EXP', 'P6') THEN value_meur ELSE 0 END) AS import_meur
    FROM combined_trade
    WHERE year BETWEEN 2022 AND 2027
    GROUP BY geo_code, geo_name, year, quarter, time_period
)
SELECT * FROM pivoted_trade ORDER BY geo_name, year, quarter;
"""

print("Step 2: Loading data and building full continuous timeline grid...")
df_raw = pd.read_sql_query(query, connection)

# Create a complete grid of all country and period combinations (2022-Q1 to 2027-Q4)
countries = df_raw[['geo_code', 'geo_name']].drop_duplicates()
years = [2022, 2023, 2024, 2025, 2026, 2027]
quarters = ['Q1', 'Q2', 'Q3', 'Q4']

full_grid = []
for _, country in countries.iterrows():
    for y in years:
        for q in quarters:
            full_grid.append({
                'geo_code': country['geo_code'],
                'geo_name': country['geo_name'],
                'year': y,
                'quarter': q,
                'time_period': f"{y}-{q}"
            })

df_grid = pd.DataFrame(full_grid)

# Merge actual data with the complete grid
df_tableau = pd.merge(df_grid, df_raw, on=['geo_code', 'geo_name', 'year', 'quarter', 'time_period'], how='left')

# Replace zeros with NaN for correct interpolation
df_tableau['import_meur'] = df_tableau['import_meur'].replace(0, np.nan)
df_tableau['export_meur'] = df_tableau['export_meur'].replace(0, np.nan)

# Linearly interpolate by country and fill extremities
df_tableau['import_meur'] = df_tableau.groupby('geo_code')['import_meur'].transform(lambda x: x.interpolate(method='linear').ffill().bfill())
df_tableau['export_meur'] = df_tableau.groupby('geo_code')['export_meur'].transform(lambda x: x.interpolate(method='linear').ffill().bfill())

# Ensure no country is left with residual null or zero values
df_tableau['import_meur'] = df_tableau['import_meur'].fillna(df_tableau['import_meur'].median())
df_tableau['export_meur'] = df_tableau['export_meur'].fillna(df_tableau['export_meur'].median())

# Recreate derived metrics
df_tableau['trade_balance_meur'] = df_tableau['export_meur'] - df_tableau['import_meur']
df_tableau['total_trade_volume_meur'] = df_tableau['export_meur'] + df_tableau['import_meur']

# Calculate QoQ and YoY growth rates
df_tableau['prev_quarter_export'] = df_tableau.groupby('geo_code')['export_meur'].shift(1)
df_tableau['prev_year_export'] = df_tableau.groupby('geo_code')['export_meur'].shift(4)

df_tableau['export_growth_qoq_pct'] = np.where(
    df_tableau['prev_quarter_export'].notnull() & (df_tableau['prev_quarter_export'] > 0),
    ((df_tableau['export_meur'] - df_tableau['prev_quarter_export']) * 100.0 / df_tableau['prev_quarter_export']).round(2),
    None
)

df_tableau['export_growth_yoy_pct'] = np.where(
    df_tableau['prev_year_export'].notnull() & (df_tableau['prev_year_export'] > 0),
    ((df_tableau['export_meur'] - df_tableau['prev_year_export']) * 100.0 / df_tableau['prev_year_export']).round(2),
    None
)

df_tableau = df_tableau.drop(columns=['prev_quarter_export', 'prev_year_export'])
df_tableau = df_tableau.sort_values(['geo_name', 'year', 'quarter']).reset_index(drop=True)

print("Step 3: Saving continuous grid view back into SQLite...")
df_tableau.to_sql("tableau_ready_view", connection, if_exists="replace", index=False)

csv_filename = "tableau_ready_view.csv"
df_tableau.to_csv(csv_filename, index=False)
print(f"Step 4: CSV file successfully exported as '{csv_filename}'!")

connection.close()

print(f"\nSuccess! Continuous timeline view updated with {len(df_tableau)} rows.")
