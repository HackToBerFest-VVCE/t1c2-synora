# t1c2-synora
Private hackathon repository for Synora
# BillSense — Explain the Unexpected Bill

# SYNORA — BillSense ⚡

### AI-Powered Electricity Bill Analysis Using Snowflake

BillSense is an electricity bill analysis application designed to help users understand changes in household electricity consumption and billing amounts. It combines bill comparison, AI-generated insights, and Karnataka domestic electricity tariff data stored in Snowflake.

## Features

- **Bill comparison:** Compare previous and current electricity bills, units consumed, and billing periods.
- **AI-powered insights:** Use Qwen2.5:3B through Ollama to generate explanations and possible causes of bill changes.
- **Snowflake integration:** Store and retrieve bill records and access Karnataka domestic electricity tariff data.
- **Tariff-based estimation:** Estimate energy and fixed charges using the selected tariff rates, consumption, sanctioned load, and billing days.
- **Bill history:** Save bill comparisons and retrieve historical records from Snowflake.
- **Bill document extraction:** Extract text from supported bill PDFs and images.

## Technology Stack

- Python
- Streamlit
- Snowflake
- Ollama
- Qwen2.5:3B
- PDF and image text-extraction tools

## Data

BillSense uses a Karnataka domestic electricity tariff dataset based on the KERC Combined Tariff Order 2025. The CSV is loaded into the following Snowflake table:

`BILLSENSE_DB.PUBLIC_DATA.KARNATAKA_DOMESTIC_TARIFF`

The application also stores bill records in:

`BILLSENSE_DB.PUBLIC_DATA.BILLS`

The tariff-based estimate covers energy and fixed charges only. It is not a complete official bill calculation and excludes other applicable charges, taxes, subsidies, and adjustments.

## Project Structure

- `app.py` — Streamlit application
- `ai_helper.py` — AI insight generation
- `test_ai.py` — AI integration testing
- `test_snowflake.py` — Snowflake connection testing
- `karnataka_domestic_electricity_tariff.csv` — Tariff data, if included in the local project

## Run Locally

1. Install Python and the required project dependencies.
2. Configure Snowflake credentials securely using Streamlit secrets.
3. Install and start Ollama, and ensure the Qwen2.5:3B model is available.
4. Install the required Python packages.
5. Run the application:

   `python -m streamlit run app.py`

Do not commit passwords, account credentials, API keys, or private configuration files.

## Team

**SYNORA**

Developed for the Snowflake-focused hackathon challenge.
