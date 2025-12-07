"""
Virtual BACnet Temperature Sensor with Alarm Listener, SMS, Email, Logging, and Rate-Limiting
BACPypes 0.19.0 compatible
"""

import random
import threading
from threading import Thread
import smtplib
from email.mime.text import MIMEText
import csv
import time
from datetime import datetime

from bacpypes.core import run, stop, deferred
from bacpypes.local.device import LocalDeviceObject
from bacpypes.pdu import Address
from bacpypes.object import AnalogValueObject
from bacpypes.app import BIPSimpleApplication
from bacpypes.service.device import WhoIsIAmServices
from bacpypes.apdu import ConfirmedEventNotificationRequest

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
APPLICATION_IP = "192.168.0.18/24"
APPLICATION_PORT = 47808

# Teltonika RUT956
TELTONIKA_IP = "192.168.0.1"  # RUT956 IP
TELTONIKA_AUTH = ('admin', 'password')  # Replace with your credentials
SMS_RECIPIENTS = ["+61412345678", "+61498765432"]

# Email
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "your_email@gmail.com"
SMTP_PASSWORD = "your_app_password"
EMAIL_RECIPIENTS = ["recipient1@example.com", "recipient2@example.com"]

# Rate limiting in seconds (minimum interval between alerts)
ALERT_INTERVAL = 300  # 5 minutes

# CSV Log File
ALARM_LOG_FILE = "alarm_log.csv"

# Track last alert timestamp to implement rate limiting
last_alert_time = 0

# -----------------------------------------------------------------------------
# Helper: Schedule functions after a delay
# -----------------------------------------------------------------------------
def schedule_after(delay_seconds, fn):
    """Schedules fn to run after delay_seconds inside BACpypes core loop."""
    def wrapper():
        deferred(fn)
    threading.Timer(delay_seconds, wrapper).start()

# -----------------------------------------------------------------------------
# Alarm Logging
# -----------------------------------------------------------------------------
def log_alarm(last_update, message):
    """Append alarm to CSV file"""
    try:
        with open(ALARM_LOG_FILE, mode='a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([datetime.now(), last_update, message])
    except Exception as e:
        print(f"[ERROR] Failed to log alarm: {e}")

# -----------------------------------------------------------------------------
# SMS via Teltonika RUT956
# -----------------------------------------------------------------------------
def send_sms_via_teltonika(number: str, message: str):
    try:
        url = f"http://{TELTONIKA_IP}/api/sms/send"
        payload = {"number": number, "message": message}
        response = requests.post(url, json=payload, auth=TELTONIKA_AUTH)
        if response.status_code == 200:
            print(f"SMS sent to {number}")
        else:
            print(f"[ERROR] Failed to send SMS: {response.status_code} {response.text}")
    except Exception as e:
        print(f"[ERROR] SMS send failed: {e}")

# -----------------------------------------------------------------------------
# Email notification
# -----------------------------------------------------------------------------
def send_email_alert(subject: str, message: str, recipients: list):
    try:
        msg = MIMEText(message)
        msg['Subject'] = subject
        msg['From'] = SMTP_USER
        msg['To'] = ", ".join(recipients)

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, recipients, msg.as_string())
        server.quit()
        print(f"Email sent to {recipients}")
    except Exception as e:
        print(f"[ERROR] Email send failed: {e}")

# -----------------------------------------------------------------------------
# Alarm Listener Application
# -----------------------------------------------------------------------------
class AlarmListenerApplication(BIPSimpleApplication):
    def confirmedEventNotificationRequest(self, apdu: ConfirmedEventNotificationRequest):
        """Handle incoming BACnet alarm/event notifications"""
        global last_alert_time
        try:
            last_update = getattr(apdu, "timeStamp", None)
            message = getattr(apdu, "messageText", None)
            print(f"ALARM RECEIVED! LastUpdate: {last_update}, Message: {message}")

            # Log the alarm
            log_alarm(last_update, message)

            # Rate-limiting
            current_time = time.time()
            if current_time - last_alert_time >= ALERT_INTERVAL:
                last_alert_time = current_time

                # Send SMS
                for number in SMS_RECIPIENTS:
                    Thread(target=send_sms_via_teltonika, args=(number, message)).start()

                # Send Email
                Thread(target=send_email_alert, args=("BACnet Alarm", message, EMAIL_RECIPIENTS)).start()
            else:
                print(f"[INFO] Alert suppressed due to rate limiting. Next alert allowed in {int(ALERT_INTERVAL - (current_time - last_alert_time))}s")

        except Exception as e:
            print(f"[ERROR] processing alarm: {e}")

# -----------------------------------------------------------------------------
# BACnet Device Definition
# -----------------------------------------------------------------------------
this_device = LocalDeviceObject(
    objectName="VirtualTemperatureSensor",
    objectIdentifier=1234,
    maxApduLengthAccepted=1024,
    segmentationSupported="noSegmentation",
    vendorIdentifier=15,
)

# -----------------------------------------------------------------------------
# Create BACnet/IP Application
# -----------------------------------------------------------------------------
this_application = AlarmListenerApplication(
    this_device,
    Address(f"{APPLICATION_IP}:{APPLICATION_PORT}")
)

# Enable Who-Is/I-Am services
this_application.add_capability(WhoIsIAmServices)

# -----------------------------------------------------------------------------
# Alarm-capable Analog Value Object
# -----------------------------------------------------------------------------
temperature_sensor = AnalogValueObject(
    objectIdentifier=("analogValue", 1),
    objectName="TemperatureSensor1",
    presentValue=22.0,
    units="degreesCelsius",

    # Niagara-compatible alarm properties
    highLimit=30.0,
    lowLimit=10.0,
    deadband=0.5,
    limitEnable="highLimitEnable,lowLimitEnable",
    timeDelay=1,
    notifyType="alarm"
)

this_application.add_object(temperature_sensor)

# -----------------------------------------------------------------------------
# Periodic Temperature Update
# -----------------------------------------------------------------------------
def update_temperature():
    """Simulate temperature changes and update BACnet object"""
    try:
        new_temp = round(random.uniform(20.0, 25.0), 2)
        temperature_sensor.presentValue = new_temp
        print(f"Updated Temperature: {new_temp} °C")
    except Exception as e:
        print(f"[ERROR] Temperature update failed: {e}")

    # Schedule next update in 5 seconds
    schedule_after(5, update_temperature)

# -----------------------------------------------------------------------------
# Main Function
# -----------------------------------------------------------------------------
def main():
    print("Starting Virtual BACnet Temperature Sensor with Alarm Listener, SMS, Email, Logging, and Rate-Limiting")
    print(f"Listening on {APPLICATION_IP}:{APPLICATION_PORT}")

    # Schedule the first temperature update
    schedule_after(1, update_temperature)

    try:
        run()  # Enter BACpypes event loop
    except KeyboardInterrupt:
        print("\nShutting down...")
        stop()

# -----------------------------------------------------------------------------
if __name__ == "__main__":
    main()
