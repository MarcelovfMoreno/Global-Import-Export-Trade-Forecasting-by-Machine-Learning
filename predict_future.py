import sqlite3
import pandas as pd
import numpy as np
import joblib

database_filename = "trade_forecast.db"
model_filename = "trade_forecast_model.pkl"

print("Step 1: Connecting to SQLite database and loading trained model...")
connection = sqlite3.connect(database_filename)
model = joblib.load(model_filename)

# Select only the columns known to exist in the table
query = "SELECT geo_code, geo_name, flow_code, flow_description, time_period, value_meur, year, quarter FROM clean_trade_model_ready"
df = pd.read_sql(query, connection)

# Safely create quarter_num by extracting the numeric value from the 'quarter' string (e.g., 'Q1' becomes 1)
df["quarter_num"] = df["quarter"].str.extract(r'(\d+)').astype(int)

print(f"Loaded {len(df)} rows. Generating future predictions for missing periods...")

future_rows = []
for (geo_code, flow_code), group in df.groupby(["geo_code", "flow_code"]):
    group = group.sort_values(by=["year", "quarter_num"])
    geo_name = group["geo_name"].iloc[0]
    flow_desc = group["flow_description"].iloc[0]
    
    for target_year in [2027]:
        for target_q in [3, 4]:
            recent_vals = group["value_meur"].values
            lag_1 = recent_vals[-1]
            lag_4 = recent_vals[-4] if len(recent_vals) >= 4 else recent_vals[-1]
            
            X_pred = pd.DataFrame([[target_year, target_q, lag_1, lag_4]], columns=["year", "quarter_num", "lag_1", "lag_4"])
            pred_value = model.predict(X_pred)[0]
            
            new_row = {
                "geo_code": geo_code,
                "geo_name": geo_name,
                "flow_code": flow_code,
                "flow_description": flow_desc,
                "time_period": f"{target_year}-Q{target_q}",
                "value_meur": round(pred_value, 2),
                "year": target_year,
                "quarter": f"Q{target_q}",
                "quarter_num": target_q
            }
            future_rows.append(new_row)
            new_df_row = pd.DataFrame([new_row])
            group = pd.concat([group, new_df_row], ignore_index=True)

df_future = pd.DataFrame(future_rows)

if not df_future.empty:
    print(f"Generated {len(df_future)} predicted rows for 2027. Inserting into database...")
    # Replace the previous predictions table to prevent duplicates
    df_future.to_sql("trade_forecast_predictions", connection, if_exists="replace", index=False)
    print("Predictions successfully saved to 'trade_forecast_predictions'.")
else:
    print("No missing periods detected for prediction.")

connection.close()
print("Process completed successfully!")
