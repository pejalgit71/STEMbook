import streamlit as st
import gspread
import os
import json
from datetime import datetime
import io
from oauth2client.service_account import ServiceAccountCredentials
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# --------------------------------
# Google Sheets Auth (gspread)
# --------------------------------
def get_gsheet_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(creds_dict), scope)
    return gspread.authorize(creds)

gc = get_gsheet_client()
sheet = gc.open("STEM Explorer Orders").sheet1

# --------------------------------
# Google Drive Auth (googleapiclient)
# --------------------------------
def get_drive_service():
    scopes = ['https://www.googleapis.com/auth/drive']
    creds_dict = dict(st.secrets["gcp_service_account"])
    credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return build('drive', 'v3', credentials=credentials)

drive_service = get_drive_service()

# --------------------------------
# Google Drive Folder ID
# --------------------------------
FOLDER_ID = '19Vr81hUu-oEOtH11vWe-EZGGtJXNszPm'


# -----------------------------
# Pricing
# -----------------------------
BOOK_PRICE = 85
ARDUINO_KIT_PRICE = 60
DELIVERY_COST = 10

# -----------------------------
# UI
# -----------------------------
st.set_page_config(page_title="Buy STEM Explorer", layout="centered")

st.title("📘 STEM Explorasi Book Order")
st.image("STEMexplorer.jpg", width=400)

st.markdown("""
### About the Book
STEM Explorer is a hands-on educational book with real-world STEM projects.

Available options:
- 📖 **Book Only** – RM 85  
- 📖➕🔧 **Book + Arduino Kit** – RM 145  
🛵 *Delivery: RM 10 added automatically per order*
""")

st.image("QR.jpg", caption="Scan to make payment", width=250)

# -----------------------------
# Order Form
# -----------------------------
st.header("📋 Order Form")

with st.form("order_form"):
    name = st.text_input("Full Name")
    phone = st.text_input("Phone Number")
    email = st.text_input("Email")
    address = st.text_area("Postal Address")
    option = st.selectbox("Select your option", ["Book Only", "Book + Arduino Kit"])
    quantity = st.number_input("Quantity", min_value=1, max_value=100, value=1)
    uploaded_receipt = st.file_uploader("Upload Payment Receipt", type=["jpg", "jpeg", "png", "pdf"])

    submitted = st.form_submit_button("Submit Order")

    if submitted:
        if not all([name, phone, email, address, uploaded_receipt]):
            st.warning("⚠️ Please fill in all fields and upload your receipt.")
        else:
            # Calculate cost
            base_price = BOOK_PRICE + (ARDUINO_KIT_PRICE if option == "Book + Arduino Kit" else 0)
            total = (base_price * quantity) + DELIVERY_COST
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            safe_name = name.replace(" ", "_")
            file_date = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{safe_name}_{file_date}.{uploaded_receipt.name.split('.')[-1]}"

            # Upload to Google Drive
            file_stream = io.BytesIO(uploaded_receipt.getvalue())
            media = MediaIoBaseUpload(file_stream, mimetype=uploaded_receipt.type)
            file_metadata = {
                'name': filename,
                'parents': [FOLDER_ID]
            }
            try:
                uploaded_file = drive_service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id'
                ).execute()
            
                file_id = uploaded_file.get('id')
                file_link = f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"
            
            except Exception as e:
                
                st.error("❌ Failed to upload file to Google Drive. Please check your permissions, folder ID, and file size.")
                st.exception(e)  # This will display the full traceback and actual error message in Streamlit
                st.stop()

            # Save to Google Sheet
            sheet.append_row([timestamp, name, phone, email, address, option, quantity, total, file_link])

            st.success(f"✅ Order submitted! Quantity: {quantity}, Total: RM {total}")
            st.info("Your receipt has been uploaded and linked to your order. We'll verify it and contact you soon.")
