import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from decouple import config
import logging

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

    def send_email(self, to_email, subject, body):
        try:
            # Set up the server connection
            with smtplib.SMTP(self.server_host, self.server_port) as server:
                server.starttls()  # Enable encryption if using port 587
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


# Initialize the SMTP server using environment variables
smtp_server = CustomSMTPServer(
    config("SMTP_HOST", default="localhost"),
    config("SMTP_PORT", default=25, cast=int),
    config("SMTP_USERNAME", default=None),
    config("SMTP_PASSWORD", default=None),
)