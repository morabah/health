from twilio.rest import Client
import os

# Twilio configuration
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

def send_verification_code(to_phone, code):
    message = client.messages.create(
        body=f"Your verification code is: {code}",
        from_=TWILIO_PHONE_NUMBER,
        to=to_phone
    )
    return message.sid
