import requests
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from urllib.parse import parse_qs
import base64
import json
from datetime import datetime
import africastalking
from .models import UserSession, CharityOrganization

# Set up Africa's Talking credentials
africastalking_username = "devjnalwa"
africastalking_api_key = "64cf4b4482f4826835ab57e9dfe25102bcfe95c3efc5150d4ce49ac7ace1eab0"

# Initialize Africa's Talking SMS
africastalking.initialize(africastalking_username, africastalking_api_key)
sms = africastalking.SMS

# Placeholder for session storage
user_sessions = {}

def get_user_session(session_id, phone_number):
    if session_id not in user_sessions:
        user_sessions[session_id] = {
            "phone_number": phone_number,
            "stage": "welcome",
            "name": None,
            "case_description": None,
            "payment_amount": None,
            "donation_type": None,
            "selected_charity": None,
            "donation_method": None
        }
    return user_sessions[session_id]


def send_sms(phone_number, message):
    # Ensure phone number is in the correct format for Africa's Talking
    if not phone_number.startswith('+'):
        phone_number = '+' + phone_number
    
    try:
        response = sms.send(message, [phone_number])
        if response['SMSMessageData']['Recipients'][0]['status'] == 'Success':
            return 'SMS sent successfully.'
        else:
            return f'Failed to send SMS. Status: {response["SMSMessageData"]["Recipients"][0]["status"]}'
    except Exception as e:
        return f'Error: {str(e)}'
    
def send_donation_stk_push(phone_number, amount):
    # Remove "+" sign from the phone number if present
    phone_number = phone_number.replace('+', '')
    
    # Format phone number to include country code (254) and remove leading zeros
    if phone_number.startswith('0'):
        phone_number = '254' + phone_number[1:]
    elif not phone_number.startswith('254'):
        phone_number = '254' + phone_number
    
    # M-PESA Credentials
    consumerKey = '4C3mkwwnUaq8AsSZ6ig0lGzEVrfNuLO9'
    consumerSecret = 'T9vB9MUhf8hRKocz'
    BusinessShortCode = '174379'
    Passkey = 'bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919'
    
    Timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    Password = base64.b64encode((BusinessShortCode + Passkey + Timestamp).encode()).decode('utf-8')
    
    access_token_url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
    response = requests.get(access_token_url, auth=(consumerKey, consumerSecret))
    
    try:
        response_data = response.json()  # Parse JSON response
        if not response_data:  # If response_data is empty
            response_data = {"errorMessage": "Empty response from API"}
    except json.decoder.JSONDecodeError:
        response_data = {"errorMessage": "Invalid JSON response from API"}

    access_token = response_data.get("access_token")

    initiate_url = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    CallBackURL = 'https://7dab-102-140-203-238.ngrok-free.app'

    payload = {
        'BusinessShortCode': BusinessShortCode,
        'Password': Password,
        'Timestamp': Timestamp,
        'TransactionType': 'CustomerPayBillOnline',
        'Amount': amount,
        'PartyA': phone_number,
        'PartyB': BusinessShortCode,
        'PhoneNumber': phone_number,
        'CallBackURL': CallBackURL,
        'AccountReference': 'donation ',
        'TransactionDesc': ' donation'
    }

    response = requests.post(initiate_url, headers=headers, json=payload)
        
    try:
        response_data = response.json()  # Parse JSON response
        if not response_data:  # If response_data is empty
            response_data = {"errorMessage": "Empty response from API"}
    except json.decoder.JSONDecodeError:
        response_data = {"errorMessage": "Invalid JSON response from API"}

    if response.status_code == 200:
        success_message = response_data.get('ResponseDescription', 'Payment initiated successfully.')
        
        # After sending STK Push, send an SMS
        sms_message_stk_push = "Your payment of {} KES has been received. Thank you!".format(amount)
        sms_result_stk_push = send_sms(phone_number, sms_message_stk_push)
        
        # Additional message
        additional_message = "Thank you."
        sms_result_additional = send_sms(phone_number, additional_message)
        
        return success_message
    else:
        error_message = response_data.get('errorMessage', 'Failed to initiate payment.')
        # Include phone number in error message
        error_message_with_phone = f'{error_message} Phone Number: {phone_number}'
        return error_message_with_phone


@csrf_exempt
def ussd_handler(request):
    if request.method == 'POST':
        session_id = request.POST.get('sessionId', None)
        phone_number = request.POST.get('phoneNumber', None)
        text = request.POST.get('text', '')

        try:
            session = UserSession.objects.get(session_id=session_id)
        except UserSession.DoesNotExist:
            session = UserSession.objects.create(session_id=session_id, phone_number=phone_number, stage="welcome")

        text_array = text.split('*')
        user_response = text_array[-1]

        if session.stage == "welcome":
            if not text.strip():
                session.stage = "register_name"
                session.save()
                response = "CON Welcome to the Donation Platform\nEnter your full name to register:"
            else:
                response = "END Invalid option. Please try again."
        elif session.stage == "register_name":
            if text.strip():
                session.name = user_response
                session.stage = "donation_type"
                session.save()
                response = (
                    "CON Hi {}, choose the type of donation you'd like to make:\n"
                    "1. Charity for the Homeless\n"
                    "2. Charity for the Poor\n"
                    "3. Charity for the Disabled\n"
                    "4. Charity for Famine Relief\n"
                    "5. Other"
                ).format(user_response)
            else:
                response = "END Please enter your full name to register."
        elif session.stage == "donation_type":
            if user_response in ["1", "2", "3", "4", "5"]:
                donation_types = {
                    "1": "Charity for the Homeless",
                    "2": "Charity for the Poor",
                    "3": "Charity for the Disabled",
                    "4": "Charity for Famine Relief",
                    "5": "Other"
                }
                donation_type = donation_types[user_response]
                session.donation_type = donation_type
                session.stage = "charity_organization"
                session.save()
                
                # Fetch and display related charity organizations
                charity_organizations = CharityOrganization.objects.filter(donation_type=donation_type)
                response = "CON Choose a charity organization:\n"
                for i, charity in enumerate(charity_organizations, start=1):
                    response += f"{i}. {charity.name}\n"
            else:
                response = "END Invalid option. Please try again."

        elif session.stage == "charity_organization":
            # Assuming user_response is the index of the selected charity organization
            try:
                selected_charity_index = int(user_response)
                charity_organizations = CharityOrganization.objects.filter(donation_type=session.donation_type)
                selected_charity = charity_organizations[selected_charity_index - 1]

                session.selected_charity = selected_charity
                session.stage = "donation_method"
                session.save()
                response = "CON Choose a donation method:\n1. Cash Donation\n2. Physical Item Donation"
            except (ValueError, IndexError):
                response = "END Invalid option. Please try again."

        elif session.stage == "donation_method":
            if user_response == "1":
                session.donation_method = "Cash"
                session.stage = "enter_amount"
                session.save()
                response = "CON Enter the donation amount:"
            elif user_response == "2":
                session.donation_method = "Physical Item"
                # Add logic for handling physical item donation
                # (e.g., providing drop-off locations or scheduling pick-up)
                session.stage = "thank_you"
                session.save()
                response = "END Thank you for your physical item donation!"
            else:
                response = "END Invalid option. Please try again."

        elif session.stage == "enter_amount":
            user_response = user_response.strip()
            if user_response.isdigit():
                try:
                    donation_amount = int(user_response)
                    # Simulate donation processing and generate STK push
                    send_donation_stk_push(session.phone_number, donation_amount, session.selected_charity.name)
                    session.stage = "thank_you"
                    session.save()
                    response = "END Thank you for your donation of {} KES.".format(donation_amount)
                except Exception as e:
                    response = "END Error: {}".format(e)
            else:
                response = "END Invalid amount. Please enter a valid numeric amount."

        elif session.stage == "thank_you":
            response = "END Thank you for your donation!"

        else:
            response = "END An error occurred. Please try again."

        return HttpResponse(response, content_type="text/plain")
    else:
        return HttpResponse("Method Not Allowed", status=405)