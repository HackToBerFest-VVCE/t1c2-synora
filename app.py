import snowflake.connector
import streamlit as st
import pandas as pd
from PIL import ImageOps
from ai_helper import get_bill_insights

st.set_page_config(page_title="BillSense", page_icon="💡")

st.title("💡 BillSense")
st.subheader("Explain the Unexpected Bill")
st.write("Compare two electricity bills to understand what changed.")

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
                     lang="eng+kan",
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





