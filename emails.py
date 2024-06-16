from typing import List

import jwt
from fastapi import BackgroundTasks, UploadFile, File, Form, Depends, HTTPException, status

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig

from dotenv import dotenv_values
from pydantic import BaseModel, EmailStr

from models import User

config_credentials = dotenv_values('.env')

config = ConnectionConfig(
    MAIL_USERNAME=config_credentials['USERNAME'],
    MAIL_PASSWORD=config_credentials['PASSWORD'],
    MAIL_FROM=config_credentials['USERNAME'],
    MAIL_PORT=465,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)


async def send_email(email: List, instance: User):
    token_data = {
        'id': instance.id,
        'username': instance.username,
    }

    token = jwt.encode(token_data, config_credentials['SECRET'], algorithm='HS256')

    template = f"""
    <!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Account Verification</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
</head>
<body class="bg-gray-100">
    <div class="max-w-lg mx-auto my-10 bg-white p-8 rounded-lg shadow-lg">
        <!-- <div class="text-center mb-6">
            <img src="your-logo-url.png" alt="Company Logo" class="mx-auto w-24">
        </div> -->
        <div class="text-center">
            <h2 class="text-2xl font-semibold mb-4">Account Verification</h2>
            <p class="text-gray-700 mb-6">Thank you for registering with us. Please verify your email address by clicking the button below to complete your registration and unlock a seamless shopping experience.</p>
            <a href="{config_credentials['BASE_URL']}/verification/?token={token}" class="inline-block px-6 py-3 text-white bg-blue-500 rounded-lg shadow hover:bg-blue-600">Verify Email</a>
        </div>
        <div class="text-center mt-6 text-gray-600 text-sm">
            <p>If you did not create an account, please ignore this email.</p>
            <p>2024 The Bee Store. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
    """

    message = MessageSchema(
        subject='The Bee Store Account verification email',
        recipients=email,
        body=template,
        subtype='html'
    )

    fm = FastMail(config)
    await fm.send_message(message)
