import os
import gspread
import smtplib
import pandas as pd
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import TypedDict, Annotated
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
import operator

from langgraph.graph import StateGraph, END

# ======================================================
# LOAD ENV
# ======================================================
load_dotenv()

GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
DATA_TAB = os.getenv("GOOGLE_SHEET_DATA_TAB")
OUTPUT_TAB = os.getenv("GOOGLE_SHEET_OUTPUT_TAB")
SERVICE_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")

HR_EMAIL = os.getenv("HR_EMAIL")
HR_EMAIL_PASSWORD = os.getenv("HR_EMAIL_PASSWORD")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))

EMPLOYEE_CSV = "employee_details.csv"

# ======================================================
# LANGGRAPH STATE
# ======================================================
class AgentState(TypedDict):
    raw_attendance: list
    processed_attendance: Annotated[list, operator.add]
    email_payloads: Annotated[list, operator.add]

# ======================================================
# NODE 1: FETCH GOOGLE SHEET DATA
# ======================================================
def fetch_attendance(_: dict) -> dict:
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_file(SERVICE_JSON, scopes=scopes)
    client = gspread.authorize(creds)

    sheet = client.open_by_key(GOOGLE_SHEET_ID)
    data_tab = sheet.worksheet(DATA_TAB)

    records = data_tab.get_all_records()
    return {"raw_attendance": records}

# ======================================================
# NODE 2: PROCESS YESTERDAY ATTENDANCE
# ======================================================
def process_attendance(state: AgentState) -> dict:
    employee_df = pd.read_csv(EMPLOYEE_CSV)
    yesterday = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")

    processed = []

    for row in state["raw_attendance"]:
        if row["ActivityDate"] != yesterday:
            continue

        emp_code = row["EmployeeCode"]
        check_in = datetime.strptime(row["CheckInTime"], "%H:%M:%S")
        check_out = datetime.strptime(row["CheckOutTime"], "%H:%M:%S")

        emp = employee_df[employee_df["Punch Code"] == emp_code]
        name = emp["Name"].values[0] if not emp.empty else "Unknown"
        shift = emp["Shift"].values[0] if not emp.empty else "Unknown"
        email = emp["Email"].values[0] if not emp.empty else None

        shift_start = datetime.strptime("10:00:00", "%H:%M:%S")
        shift_end = datetime.strptime("18:00:00", "%H:%M:%S")

        if check_in == check_out:
            in_status = out_status = "Missing"
        else:
            in_status = "On Time" if check_in <= shift_start + timedelta(minutes=30) else "Come Late"
            out_status = "Missing" if check_out < datetime.strptime("13:00:00", "%H:%M:%S") else \
                         "Left Early" if check_out < shift_end - timedelta(minutes=5) else "On Time"

        processed.append({
            "EmployeeCode": emp_code,
            "Name": name,
            "Shift": shift,
            "Email": email,
            "Date": yesterday,
            "CheckIn": row["CheckInTime"],
            "CheckOut": row["CheckOutTime"],
            "CheckInStatus": in_status,
            "CheckOutStatus": out_status
        })

    return {"processed_attendance": processed}

# ======================================================
# NODE 3: GENERATE EMAIL CONTENT
# ======================================================
def generate_emails(state: AgentState) -> dict:
    emails = []

    for row in state["processed_attendance"]:
        if not row["Email"]:
            continue

        body = f"""
Dear {row['Name']},

Here is your attendance summary for {row['Date']}:

• Check-in Time: {row['CheckIn']}
• Check-in Status: {row['CheckInStatus']}
• Check-out Time: {row['CheckOut']}
• Check-out Status: {row['CheckOutStatus']}

Shift: {row['Shift']}

If you find any discrepancy, please contact HR.

Regards,  
HR Department
"""

        emails.append({
            "to": row["Email"],
            "subject": f"Attendance Summary – {row['Date']}",
            "body": body
        })

    return {"email_payloads": emails}

# ======================================================
# NODE 4: SEND EMAILS
# ======================================================
def send_emails(state: AgentState) -> dict:
    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()
    server.login(HR_EMAIL, HR_EMAIL_PASSWORD)

    for mail in state["email_payloads"]:
        msg = MIMEMultipart()
        msg["From"] = HR_EMAIL
        msg["To"] = mail["to"]
        msg["Subject"] = mail["subject"]
        msg.attach(MIMEText(mail["body"], "plain"))

        server.send_message(msg)

    server.quit()
    print("✅ Attendance emails sent successfully.")
    return {}

# ======================================================
# BUILD LANGGRAPH
# ======================================================
workflow = StateGraph(AgentState)

workflow.add_node("fetch", fetch_attendance)
workflow.add_node("process", process_attendance)
workflow.add_node("email_draft", generate_emails)
workflow.add_node("send", send_emails)

workflow.set_entry_point("fetch")
workflow.add_edge("fetch", "process")
workflow.add_edge("process", "email_draft")
workflow.add_edge("email_draft", "send")
workflow.add_edge("send", END)

app = workflow.compile()

# ======================================================
# RUN
# ======================================================
if __name__ == "__main__":
    print("🚀 Running Daily Attendance Agent...")
    app.invoke({})
