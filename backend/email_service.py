import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os
from dotenv import load_dotenv

load_dotenv()

class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv("MAIL_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("MAIL_PORT", "587"))
        self.username = os.getenv("MAIL_USERNAME")
        self.password = os.getenv("MAIL_PASSWORD")
        self.from_email = os.getenv("MAIL_FROM", self.username)
        # For development/playground, we can default to a dummy if env vars aren't set
        # effectively mocking it unless configured.
        self.configured = bool(self.username and self.password)

    def send_tax_return_email(self, to_email: str, pdf_bytes: bytes, filename: str = "TaxReturn_2025.pdf"):
        if not self.configured:
            print(f"[MOCK EMAIL] To: {to_email} | Attachment: {filename} ({len(pdf_bytes)} bytes)")
            print("[MOCK EMAIL] Configure MAIL_USERNAME and MAIL_PASSWORD to send real emails.")
            return True

        try:
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = "Your 2025 Tax Return Package"

            body = """
            Hello,

            Please find attached your complete 2025 Tax Return package (Form 1040-NR and applicable schedules).

            Instructions:
            1. Print the attached PDF.
            2. Sign and date the return on page 1.
            3. Mail it to the IRS address listed in the 1040-NR instructions.
            
            Thank you for using our service!
            """
            msg.attach(MIMEText(body, 'plain'))

            # Attach PDF
            part = MIMEApplication(pdf_bytes, Name=filename)
            part['Content-Disposition'] = f'attachment; filename="{filename}"'
            msg.attach(part)

            # Send
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            print(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            print(f"Failed to send email: {e}")
            return False
