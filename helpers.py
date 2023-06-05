import os
import requests
import urllib.parse
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import redirect, render_template, request, session
from functools import wraps
from cryptography.fernet import Fernet
import json
import openai

from models import db_session, User


def login_required(f):
    """
    Decorate routes to require login.
    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function


# Send email
def send_email(email, verification_code, username):
    # Load the key
    with open('key.key', 'rb') as key_file:
        key = key_file.read()

    fernet = Fernet(key)

    # Decrypt the configuration
    with open('config.enc', 'rb') as config_file:
        encrypted = config_file.read()

    decrypted = fernet.decrypt(encrypted)
    config = json.loads(decrypted.decode())

    # Get the email address and password from the environment variables
    EMAIL_ADDRESS_USER = config['email']
    EMAIL_PASSWORD_USER = config['password']

    # Construct the message
    message = MIMEMultipart("alternative")
    message["Subject"] = "Verification Code for Flask Final Project"
    message["From"] = EMAIL_ADDRESS_USER
    message["To"] = email

    # Create the HTML version of the message
    html = f"""
            <html>
                <head>
                    <meta charset="utf-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>PlanMate Verification Email</title>
                    <style>
                        /* Define some styles for the email */
                        body {{
                            background-color: #f2f2f2;
                            font-family: Arial, sans-serif;
                            font-size: 16px;
                            line-height: 1.5;
                            color: #333333;
                            margin: 0;
                            padding: 0;
                        }}

                        .container {{
                            max-width: 600px;
                            margin: 0 auto;
                            padding: 20px;
                            background-color: #ffffff;
                            border: 1px solid #d9d9d9;
                            border-radius: 5px;
                            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
                        }}

                        h1 {{
                            margin-top: 0;
                            margin-bottom: 20px;
                            font-size: 28px;
                            color: #007bff;
                        }}

                        h2 {{
                            margin-top: 0;
                            margin-bottom: 10px;
                            font-size: 24px;
                            color: #333333;
                        }}

                        p {{
                            margin-top: 0;
                            margin-bottom: 10px;
                            font-size: 16px;
                            color: #333333;
                        }}

                        .button {{
                            display: inline-block;
                            font-weight: bold;
                            text-align: center;
                            text-decoration: none;
                            background-color: #007bff;
                            color: #ffffff;
                            border-radius: 5px;
                            padding: 10px 20px;
                            transition: background-color 0.3s ease-in-out;
                        }}

                        .button:hover {{
                            background-color: #0056b3;
                        }}
                        
                        h2 {{
                            border: 1px solid #333333;
                            padding: 10px;
                            margin: 10px;
                        }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>Verification Code for PlanMate</h1>
                        <p>Dear {username},</p>
                        <p>Please use the following verification code to complete your registration:</p>
                        <h2>{verification_code}</h2>
                        <p>If you did not request this verification code, please ignore this email.</p>
                        <p>Thank you for using our service!</p>
                        <p>Best regards,</p>
                        <p>The PlanMate Team</p>
                        <p><a href="#" class="button">Verify Now &rarr;</a></p>
                    </div>
                </body>
            </html>
        """

    # Convert the HTML message into a MIME object
    html_part = MIMEText(html, "html")

    # Add both parts (text/plain and text/html) to the message
    message.attach(html_part)

    # Connect to the SMTP server and send the email
    with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
        smtp.starttls()
        smtp.login(EMAIL_ADDRESS_USER, EMAIL_PASSWORD_USER)
        smtp.sendmail(EMAIL_ADDRESS_USER, email, message.as_string())


# is logged in
def is_logged_in():
    user_id = session.get('user_id')
    if user_id is None:
        return False

    user = db_session.query(User).filter_by(user_id=user_id).first()
    return user is not None


def generate_event_invitation(event_name, event_date, event_time, event_location, event_organizer):
    # Create the HTML version of the message, message should be as generic as possible to be used for all events
    # Also need to add the event name, date, time, location, and organizer

    html = f"""
            <html>
                <head>
                    <meta charset="utf-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>PlanMate Event Invitation</title>
                    <style>
                        /* Define some styles for the email */
                        body {{
                            background-color: #f2f2f2;
                            font-family: Arial, sans-serif;
                            font-size: 16px;
                            line-height: 1.5;
                            color: #333333;
                            margin: 0;
                            padding: 0;
                        }}
                        
                        .container {{
                            max-width: 600px;
                            margin: 0 auto;
                            padding: 20px;
                            background-color: #ffffff;
                            border: 1px solid #d9d9d9;
                            border-radius: 5px;
                            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
                        }}
                        
                        h1 {{
                            margin-top: 0;
                            margin-bottom: 20px;
                            font-size: 28px;
                            color: #007bff;
                        }}
                        
                        h2 {{
                            margin-top: 0;
                            margin-bottom: 10px;
                            font-size: 24px;
                            color: #333333;
                        }}
                        
                        p {{
                            margin-top: 0;
                            margin-bottom: 10px;
                            font-size: 16px;
                            color: #333333;
                        }}
                        
                        .button {{
                            display: inline-block;
                            font-weight: bold;
                            text-align: center;
                            text-decoration: none;
                            background-color: #007bff;
                            color: #ffffff;
                            border-radius: 5px;
                            padding: 10px 20px;
                            transition: background-color 0.3s ease-in-out;
                        }}
                        
                        .button:hover {{
                            background-color: #0056b3;
                        }}
                        
                        h2 {{   
                            border: 1px solid #333333;
                            padding: 10px;
                            margin: 10px;
                        }}
                    </style>
                </head>
                
                <body>
                    <div class="container">
                        <h1>Event Invitation from PlanMate</h1>
                        <p>Dear INVITEE,</p>
                        <p>You have been invited to the following event:</p>
                        <h2>{event_name}</h2>
                        <p>Event Date: {event_date}</p>
                        <p>Event Time: {event_time}</p>
                        <p>Event Location: {event_location}</p>
                        <p>Event Organizer: {event_organizer}</p>
                        <p>Thank you for using our service!</p>
                        <p>Best regards,</p>
                        <p>The PlanMate Team</p>
                        <p><a href="#" class="button">View Event &rarr;</a></p>
                    </div>
                </body>
            </html>
        """

    return html


def send_invitations_func(guests, invitation):
    # Load the key
    with open('key.key', 'rb') as key_file:
        key = key_file.read()

    fernet = Fernet(key)

    # Decrypt the configuration
    with open('config.enc', 'rb') as config_file:
        encrypted = config_file.read()

    decrypted = fernet.decrypt(encrypted)
    config = json.loads(decrypted.decode())

    # Get the email address and password from the config
    EMAIL_ADDRESS_USER = config['email']
    EMAIL_PASSWORD_USER = config['password']

    # Create the base text message
    message = MIMEMultipart("alternative")
    message["Subject"] = "PlanMate Event Invitation"
    message["From"] = EMAIL_ADDRESS_USER

    # Use the html message passed in as a parameter
    html = invitation

    # Convert the HTML message into a MIME object
    html_part = MIMEText(html, "html")

    # Add both parts (text/plain and text/html) to the message
    message.attach(html_part)

    # Connect to the SMTP server and send the email to each guest
    with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
        smtp.starttls()
        smtp.login(EMAIL_ADDRESS_USER, EMAIL_PASSWORD_USER)
        for guest in guests:
            smtp.sendmail(EMAIL_ADDRESS_USER, guest.guest_email, message.as_string())

    return True

