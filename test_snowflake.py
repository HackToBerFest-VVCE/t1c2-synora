import streamlit as st
import snowflake.connector

st.title("BillSense - Snowflake Connection Test")

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
        SELECT CURRENT_DATABASE(),
               CURRENT_SCHEMA(),
               CURRENT_WAREHOUSE()
    """)

    result = cursor.fetchone()

    st.success("Snowflake connected successfully!")
    st.write("Database:", result[0])
    st.write("Schema:", result[1])
    st.write("Warehouse:", result[2])

    cursor.close()
    conn.close()

except Exception as e:
    st.error("Connection failed. Check the error below.")
    st.code(str(e))