import smtplib
import os
from dotenv import load_dotenv
from email.message import EmailMessage

load_dotenv()
EMAIL_ADDRESS = os.getenv('FIRST_EMAIL')
EMAIL_PASSWORD = os.getenv('SECRET_KEY')


def contact_message(name, sender, email, user, calendar_invite, message, email_password):
    msg = EmailMessage()
    msg['Subject'] = f'{name} has requested for an appointment with you.'
    msg['From'] = sender
    msg['To'] = email
    msg.set_content(f"Message: {message}\n\n\nReply to the student via his/her mail here: {user}\n\n\nBelow is the "
                    f"calendar invite: \n\n\n {calendar_invite}")
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(sender, email_password)
        smtp.send_message(msg)


def cancel_message(name, sender, email, message, email_password):
    msg = EmailMessage()
    msg['Subject'] = f'{name} has cancelled an appointment with you.'
    msg['From'] = sender
    msg['To'] = email
    msg.set_content(f"Message: {message}\n\n\nCheck your calendar for confirmation!")
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(sender, email_password)
        smtp.send_message(msg)


class Email:
    def __init__(self, user, name):
        name = name.split(' ')[0]
        msg = EmailMessage()
        msg['Subject'] = f'{name} has requested for an appointment with you.'
        msg['From'] = EMAIL_ADDRESS
        msg.set_content('''
                    <!DOCTYPE html>
                    <html lang="en">
                    <head>
                        <meta charset="UTF-8">
                        <meta name="viewport" content="width=device-width, initial-scale=1.0">
                        <style>
                            /* Add your custom CSS styles here */
                            body {
                                font-family: Arial, sans-serif;
                                background-color: #f7f7f7;
                                margin: 0;
                                padding: 0;
                                text-align: center;
                            }

                            .container {
                                max-width: 600px;
                                margin: 0 auto;
                                padding: 20px;
                                background-color: #fff;
                                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                                border-radius: 5px;
                            }

                            .header {
                                background-color: #333;
                                color: #fff;
                                text-align: center;
                                padding: 20px 0;
                            }

                            h1 {
                                color: #fff;
                                font-size: 24px;
                                margin-top: 10px;
                            }

                            p {
                                color: #666;
                                font-size: 16px;
                                line-height: 1.5;
                            }

                            .cta-button {
                                display: inline-block;
                                background-color: #000;
                                color: #fff;
                                font-size: 18px;
                                padding: 10px 20px;
                                text-decoration: none;
                                border-radius: 5px;
                            }
                        </style>
                    </head>
                    <body>
                        <div style="text-align: center;" class="container">
                            <div class="header">
                                <h1>Welcome to Fisk University!</h1>
                            </div>
                            <p style="text-align: center;">Thank you for joining our university community. We're thrilled to have you as a member.</p>
                            <p style="text-align: center;">Explore our course collection and make swift appointments with tutors</p>
                            <p style="text-align: center;">Stay tuned for the latest courses and updates.</p>
                            <a style="text-align: center;" href="https://www.yourwebsite.com/contacts" class="cta-button">Make an appointment now</a>
                            <footer style="margin-top: 20px;">
                                <hr style="top: 10px; border: none; height: 1px; background-color: grey;">
                                <p style="text-align: center; margin-top: 25px; font-size: 12px; font-style: italic;">© Copyright 2023 FISK UNIVERSITY. All rights reserved.</p>
                                <p style="text-align: center; padding-top: 20px; font-size: 10px;">Want to change how you recieve these emails?</p>
                                <p style="text-align: center; font-size: 12px;">You can <a href='https://www.google.com/'>update your preferences</a> or <a href='https://www.google.com/'>unsubscribe</a>.</p>

                            </footer>
                        </div>
                    </body>
                    </html>
                ''', subtype='html')
        msg['To'] = user
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)


class EmailTeacher:
    def __init__(self, user, name):
        name = name.split(' ')[0]
        msg = EmailMessage()
        msg['Subject'] = f'{name} has requested for an appointment with you.'
        msg['From'] = EMAIL_ADDRESS
        msg.set_content('''
                    <!DOCTYPE html>
                    <html lang="en">
                    <head>
                        <meta charset="UTF-8">
                        <meta name="viewport" content="width=device-width, initial-scale=1.0">
                        <style>
                            /* Add your custom CSS styles here */
                            body {
                                font-family: Arial, sans-serif;
                                background-color: #f7f7f7;
                                margin: 0;
                                padding: 0;
                                text-align: center;
                            }

                            .container {
                                max-width: 600px;
                                margin: 0 auto;
                                padding: 20px;
                                background-color: #fff;
                                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                                border-radius: 5px;
                            }

                            .header {
                                background-color: #333;
                                color: #fff;
                                text-align: center;
                                padding: 20px 0;
                            }

                            h1 {
                                color: #fff;
                                font-size: 24px;
                                margin-top: 10px;
                            }

                            p {
                                color: #666;
                                font-size: 16px;
                                line-height: 1.5;
                            }

                            .cta-button {
                                display: inline-block;
                                background-color: #000;
                                color: #fff;
                                font-size: 18px;
                                padding: 10px 20px;
                                text-decoration: none;
                                border-radius: 5px;
                            }
                        </style>
                    </head>
                    <body>
                        <div style="text-align: center;" class="container">
                            <div class="header">
                                <h1>Welcome to Fisk University!</h1>
                            </div>
                            <p style="text-align: center;">Thank you for joining our university community. We're thrilled to have you as a member.</p>
                            <p style="text-align: center;">Explore our course collection and make swift appointments with tutors</p>
                            <p style="text-align: center;">Stay tuned for the latest courses and updates.</p>
                            <a style="text-align: center;" href="https://www.yourwebsite.com/contacts" class="cta-button">Make an appointment now</a>
                            <footer style="margin-top: 20px;">
                                <hr style="top: 10px; border: none; height: 1px; background-color: grey;">
                                <p style="text-align: center; margin-top: 25px; font-size: 12px; font-style: italic;">© Copyright 2023 FISK UNIVERSITY. All rights reserved.</p>
                                <p style="text-align: center; padding-top: 20px; font-size: 10px;">Want to change how you recieve these emails?</p>
                                <p style="text-align: center; font-size: 12px;">You can <a href='https://www.google.com/'>update your preferences</a> or <a href='https://www.google.com/'>unsubscribe</a>.</p>

                            </footer>
                        </div>
                    </body>
                    </html>
                ''', subtype='html')
        msg['To'] = user
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
