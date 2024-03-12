import requests
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from urllib.parse import parse_qs
import base64
import json
from datetime import datetime
import africastalking
from .models import UserSession, LivestockRegistration, Claim, Payment, Service

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


def send_stk_push(phone_number, amount):
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
        'AccountReference': 'CHARITY Platform',
        'TransactionDesc': 'charity'
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
        sms_message_stk_push = "Thanks {} Your donation of {} KES has been received.".format(amount)
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
                response = "CON Welcome to Charity Platform \nEnter your full name to register:"
            else:
                response = "END Invalid option. Please try again."
        elif session.stage == "register_name":
            if text.strip():
                session.name = user_response
                session.stage = "main_menu"
                session.save()
                response = (
                    "CON Hi {}, select type of charity you wish to take:\n"
                    "1. donate for poor\n"
                    "2. donate for disabled\n"
                    "3. donate for famine relief\n"
                    "4. donate for homeless\n"
                    "5. about us"
                ).format(user_response)
            else:
                response = "END Please enter your name to register."
        elif session.stage == "main_menu":
            if user_response in ["1", "2", "3", "4", "5"]:
                if user_response == "1":
                    if LivestockRegistration.objects.filter(session=session).exists():
                        response = "CON Choose an option:\n1. View Registered Livestock\n2. Register a New Livestock\n3. Return to Main Menu"
                    else:
                        session.stage = "register_location_name"
                        session.save()
                        response = "CON Register a new livestock...\nEnter your location and livestock name separated by comma (e.g., Location, Livestock Name):"
                elif user_response == "2":
                    session.stage = "report_case"
                    session.save()
                    response = "CON Report your case...\nEnter a brief description of your case:"
                elif user_response == "3":
                    session.stage = "claim"
                    session.save()
                    response = "CON Enter your claim description:"
                elif user_response == "4":
                    session.stage = "choose_charity"
                    session.save()
                    response = (
                        "CON Select charity for the homeless:\n"
                        "1. Red Cross\n"
                        "2. Habitat for Humanity"
                    )
                elif user_response == "5":
                    session.stage = "services"
                    session.save()
                    response = "CON Choose a service..."
            else:
                response = "END Invalid option. Please try again."
        elif session.stage == "choose_charity":
            if user_response in ["1", "2"]:
                if user_response == "1":
                    charity = "Red Cross"
                else:
                    charity = "Habitat for Humanity"
                session.charity = charity
                session.stage = "payment_amount"
                session.save()
                response = "CON You have selected {}. Enter the amount you wish to donate:".format(charity)
            else:
                response = "END Invalid option. Please choose a charity."
        elif session.stage == "payment_amount":
            user_response = user_response.strip()
            if user_response.isdigit():
                try:
                    payment_amount = int(user_response)
                    Payment.objects.create(session=session, amount=payment_amount)
                    # Simulate payment processing and generate STK push
                    stk_push_result = send_stk_push(session.phone_number, payment_amount)
                    response = "END Donation of {} KES initiated successfully.".format(payment_amount)
                except Exception as e:
                    response = "END Error: {}".format(e)
            else:
                response = "END Invalid amount. Please enter a valid numeric amount. Text received: '{}'".format(user_response)
        elif session.stage == "services":
            # Handle services logic
            # For example:
            Service.objects.create(session=session)
            session.stage = "main_menu"
            session.save()
            response = "CON Service chosen. Thank you!"
        elif session.stage == "report_case":
            if text.strip():
                Claim.objects.create(session=session, description=text)
                session.stage = "main_menu"
                session.save()
                response = "CON Case reported successfully. Thank you!\n1. Return to Main Menu"
            else:
                response = "END Please enter a brief description of your case."
        elif session.stage == "register_location_name":
            if text.strip():
                location, livestock_name = map(str.strip, text.split(','))
                LivestockRegistration.objects.create(session=session, location=location, livestock_name=livestock_name)
                session.stage = "choose_package"
                session.save()
                response = (
                    "CON Location and Livestock name registered successfully.\n"
                    "Choose a package:\n"
                    "1. Basic Insurance\n"
                    "2. Standard Insurance\n"
                    "3. Premium Insurance"
                )
            else:
                response = "END Please enter your location and livestock name separated by comma."
        elif session.stage == "choose_package":
            if user_response in ["1", "2", "3"]:
                package = {
                    "1": "Basic Insurance",
                    "2": "Standard Insurance",
                    "3": "Premium Insurance"
                }[user_response]
                session.package = package
                # Additional logic like calculating premiums, etc. can go here
                session.save()
                response = "END {} package selected. Thank you.".format(package)
            else:
                response = "END Invalid option. Please choose a package from the provided options."
        else:
            response = "END An error occurred. Please try again."

        return HttpResponse(response, content_type="text/plain")
    else:
        return HttpResponse("Method Not Allowed", status=405)