"""
Scheduled task.
"""
import logging
from logging.handlers import TimedRotatingFileHandler
import time
import ssl
import smtplib
import os
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import requests
from requests.exceptions import ConnectTimeout
from requests.packages.urllib3.exceptions import InsecureRequestWarning


CONST_DEFAULT_TIMEOUT = 10
CONST_ENCODING = 'utf-8'

load_dotenv()

levels = {
    'critical': logging.CRITICAL,
    'error': logging.ERROR,
    'warn': logging.WARNING,
    'info': logging.INFO,
    'debug': logging.DEBUG
}
logger = logging.getLogger()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_output_handler = \
    TimedRotatingFileHandler(
        os.getenv('LOG_FILE', './task-scheduler.log'),
        when="midnight",
        encoding=CONST_ENCODING
    )
file_output_handler.setFormatter(formatter)
logger.addHandler(file_output_handler)
console_output_handler = logging.StreamHandler()
console_output_handler.setFormatter(formatter)
logger.addHandler(console_output_handler)
try:
    logger.setLevel(levels.get(os.getenv('LOG_LEVEL', 'info').lower()))
except KeyError:
    logger.setLevel(logging.INFO)


smtp_port = os.getenv('SMTP_SERVER_PORT')
smtp_server = os.getenv('SMTP_SERVER_ADDRESS')
sender_mail = os.getenv('SENDER_EMAIL')
sender_pw = os.getenv('SENDER_PASSWORD')
recipients = os.getenv('RECIPIENT_EMAIL').split(',')

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def send_alert_html(title: str, message="<b>Unspecified error</b>"):
    """
    Sends an alert with title and message. Body is sent as HTML.

    Args:
        title (str): The title of the message
        message (str): the actual message
    """
    try:
        date_str = datetime.now().strftime('%d %b %Y %H %M %Z')
        email_message = MIMEMultipart()
        email_message['From'] = sender_mail
        email_message['To'] = ", ".join(recipients)
        email_message['Subject'] = f'{title} - {date_str}'
        email_message.attach(MIMEText(message, "html"))
        email_string = email_message.as_string()
        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls(context=context)
            server.login(sender_mail, sender_pw)
            server.sendmail(sender_mail, recipients, email_string)
    except Exception as error:
        logger.error("Cannot send alert: %s", str(error))


def check_rainmachine():
    """
    Checks the RainMachine.
    Performs a login and then retrieves the diagnostics.
    """
    start_time = time.perf_counter()
    logger.info("RainMachine check running...")
    base_url = \
        f"https://{os.getenv('RM_HOST')}:{os.getenv('RM_PORT')}/api/4/"
    headers = {
        "Content-Type": "application/json"
    }
    auth_json = {
        "pwd": os.getenv('RM_PASSWORD'),
        "remember": False
    }
    try:
        response = requests.post(
            f"{base_url}auth/login",
            headers=headers,
            json=auth_json,
            verify=False,
            timeout=CONST_DEFAULT_TIMEOUT
        )

        if not response.ok:
            logger.error("Unable to login.")
            send_alert_html(
                "RainMachine connection problem",
                "<p>Unable to login</p>"
                "<p>RainMachine is likely offline</p>")
        else:
            logger.info("Authenticated successfully with RainMachine.")
            response = requests.get(
                f"{base_url}diag?access_token="
                f"{response.json()['access_token']}",
                headers=headers,
                verify=False,
                timeout=CONST_DEFAULT_TIMEOUT
            )

            if not response.ok:
                logger.error("Cannot get diagnostics.")
                send_alert_html(
                    "RainMachine connection problem",
                    "<p>Login was successful, but cannot get diagnostics</p>"
                    "<p>RainMachine likely not operating correctly</p>")
            else:
                logger.info("Diagnostics: %s", str(response.json()))
    except ConnectTimeout as error:
        logger.error("RainMachine is not online: %s", str(error))
        send_alert_html(
            "RainMachine is not online",
            "<p>RainMachine did not respond within the given timeout "
            "and is thus assumed to not be online.</p>"
            f"<p>Detailed error: {str(error)}</p>")
    except Exception as error:
        logger.error("Unexpected error checking Rainmachine: %s", str(error))
        send_alert_html(
            "RainMachine connection problem",
            "<p>An unexpected error occurred:</p>"
            f"<p>{str(error)}</p>")
    logger.info(
        "RainMachine check completed in "
        f"{time.perf_counter() - start_time:0.3f} seconds")


if __name__ == "__main__":
    logger.info("Running checks at %s", datetime.now())
    check_rainmachine()
