# Global Import-Export & Trade Forecasting Pipeline

## 1. Project Overview & Architecture
* **Project Name:** Global Import-Export & Trade Forecasting Pipeline
* **Objective:** Build an end-to-end automated data pipeline (ETL) extracting international trade statistics directly from the Eurostat API, structuring a clean relational SQLite database, applying Machine Learning for time-series forecasting, generating automated projection tables, and adapting assets for executive BI visualization.
* **Tech Stack:** Python, Pandas, Requests, Scikit-learn, Joblib, SQLite, Tableau Public (Web), CSV Extracts.

---

## 2. Executed Step-by-Step Roadmap

* **Step 1: Programmatic Extraction via API (ETL)**
  * Established programmatic connection with the official Eurostat JSON-stat API (`namq_10_exi`).
  * Automated extraction of multi-dimensional data, capturing geographical units, trade flow items, and quarterly periods.
* **Step 2: Data Parsing & Metadata Mapping**
  * Mapped country codes to full, human-readable descriptive names.
  * Converted multi-dimensional JSON-stat arrays into a clean, structured tabular format.
* **Step 3: Rigorous Filtering & Data Cleansing**
  * Excluded regional economic blocks and monetary unions to eliminate statistical distortion and isolate strictly **sovereign countries**.
  * Performed type conversions on numerical transaction values (`value_meur`) and dropped null records.
* **Step 4: Temporal Feature Engineering**
  * Split the quarterly time period column into dedicated `year` and `quarter` attributes.
  * Imposed strict chronological sorting by country and trade flow to preserve time-series integrity.
* **Step 5: Relational Database Storage**
  * Persisted processed data into a local SQLite relational database (`trade_forecast.db`), outputting an optimized table named `clean_trade_model_ready`.
* **Step 6: Predictive Modeling (Machine Learning)**
  * Developed a Python script to engineer lag features (`lag_1`, `lag_4`) and train a robust Scikit-learn regression model (`Ridge`) over historical trade sequences.
  * Serialized and exported the trained predictive model using `Joblib` (`trade_forecast_model.pkl`).
* **Step 7: Automated Forecasting & Table Generation**
  * Implemented an automated inference script (`predict_future.py`) to fetch recent historical markers, calculate future feature vectors, and predict subsequent trade values (including Q3 and Q4 of 2027).
  * Stored future projections programmatically back into the SQLite database under `trade_forecast_predictions`.
* **Step 8: BI Integration & Tableau Public Adaptation**
  * Built a consolidated database view (`tableau_ready_view`) filtering the target analytical window strictly between **2022 and 2027**.
  * Exported the polished view directly into an optimized CSV file (`tableau_ready_view.csv`) to ensure seamless integration and compatibility with Tableau Public Web connectors, powering executive dashboards displaying trade balances, volumes, and YoY/QoQ growth metrics.

---

## 3. Executive Dashboard & Visual Architecture
* **Executive KPI Suite:** Real-time consolidated metric cards tracking **Total Trade Volume (€)**, **Total Imports (€)**, **Total Exports (€)**, and **Net Trade Balance (€)** with dynamic cross-filtering capabilities.
* **Macro Import vs. Export Time-Series:** Quarterly performance tracking spanning historical execution and machine learning predictive horizons through 2027.
* **Country Trade Volume Ranking:** Interactive matrix governing global cross-filtering across all visual elements to isolate sovereign country behaviors instantly.
* **Trade Balance Analytics:** Divergent visual modeling separating commercial surpluses from structural trade deficits by country to assess economic health at a glance.

---

## 4. Repository Structure
```text
├── exports/                  # Optimized CSV extracts for Tableau Web compatibility
│   ├── clean_trade_model_ready.csv
│   ├── trade_forecast_predictions.csv
│   └── tableau_ready_view.csv # Polished historical & predicted view (2022-2027)
├── updated/                  # Contains production-ready SQLite database & ML model
│   ├── trade_forecast.db     # Relational database (contains historical & prediction tables)
│   └── trade_forecast_model.pkl # Serialized Scikit-learn model
├── etl_pipeline.py           # Eurostat API extraction & data cleansing script
├── train_model.py            # Model training & evaluation script
├── predict_future.py         # Automated forecasting & database insertion script
├── prepare_tableau_view.py   # View consolidation, 2022-2027 filtering & CSV export script
└── README.md                 # Project documentation
```
