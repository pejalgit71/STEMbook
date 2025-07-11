import streamlit as st
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io

# --------------------------------
# Google Sheets & Drive Setup
# --------------------------------
SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = 'ave2025-fbe390c33c3d.json'

credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
gc = gspread.authorize(credentials)

# Google Sheet setup
sheet = gc.open("STEM Explorer Orders").sheet1

# Google Drive setup
drive_service = build('drive', 'v3', credentials=credentials)

# Replace with your actual Google Drive folder ID
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

st.title("📘 STEM Explorer Book Order")
st.image("STEMexplorer.jpg", width=300)

st.markdown("""
### About the Book
STEM Explorer is a hands-on educational book with real-world STEM projects.

Available options:
- 📖 **Book Only** – RM 85  
- 📖➕🔧 **Book + Arduino Kit** – RM 145 
🛵 *Delivery: RM 10 added automatically*
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
    uploaded_receipt = st.file_uploader("Upload Payment Receipt", type=["jpg", "jpeg", "png", "pdf"])

    submitted = st.form_submit_button("Submit Order")

    if submitted:
        if not all([name, phone, email, address, uploaded_receipt]):
            st.warning("⚠️ Please fill in all fields and upload your receipt.")
        else:
            # Calculate cost
            base_price = BOOK_PRICE + (ARDUINO_KIT_PRICE if option == "Book + Arduino Kit" else 0)
            total = base_price + DELIVERY_COST
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
            uploaded_file = drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()

            file_id = uploaded_file.get('id')
            file_link = f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"

            # Save to Google Sheet
            sheet.append_row([timestamp, name, phone, email, address, option, total, file_link])

            st.success(f"✅ Order submitted! Total: RM {total}")
            st.info("Your receipt has been uploaded and linked to your order. We'll verify it and contact you soon.")
