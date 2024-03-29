#!/usr/bin/python3

import os
import sys
import smtplib
import sys
import time
from email.mime.text import MIMEText
from socket import gethostname
from subprocess import run, PIPE

# Needs to be a TLS protected SMTP server
EMAIL = "INSERT EMAIL HERE"
PASSWORD = "INSERT PASSWORD HERE"
SUBJECT_TEMPLATE = "Updates available in {hostname}"
MSG_TEMPLATE = """
At {time}, there are updates available in {hostname}.
{updates}
Login to {hostname} and run:
    # pacman -Su
To update the system.
"""

def from_env(var, type_converter=None):
    value = os.environ.get(var)
    if value is None:
        raise Exception(f"Environment variable {var} is required")
    if type_converter is not None:
        try:
            value = type_converter(value)
        except ValueError:
            raise Exception(f"Environment variable {var} value {value} is not valid")
    return value

def add_prefix(prefix, text):
    result = ""
    for line in text.splitlines():
        result += prefix + line + "\n"
    return result

def check_updates():
    run(["pacman", "--sync", "--downloadonly", "--sysupgrade", "--refresh", "--quiet"], stdout=PIPE)
    result = run(["pacman", "--query", "--upgrades"], stdout=PIPE, universal_newlines=True)

    packages = ""
    if result.stdout:
        packages += "\nOfficial repositories:\n"
        packages += add_prefix("\t* ", result.stdout)

    return packages

def send_email(email, password, subject, message):
    # Connect to SMTP server
    smtp_server = from_env("SMTP_SERVER")
    smtp_port = from_env("SMTP_PORT", int)
    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.ehlo()
    server.starttls()
    server.login(email, password)

    # Sender/Receiver should be the same e-mail
    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = email
    msg['To'] = email

    server.send_message(msg)
    server.quit()

def main():
    if os.geteuid() != 0:
        sys.exit("You need root privileges to run {}".format(sys.argv[0]))

    available_updates = check_updates()
    if available_updates:
        email = from_env("SMTP_EMAIL")
        password = from_env("SMTP_PASSWORD")
        print("Available updates, sending e-mail to {}".format(email))
        hostname = gethostname()
        send_email(email, password,
                   SUBJECT_TEMPLATE.format(hostname=hostname),
                   MSG_TEMPLATE.format(time=time.strftime("%c"),
                                       hostname=hostname,
                                       updates=available_updates)
                   )
    else:
        print("No available updates, not sending e-mail")

    sys.exit()

if __name__ == "__main__":
    main()
