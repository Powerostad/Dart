import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from email_validator import validate_email, EmailNotValidError
from django.conf import settings

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class CustomSMTPServer:
    def __init__(self, server_host, server_port, username=None, password=None):
        if not server_host:
            raise ValueError("SMTP server host is required.")
        self.server_host = server_host
        self.server_port = server_port
        self.username = username
        self.password = password


    def validate_email_address(self, email):
        try:
            validate_email(email).normalized
            return True
        except EmailNotValidError:
            return False

    def send_email(self, to_email, subject, body):
        try:
            email_is_valid = self.validate_email_address(to_email)
            if not email_is_valid:
                return {"status": "error", "message": "Email is not Valid"}

            with smtplib.SMTP(self.server_host, self.server_port, timeout=30) as server:
                server.set_debuglevel(0)
                server.starttls(context=ssl.create_default_context())
                if self.username and self.password:
                    server.login(self.username, self.password)

                # Create the email message
                msg = MIMEMultipart()
                msg['From'] = self.username or "no-reply@example.com"
                msg['To'] = to_email
                msg['Subject'] = subject
                msg.attach(MIMEText(body, 'plain'))

                # Send the email
                server.sendmail(msg['From'], to_email, msg.as_string())
                logger.info(f"Email sent to {to_email}")
                return {"status": "success", "message": f"Email sent to {to_email}"}
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return {"status": "error", "message": str(e)}

smtp_server = CustomSMTPServer(
    server_host=settings.SMTP_HOST,
    server_port=settings.SMTP_PORT,
    username=settings.SMTP_USERNAME,
    password=settings.SMTP_PASSWORD
)
