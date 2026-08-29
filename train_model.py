import sqlite3
import pandas as pd
import numpy as np
joblib_imported = True
try:
    import joblib
except ImportError:
    joblib_imported = False

from sklearn.model_selection import train_test_split
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error, mean_absolute_error

# 1. Connect and load data from SQLite database where ETL actually saved it
database_filename = r"C:\Users\helen\trade_forecast.db"
connection = sqlite3.connect(database_filename)

query = """SELECT geo_code, geo_name, flow_code,
           flow_description, time_period, value_meur, year, quarter FROM clean_trade_model_ready"""
df = pd.read_sql(query, connection)
connection.close()

print(f"Loaded {len(df)} rows from database for machine learning.")

# 2. Feature Engineering: Create Lag features and time indices
df["quarter_num"] = df["quarter"].str.replace("Q", "").astype(int)
df = df.sort_values(by=["geo_code", "flow_code", "year", "quarter_num"])

df["lag_1"] = df.groupby(["geo_code", "flow_code"])["value_meur"].shift(1)
df["lag_4"] = df.groupby(["geo_code", "flow_code"])["value_meur"].shift(4)

df_model = df.dropna(subset=["lag_1", "lag_4"]).copy()

# 3. Define Features (X) and Target (y)
features = ["year", "quarter_num", "lag_1", "lag_4"]
target = "value_meur"

X = df_model[features]
y = df_model[target]

# 4. Train/Test Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 5. Model Training (Ridge Regression)
model = Ridge(alpha=1.0)
model.fit(X_train, y_train)

# 6. Evaluation
y_pred = model.predict(X_test)
mse = mean_squared_error(y_test, y_pred)
rmse = np.sqrt(mse)
mae = mean_absolute_error(y_test, y_pred)

print(f"Model Training Completed Successfully!")
print(f"RMSE: {rmse:.2f}")
print(f"MAE: {mae:.2f}")

# 7. Save the trained model to disk
model_filename = r"C:\Users\helen\trade_forecast_model.pkl"
joblib.dump(model, model_filename)
print(f"Model successfully saved to: {model_filename}")