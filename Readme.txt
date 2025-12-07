# Virtual BACnet Temperature Sensor with SMS/Email Alerts

This project is a **virtual BACnet temperature sensor** implemented in Python. It simulates a temperature sensor, listens for BACnet alarms, logs them, and sends SMS and email notifications.

---

## Features

- Periodic temperature updates every 5 seconds - This is more to confirm that the script is running anyone on a supervisor can check this way that a temperature is readable and changing.
- Listens for incoming BACnet alarms/events
- Prints `lastUpdate` and `messageText` of alarms
- Logs alarms to `alarm_log.csv`
- Sends SMS via Teltonika RUT956
- Sends email notifications via SMTP
- Rate-limits alerts to avoid spamming
- Supports multiple recipients

---

## Setup

1. Clone the repository:

git clone <your-repo-url>
cd <your-repo-folder>

2. Create a virtual environment:
python -m venv .venv

3. Activate the virtual environment:
.venv\Scripts\activate

4. Install dependencies:
pip install -r requirements.txt

Make sure requests and bacpypes are installed.

5. Configuration

Edit the following variables in your script to match your network and recipients:

APPLICATION_IP and APPLICATION_PORT – your BACnet IP and port
TELTONIKA_IP and TELTONIKA_AUTH – your Teltonika RUT956 router credentials
SMS_RECIPIENTS – phone numbers for SMS notifications
SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, EMAIL_RECIPIENTS – for email notifications
ALERT_INTERVAL – rate-limiting interval in seconds

Logging

All alarms are logged to alarm_log.csv with the following columns:

Timestamp, LastUpdate, Message
