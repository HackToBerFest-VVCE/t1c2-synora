import snowflake.connector
import streamlit as st
import pandas as pd
from PIL import ImageOps
from ai_helper import get_bill_insights


import numpy as np


def analyze_bill_history(history, current_amount, current_units, current_days):
    """
    Analyze a current bill against historical monthly bills.
    Uses daily averages and robust median/MAD statistics.
    """

    required = ["BILL_AMOUNT", "UNITS_KWH", "BILLING_DAYS"]
    history = history.copy()

    # Convert database values to numeric and remove invalid rows
    for column in required:
        history[column] = pd.to_numeric(
            history[column], errors="coerce"
        )

    history = history.dropna(subset=required)

    history = history[
        (history["BILL_AMOUNT"] >= 0)
        & (history["UNITS_KWH"] >= 0)
        & (history["BILLING_DAYS"] > 0)
    ].copy()

    if len(history) < 5:
        return None, (
            f"Only {len(history)} valid historical bills found. "
            "Save at least 5 genuine past monthly bills for "
            "a more useful statistical comparison."
        )

    # Normalize for different billing-period lengths
    history["DAILY_UNITS"] = (
        history["UNITS_KWH"] / history["BILLING_DAYS"]
    )
    history["DAILY_AMOUNT"] = (
        history["BILL_AMOUNT"] / history["BILLING_DAYS"]
    )

    current_daily_units = current_units / current_days
    current_daily_amount = current_amount / current_days

    metrics = {
        "Daily consumption (kWh/day)": (
            history["DAILY_UNITS"], current_daily_units
        ),
        "Daily bill cost (₹/day)": (
            history["DAILY_AMOUNT"], current_daily_amount
        ),
    }

    results = {}

    for label, (past_values, current_value) in metrics.items():
        median = float(past_values.median())
        mean = float(past_values.mean())
        std = float(past_values.std(ddof=1))
        mad = float((past_values - median).abs().median())

        # Robust anomaly score: less sensitive to extreme old bills
        if mad > 0:
            robust_z = 0.6745 * (current_value - median) / mad
        elif std > 0:
            robust_z = (current_value - mean) / std
        else:
            robust_z = 0.0 if current_value == median else None

        pct_vs_median = (
            ((current_value - median) / median) * 100
            if median > 0 else None
        )

        results[label] = {
            "current": current_value,
            "historical_mean": mean,
            "historical_median": median,
            "historical_std": std,
            "change_pct_vs_median": pct_vs_median,
            "robust_z": robust_z,
        }

    # Historical total bill amount and units are also summarized
    summary = {
        "history_count": len(history),
        "historical_amount_median": float(
            history["BILL_AMOUNT"].median()
        ),
        "historical_units_median": float(
            history["UNITS_KWH"].median()
        ),
        "metrics": results,
    }

    return summary, None



st.set_page_config(
    page_title="BillSense | Energy Dashboard",
    page_icon="💡",
    layout="wide"
)




st.markdown(
    """
    <style>
    .billsense-heading {
        color: white;
        font-size: 38px;
        font-weight: 700;
        margin-top: -105px;
        margin-bottom: 12px;
        padding-left: 22px;
    }
    .billsense-subtitle {
        color: #F0FFF4;
        font-size: 17px;
        margin-bottom: 35px;
        padding-left: 22px;
    }
    </style>
    <div class="billsense-heading">💡 BillSense</div>
    <div class="billsense-subtitle">
        Understand your electricity bills. Discover usage changes.
        Make smarter energy decisions.
    </div>
    """,
    unsafe_allow_html=True,
)



st.set_page_config(
    page_title="BillSense | Energy Dashboard",
    page_icon="💡",
    layout="wide"
)

st.markdown("""
<style>
    .stApp {
        background-color: #F5F9F5;
        color: #193528;
    }

    [data-testid="stHeader"] {
        background-color: #F5F9F5;
    }

    h1, h2, h3 {
        color: #176B45;
    }

    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #DCEBDD;
        padding: 18px;
        border-radius: 14px;
    }

    div.stButton > button {
        background-color: #16804A;
        color: white;
        border: none;
        border-radius: 10px;
        padding: 10px 18px;
        font-weight: 600;
    }

    div.stButton > button:hover {
        background-color: #11663A;
        color: white;
        border: 1px solid #11663A;
    }

    div[data-testid="stFileUploader"] {
        background-color: #FFFFFF;
        border: 1px dashed #9BC9A7;
        border-radius: 12px;
        padding: 12px;
    }

    hr {
        border-color: #DCEBDD;
    }
</style>
""", unsafe_allow_html=True)






st.subheader("Understand your electricity bills")
st.write(
    "Discover usage changes and make smarter energy decisions."
)



st.markdown(
    """
    <div style="
        background: linear-gradient(135deg, #176B45, #2E9862);
        padding: 28px 32px;
        border-radius: 18px;
        margin-bottom: 28px;
        color: white;
    ">
        <div style="font-size: 13px; letter-spacing: 2px; color: #D8F3DF;">
            SMART ENERGY ANALYTICS
        </div>
        <h1 style="color: white; font-size: 38px; margin: 10px 0;">
            💡 BillSense
        </h1>
        
    </div>
    """,
    unsafe_allow_html=True,
)

col1, col2 = st.columns(2)


with col1:
    st.header("Previous Bill")
    previous_amount = st.number_input(
        "Previous amount (₹)", min_value=0.0, value=1500.0
    )
    previous_units = st.number_input(
        "Previous usage (kWh)", min_value=0.0, value=180.0
    )
    previous_days = st.number_input(
        "Previous billing days", min_value=1, value=30
    )

with col2:
    st.header("Current Bill")
    current_amount = st.number_input(
        "Current amount (₹)", min_value=0.0, value=2400.0
    )
    current_units = st.number_input(
        "Current usage (kWh)", min_value=0.0, value=240.0
    )
    current_days = st.number_input(
        "Current billing days", min_value=1, value=30
    )
    
sanctioned_load = st.number_input(
    "Sanctioned load (kW)",
    min_value=0.1,
    value=2.0,
    step=0.5
)


st.header("Household Changes")
changes = st.multiselect(
    "Did anything change during this billing period?",
    [
        "New appliance",
        "More air-conditioner use",
        "More people or guests",
        "Unusual weather",
        "Changed daily routine",
        "No known changes"
    ]
)

if st.button("Explain My Bill", type="primary"):

    st.header("Your BillSense Report")
    
    st.subheader("📈 Historical Statistical Analysis")

    conn = None
    cursor = None
    try:
        conn = snowflake.connector.connect(
            account=st.secrets["snowflake"]["account"],
            user=st.secrets["snowflake"]["user"],
            password=st.secrets["snowflake"]["password"],
            warehouse=st.secrets["snowflake"]["warehouse"],
            database=st.secrets["snowflake"]["database"],
            schema=st.secrets["snowflake"]["schema"],
            role=st.secrets["snowflake"]["role"],
        )

        cursor = conn.cursor()

        cursor.execute("""
            SELECT BILL_ID, BILL_TYPE, BILL_AMOUNT,
                   UNITS_KWH, BILLING_DAYS, CREATED_AT
            FROM BILLSENSE_DB.PUBLIC_DATA.BILLS
            WHERE UPPER(BILL_TYPE) = 'CURRENT'
            ORDER BY CREATED_AT DESC, BILL_ID DESC
            LIMIT 12
        """)

        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        history = pd.DataFrame(rows, columns=columns)

        # Exclude the current bill if it was already saved previously.
        # The selected history must represent earlier bills only.
        if not history.empty:
            history = history.drop_duplicates(
                subset=["BILL_AMOUNT", "UNITS_KWH", "BILLING_DAYS"],
                keep="first"
            )

        stats, warning_message = analyze_bill_history(
            history,
            current_amount,
            current_units,
            current_days
        )

        if warning_message:
            st.warning(warning_message)

        else:
            st.write(
                f"Compared against {stats['history_count']} "
                "historical bill records."
            )

            st.caption(
                "Historical records must represent genuine, distinct "
                "billing periods. Duplicate values can occur naturally, "
                "so verify dates before relying on this analysis."
            )

            
            # Explain the statistics in everyday language
            metric_explanations = {
                "Daily consumption (kWh/day)": {
                    "title": "⚡ Electricity Used Per Day",
                    "unit": "units/day",
                    "description": "This shows how many units of electricity you use each day."
                },
                "Daily bill cost (₹/day)": {
                    "title": "💰 Electricity Cost Per Day",
                    "unit": "₹/day",
                    "description": "This shows approximately how much your electricity costs per day."
                }
            }

            for label, values in stats["metrics"].items():
                details = metric_explanations.get(label, {
                    "title": label,
                    "unit": "",
                    "description": "This is compared with your previous bills."
                })

                current = values["current"]
                usual = values["historical_median"]
                pct = values["change_pct_vs_median"]
                z = values["robust_z"]

                st.markdown(f"### {details['title']}")
                st.caption(details["description"])

                col_a, col_b, col_c = st.columns(3)

                col_a.metric(
                    "Your current bill",
                    f"{current:.2f} {details['unit']}"
                )
                col_b.metric(
                    "Your usual level",
                    f"{usual:.2f} {details['unit']}"
                )
                col_c.metric(
                    "Difference from usual",
                    f"{pct:+.1f}%" if pct is not None else "N/A"
                )

                if pct is None:
                    st.info(
                        "We cannot calculate the percentage difference "
                        "because the usual value is zero or unavailable."
                    )
                elif z is not None and abs(z) >= 3.5:
                    if pct > 0:
                        st.warning(
                            f"This is much higher than your usual level "
                            f"({pct:.1f}% higher). Check whether you used "
                            "more electricity or whether the bill details "
                            "are correct."
                        )
                    else:
                        st.warning(
                            f"This is much lower than your usual level "
                            f"({abs(pct):.1f}% lower). Check your meter "
                            "reading and billing details."
                        )
                elif pct > 0:
                    st.info(
                        f"You are using or spending {pct:.1f}% more "
                        "than your usual level. This may be normal if "
                        "your household used more electricity."
                    )
                elif pct < 0:
                    st.success(
                        f"You are using or spending {abs(pct):.1f}% less "
                        "than your usual level. That's a decrease compared "
                        "with your previous bills."
                    )
                else:
                    st.success(
                        "This is almost exactly the same as your usual level."
                    )
                    
            # ---------------- MONTHLY ELECTRICITY SUMMARY ----------------
            st.markdown("---")
            st.header("🏠 Your Monthly Electricity Summary")
            st.write(
                "Here is an estimate of your electricity usage and cost "
                "for a 30-day month, based on your current bill."
            )

            monthly_units = (current_units / current_days) * 30
            monthly_cost = (current_amount / current_days) * 30

            col1, col2 = st.columns(2)
            with col1:
                st.metric(
                    label="Estimated Monthly Electricity Usage",
                    value=f"{monthly_units:.1f} units",
                )
            with col2:
                st.metric(
                    label="Estimated Monthly Electricity Cost",
                    value=f"₹{monthly_cost:,.2f}",
                )

            st.info(
                f"If your current daily usage continues, you may use "
                f"approximately {monthly_units:.1f} units and spend "
                f"₹{monthly_cost:,.2f} over 30 days. "
                "Your actual bill may differ depending on usage, tariff "
                "slabs, fixed charges, taxes and adjustments."
            )

            st.markdown("### 🏠 What does this mean for you?")

            consumption = stats["metrics"].get(
                "Daily consumption (kWh/day)"
            )
            cost = stats["metrics"].get("Daily bill cost (₹/day)")

            if consumption is not None and cost is not None:
                usage_pct = consumption["change_pct_vs_median"]
                cost_pct = cost["change_pct_vs_median"]

                if usage_pct is not None and cost_pct is not None:
                    if usage_pct < 0 and cost_pct < 0:
                        st.success(
                            "Your daily electricity use and daily cost "
                            "are both lower than usual."
                        )
                    elif usage_pct > 0 and cost_pct > 0:
                        st.warning(
                            "Both your daily electricity use and daily "
                            "cost are higher than usual. Think about "
                            "whether you used more appliances recently."
                        )
                    elif usage_pct > 0 and cost_pct < 0:
                        st.info(
                            "You are using more electricity per day, "
                            "but your daily cost is lower than usual. "
                            "Check the bill details to understand why."
                        )
                    elif usage_pct < 0 and cost_pct > 0:
                        st.info(
                            "You are using less electricity per day, "
                            "but your daily cost is higher than usual. "
                            "Check fixed charges, adjustments, and "
                            "other items on your bill."
                        )
                    else:
                        st.info(
                            "Your electricity use and cost are close "
                            "to their usual levels."
                        )

            st.caption(
                "We compare your current bill with your saved past bills. "
                "A change does not automatically mean something is wrong. "
                "Actual charges can also depend on tariffs, fixed charges, "
                "subsidies, taxes, and other adjustments."
            )

            st.markdown("#### Historical bill summary")

            summary_data = pd.DataFrame({
                "Metric": ["Bill amount (₹)", "Consumption (kWh)"],
                "Historical median": [
                    stats["historical_amount_median"],
                    stats["historical_units_median"],
                ],
                "Current bill": [current_amount, current_units],
            })

            st.dataframe(summary_data, use_container_width=True)

    except Exception as e:
        st.error("Historical analysis could not be completed.")
        st.code(str(e))

    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


    amount_change = current_amount - previous_amount
    units_change = current_units - previous_units

    amount_pct = (
        amount_change / previous_amount * 100
        if previous_amount > 0 else None
    )

    units_pct = (
        units_change / previous_units * 100
        if previous_units > 0 else None
    )

    previous_daily = previous_units / previous_days
    current_daily = current_units / current_days

    c1, c2 = st.columns(2)
    c1.metric(
        "Bill amount change",
        f"₹{amount_change:,.2f}",
        f"{amount_pct:+.1f}%" if amount_pct is not None else None
    )
    c2.metric(
        "Usage change",
        f"{units_change:+.1f} kWh",
        f"{units_pct:+.1f}%" if units_pct is not None else None
    )

    st.subheader("Usage and Cost Comparison")

    chart_data = pd.DataFrame({
        "Previous bill": [previous_units, previous_amount],
        "Current bill": [current_units, current_amount]
    }, index=["Usage (kWh)", "Amount (₹)"])

    st.bar_chart(chart_data)

    st.subheader("🔎 BillSense Analysis")

    st.markdown("### 1. Verified findings")

    st.write(
          f"Your bill changed by ₹{amount_change:,.2f}."
      )

    if amount_pct is not None:
          st.write(f"That is a {amount_pct:+.1f}% change in the bill amount.")

    st.write(
          f"Electricity usage changed by {units_change:+.1f} kWh."
      )

    if units_pct is not None:
          st.write(f"That is a {units_pct:+.1f}% change in usage.")

    st.write(
          f"Average daily usage changed from {previous_daily:.2f} "
          f"to {current_daily:.2f} kWh/day."
      )

    st.markdown("### 2. What might explain the change?")

    if amount_change > 0 and units_change > 0:
          st.info(
              "Both the bill amount and electricity usage increased. "
              "Higher usage may be one contributor, but these figures "
              "alone cannot establish the full reason for the increase."
          )
    elif amount_change > 0 and units_change <= 0:
          st.warning(
              "The bill increased even though recorded usage did not. "
              "Check the tariff rate, fixed charges, taxes, adjustments "
              "and meter readings."
          )
    elif amount_change <= 0 and units_change > 0:
          st.info(
              "Usage increased while the bill amount did not. "
              "Check the itemized charges and applicable rates to "
              "understand the difference."
          )
    else:
          st.info(
              "Neither the bill amount nor recorded usage increased. "
              "Review the bill details for any other changes."
          )

    if changes and "No known changes" not in changes:
          st.markdown("### 3. Household context")

          st.write(
              "You reported these changes: " + ", ".join(changes) + "."
          )

          st.caption(
              "These changes may be relevant, but they do not prove "
              "the cause of the bill difference."
          )

    st.markdown("### 4. What should you check next?")

    for item in [
          "Compare the billing period and meter readings on both bills.",
          "Compare the per-unit tariff and fixed charges.",
          "Check taxes, arrears, rebates and other adjustments.",
          "Review recent changes in appliance use or daily routine."
      ]:
          st.write("☐ " + item)

    st.caption(
          "BillSense distinguishes measured differences from possible "
          "causes. Confirm the itemized bill details before drawing "
          "a conclusion."
      )
    
    st.divider()
    st.subheader("🤖 AI-Powered Bill Insights")

    bill_details = {
        "previous_bill_amount_rupees": previous_amount,
        "current_bill_amount_rupees": current_amount,
        "previous_usage_kwh": previous_units,
        "current_usage_kwh": current_units,
        "previous_billing_days": previous_days,
        "current_billing_days": current_days,
        "reported_household_changes": changes
    }

    with st.spinner("Qwen2.5 is analyzing your bills..."):
        ai_insights = get_bill_insights(bill_details)

    st.markdown(ai_insights)
    st.caption(
        "AI-generated suggestions are informational. "
        "Verify your actual bill details before acting on them."
    )


    
st.divider()

st.header("☁️ Bills Stored in Snowflake")

if st.button("View Snowflake Bills"):
    conn = None
    cursor = None

    try:
        conn = snowflake.connector.connect(
            account=st.secrets["snowflake"]["account"],
            user=st.secrets["snowflake"]["user"],
            password=st.secrets["snowflake"]["password"],
            warehouse=st.secrets["snowflake"]["warehouse"],
            database=st.secrets["snowflake"]["database"],
            schema=st.secrets["snowflake"]["schema"],
            role=st.secrets["snowflake"]["role"],
        )

        cursor = conn.cursor()
        cursor.execute("""
            SELECT BILL_ID, BILL_TYPE, BILL_AMOUNT,
                   UNITS_KWH, BILLING_DAYS, CREATED_AT
            FROM BILLSENSE_DB.PUBLIC_DATA.BILLS
            ORDER BY BILL_ID
        """)

        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]

        st.dataframe(
            pd.DataFrame(rows, columns=columns),
            use_container_width=True
        )

        st.success(f"Retrieved {len(rows)} bills from Snowflake!")

    except Exception as e:
        st.error("Could not retrieve bills from Snowflake.")
        st.code(str(e))

    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()

    
st.divider()
st.header("💾 Save Bill Comparison to Snowflake")

if st.button("Save Current Comparison"):
    conn = None
    cursor = None

    try:
        conn = snowflake.connector.connect(
            account=st.secrets["snowflake"]["account"],
            user=st.secrets["snowflake"]["user"],
            password=st.secrets["snowflake"]["password"],
            warehouse=st.secrets["snowflake"]["warehouse"],
            database=st.secrets["snowflake"]["database"],
            schema=st.secrets["snowflake"]["schema"],
            role=st.secrets["snowflake"]["role"],
        )

        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO BILLSENSE_DB.PUBLIC_DATA.BILLS
                (BILL_TYPE, BILL_AMOUNT, UNITS_KWH, BILLING_DAYS)
            VALUES
                (%s, %s, %s, %s),
                (%s, %s, %s, %s)
            """,
            (
                "Previous", previous_amount, previous_units, previous_days,
                "Current", current_amount, current_units, current_days,
            ),
        )

        conn.commit()
        st.success("Both bills saved to Snowflake successfully!")

    except Exception as e:
        st.error("Could not save bills to Snowflake.")
        st.code(str(e))

    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


st.divider()

st.header("📊 Bill History Dashboard")

if st.button("Load Bill History"):
    conn = None
    cursor = None

    try:
        conn = snowflake.connector.connect(
            account=st.secrets["snowflake"]["account"],
            user=st.secrets["snowflake"]["user"],
            password=st.secrets["snowflake"]["password"],
            warehouse=st.secrets["snowflake"]["warehouse"],
            database=st.secrets["snowflake"]["database"],
            schema=st.secrets["snowflake"]["schema"],
            role=st.secrets["snowflake"]["role"],
        )

        cursor = conn.cursor()
        cursor.execute("""
            SELECT BILL_ID, BILL_TYPE, BILL_AMOUNT,
                   UNITS_KWH, BILLING_DAYS, CREATED_AT
            FROM BILLSENSE_DB.PUBLIC_DATA.BILLS
            ORDER BY BILL_ID
        """)

        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        history = pd.DataFrame(rows, columns=columns)

        if history.empty:
            st.info("No saved bills yet.")
        else:
            st.subheader("Saved Bills")
            st.dataframe(history, use_container_width=True)

            st.subheader("Electricity Usage History")
            st.bar_chart(
                history.set_index("BILL_ID")["UNITS_KWH"]
            )

            st.subheader("Bill Amount History")
            st.bar_chart(
                history.set_index("BILL_ID")["BILL_AMOUNT"]
            )

            st.caption(
                "Each bar represents a saved bill record. "
                "Repeated test entries may appear more than once."
            )

    except Exception as e:
        st.error("Could not load bill history.")
        st.code(str(e))

    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


st.divider()

st.header("📄 Upload Electricity Bill PDF")

uploaded_pdf = st.file_uploader(
    "Choose an electricity bill PDF",
    type=["pdf"],
    key="bill_pdf_upload"
)

if uploaded_pdf is not None:
    import pdfplumber

    try:
        
        import pdfplumber
        import pytesseract
        from pdf2image import convert_from_bytes

        pytesseract.pytesseract.tesseract_cmd = (
            r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        )

        with pdfplumber.open(uploaded_pdf) as pdf:
            extracted_text = "\n".join(
                page.extract_text() or ""
                for page in pdf.pages
            )

        if not extracted_text.strip():
            st.info("Scanned PDF detected. Trying OCR...")
            images = convert_from_bytes(
                uploaded_pdf.getvalue(),
                poppler_path=r"C:\Release-26.09.0-0\poppler-26.09.0\Library\bin"
            )
            


        ocr_results = []

        for image in images:
         processed_image = image.convert("L")
         processed_image = ImageOps.autocontrast(processed_image)
         
         processed_image = processed_image.resize(
                     (processed_image.width * 2, processed_image.height * 2)
                 )
         
         text = pytesseract.image_to_string(
                     processed_image,
                     lang="eng",
                     config="--oem 1 --psm 3"
                 )
         
         ocr_results.append(text)
        

         extracted_text = "\n".join(ocr_results)


            



        if extracted_text.strip():
            st.success("PDF uploaded and text extracted!")
            st.text_area(
                "Extracted bill text — review it below",
                extracted_text,
                height=250
            )
            
            import re

            amount_match = re.search(
                r"(?:total\s+(?:amount|bill|payable)|amount\s+payable|net\s+amount)[^\d\n₹]{0,25}₹?\s*([\d,]+(?:\.\d{1,2})?)",
                extracted_text,
                re.IGNORECASE
            )

            units_match = re.search(
                r"(?:units\s+consumed|energy\s+consumed|consumption|kwh)\D{0,20}([\d,]+(?:\.\d+)?)",
                extracted_text,
                re.IGNORECASE
            )

            days_match = re.search(
                r"(?:billing\s+days|bill\s+days|no\.?\s+of\s+days|days\s+of\s+consumption)\D{0,15}(\d{1,3})",
                extracted_text,
                re.IGNORECASE
            )

            st.subheader("🔍 Detected Bill Details")

            if amount_match:
                detected_amount = float(
                    amount_match.group(1).replace(",", "")
                )
                st.write(f"Possible bill amount: ₹{detected_amount:,.2f}")
            else:
                st.warning(
                    "Bill amount not detected reliably. "
                    "Please check the extracted text."
                )

            if units_match:
                detected_units = float(
                    units_match.group(1).replace(",", "")
                )
                st.write(f"Possible electricity usage: {detected_units:g} kWh")
            else:
                st.warning(
                    "Electricity usage not detected. "
                    "Please check the extracted text."
                )

            if days_match:
                detected_days = int(days_match.group(1))
                st.write(f"Possible billing days: {detected_days}")
            else:
                st.warning(
                    "Billing days not detected. "
                    "Please check the extracted text."
                )

            st.caption(
                "These are pattern-based guesses, not verified values. "
                "Check the original bill before using them."
            )

        else:
            st.warning(
                "No selectable text found. This may be a scanned PDF; "
                "we can add OCR support later."
            )

    except Exception as e:
        st.error("Could not read this PDF.")
        st.code(str(e))
        
st.divider()
st.header("⚡ Karnataka Domestic Electricity Tariff")

if st.button("View Karnataka Tariff Rates"):
    conn = None
    cursor = None

    try:
        conn = snowflake.connector.connect(
            account=st.secrets["snowflake"]["account"],
            user=st.secrets["snowflake"]["user"],
            password=st.secrets["snowflake"]["password"],
            warehouse=st.secrets["snowflake"]["warehouse"],
            database=st.secrets["snowflake"]["database"],
            schema=st.secrets["snowflake"]["schema"],
            role=st.secrets["snowflake"]["role"],
        )

        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT FIXED_CHARGE_INR_PER_KW_MONTH,
                   ENERGY_CHARGE_INR_PER_KWH
            FROM BILLSENSE_DB.PUBLIC_DATA.KARNATAKA_DOMESTIC_TARIFF
            WHERE FINANCIAL_YEAR = '2026-27'
            LIMIT 1
        """)
        
        tariff = cursor.fetchone()

        if tariff is None:
            st.warning("No tariff found for 2026-27.")
        else:
            fixed_rate, energy_rate = tariff

            energy_charge = current_units * float(energy_rate)
            fixed_charge = sanctioned_load * float(fixed_rate) * current_days / 30

            st.subheader("Estimated Karnataka Electricity Charges")
            st.metric("Energy Charge", f"₹{energy_charge:.2f}")
            st.metric("Fixed Charge", f"₹{fixed_charge:.2f}")
            st.metric(
                "Estimated Total",
                f"₹{energy_charge + fixed_charge:.2f}"
            )
            st.caption(
                "Estimate only. Excludes other applicable charges, "
                "taxes, subsidies, and adjustments."
            )


  
       
        st.success("Tariff rates loaded for FY 2026-27.")


    except Exception as e:
        st.error("Could not retrieve Karnataka tariff rates.")
        st.code(str(e))

    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()





