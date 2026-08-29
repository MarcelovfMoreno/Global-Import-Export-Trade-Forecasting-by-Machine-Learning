import pandas as pd
import requests
import sqlite3

# Save directly in the project directory using a safe relative path
database_filename = "trade_forecast.db"
api_url = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/namq_10_exi?format=JSON&unit=CP_MEUR&s_adj=NSA&lang=EN"

print("Step 1: Connecting to Eurostat API to fetch raw trade data...")
response = requests.get(api_url)

if response.status_code == 200:
  data = response.json()
  print("Data extracted successfully from API!")

  values = data.get("value", {})
  dimensions = data.get("dimension", {})

  geo_dimension = dimensions.get("geo", {})
  geo_category_index = geo_dimension.get("category", {}).get("index", {})
  geo_category_label = geo_dimension.get("category", {}).get("label", {})

  item_dimension = dimensions.get("na_item", {})
  item_category_index = item_dimension.get("category", {}).get("index", {})
  item_category_label = item_dimension.get("category", {}).get("label", {})

  time_category = (
      dimensions.get("time", {}).get("category", {}).get("index", {})
  )

  geo_keys = list(geo_category_index.keys())
  item_keys = list(item_category_index.keys())
  time_keys = list(time_category.keys())

  geo_length = len(geo_keys)
  item_length = len(item_keys)
  time_length = len(time_keys)

  print(f"Dimensions -> Geographies: {geo_length} | Trade Flows: {item_length} | Time Periods: {time_length}")

  print("Step 2: Parsing multi-dimensional JSON-stat structure...")
  parsed_rows = []
  for flat_idx_str, val in values.items():
    flat_index = int(flat_idx_str)

    time_index = flat_index % time_length
    remaining = flat_index // time_length
    item_index = remaining % item_length
    geo_index = remaining // item_length

    geo_code = geo_keys[geo_index] if geo_index < geo_length else None
    geo_name = geo_category_label.get(geo_code, geo_code) if geo_code else None

    item_code = item_keys[item_index] if item_index < item_length else None
    item_name = item_category_label.get(item_code, item_code) if item_code else None

    time_period = time_keys[time_index] if time_index < time_length else None

    parsed_rows.append(
        {
            "geo_code": geo_code,
            "geo_name": geo_name,
            "flow_code": item_code,
            "flow_description": item_name,
            "time_period": time_period,
            "value_meur": val,
        }
    )

  df = pd.DataFrame(parsed_rows)

  print("Step 3: Cleaning data, converting types, and filtering sovereign countries...")
  df["value_meur"] = pd.to_numeric(df["value_meur"], errors="coerce")
  df = df.dropna(subset=["geo_code", "flow_code", "time_period", "value_meur"])

  # Strict filter to exclude economic blocks/unions and keep only individual countries
  aggregates_to_exclude = [
      "EU27_2020", "EU28", "EU15", "EA19", "EA20", "EA12", "EA18", 
      "EFTA", "CANDIDATE_COUNTRIES", "EXT_EU27_2020", "EXT_EU28", 
      "NACE_R2", "TOTAL", "WRL_REST"
  ]
  
  df = df[
      ~df["geo_code"].str.startswith(("EA", "EU", "EXT"), na=False) & 
      ~df["geo_code"].isin(aggregates_to_exclude)
  ]

  # Filtro direto para os 10 mercados-chave selecionados
  target_core_countries = [
      "Germany", "Netherlands", "Ireland", "Spain", 
      "Portugal", "Italy", "Luxembourg", "Belgium", 
      "France", "Austria"
  ]
  
  df = df[df["geo_name"].isin(target_core_countries)]

  # Split time_period into year and quarter for ML and time-series modeling
  df[["year", "quarter"]] = df["time_period"].str.split("-", expand=True)
  df["year"] = df["year"].astype(int)

  # Sort chronologically
  df = df.sort_values(by=["geo_code", "flow_code", "year", "quarter"]).reset_index(drop=True)

  print(f"Processed clean dataset ready for core markets. Total clean rows: {len(df)}")

  print("Step 4: Saving polished table into SQLite database...")
  connection = sqlite3.connect(database_filename)
  df.to_sql("clean_trade_model_ready", connection, if_exists="replace", index=False)
  connection.close()

  print(f"Absolute success! Pipeline executed with your 10 target markets. Table 'clean_trade_model_ready' updated in: {database_filename}")

else:
  print(f"Request error: {response.status_code}")