"""
Scheduled task.
"""
import ssl
import smtplib
import os
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from rich.console import Console

load_dotenv()
console = Console()

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
        console.print(f"[b red]ERROR[/b red]: Cannot send alert: {str(error)}")

def check_rainmachine():
    """
    Checks the RainMachine.
    Performs a login and then retrieves the diagnostics.
    """
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
            verify=False
        )

        if not response.ok:
            console.print("[b red]ERROR[/b red]: Unable to login.")
            send_alert_html(
                "RainMachine connection problem",
                "<p>Unable to login</p>"
                "<p>RainMachine is likely offline</p>")
        else:
            console.print("[b green]INFO [/b green]: Authenticated with RainMachine.")
            response = requests.get(
                f"{base_url}diag?access_token="
                f"{response.json()['access_token']}",
                headers=headers,
                verify=False
            )

            if not response.ok:
                console.print("[b red]ERROR[/b red]: Cannot get diagnostics.")
                send_alert_html(
                    "RainMachine connection problem",
                    "<p>Login was successful, but cannot get diagnostics</p>"
                    "<p>RainMachine likely offline</p>")
            else:
                console.print(f"[b green]INFO [/b green]: Diagnostics: {response.json()}")

    except Exception as error:
        console.print(f"[b red]ERROR[/b red]: {str(error)}")
        send_alert_html(
            "RainMachine connection problem",
            "<p>An unexpected error occurred:</p>"
            f"<p>{str(error)}</p>")

if __name__ == "__main__":
    console.print(f"[b green]INFO [/b green]: Running script at [b blue]{datetime.now()}")
    check_rainmachine()
