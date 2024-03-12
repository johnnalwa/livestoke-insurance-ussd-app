from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from urllib.parse import parse_qs
from django.shortcuts import render, redirect
import base64
import json
from datetime import datetime
import africastalking
from .models import UserSession, Charity, Donation
import logging
import requests

logging.basicConfig(level=logging.ERROR)

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
        'AccountReference': 'Donation Platform',
        'TransactionDesc': 'charity {}',
    }

    response = requests.post(initiate_url, headers=headers, json=payload)
        
    try:
        response_data = response.json()  # Parse JSON response
        if not response_data:  # If response_data is empty
            response_data = {"errorMessage": "Empty response from API"}
    except json.decoder.JSONDecodeError:
        response_data = {"errorMessage": "Invalid JSON response from API"}

    if response.status_code == 200:
        # Check if the API response indicates success
        if response_data.get('errorCode') == '0':
            success_message = response_data.get('ResponseDescription', 'Donation has been initiated successfully.')
            # After sending STK Push, send an SMS
            sms_message_stk_push = f"Thanks! Your donation of {amount} KES has been received."
            sms_result_stk_push = send_sms(phone_number, sms_message_stk_push)
            # Additional message
            additional_message = "Thank you."
            sms_result_additional = send_sms(phone_number, additional_message)
            return success_message
        else:
            # Log the error
            logging.error(f"Failed to initiate STK push. Error: {response_data}")
            # Handle API error
            error_message = response_data.get('errorMessage', 'Failed to initiate payment.')
            # Include phone number in error message
            error_message_with_phone = f'{error_message} Phone Number: {phone_number}'
            return error_message_with_phone
    else:
        # Log the error
        logging.error(f"HTTP Error: {response.status_code}")
        # Handle HTTP error
        error_message = f'HTTP Error: {response.status_code}'
        # Include phone number in error message
        error_message_with_phone = f'{error_message} Phone Number: {phone_number}'
        return error_message_with_phone

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
        # Log the error
        logging.error(f"Error sending SMS: {e}")
        return f'Error: {str(e)}'

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

        try:
            if session.stage == "welcome":
                if not text.strip():
                    session.stage = "register_name"
                    session.save()
                    response = "CON Welcome to Donation Platform \nEnter your full name to register:"
                else:
                    response = "END Invalid option. Please try again."
            elif session.stage == "register_name":
                if text.strip():
                    session.name = user_response
                    session.stage = "main_menu"
                    session.save()
                    response = (
                        "CON Hi {}, select type of charity you wish to donate to:\n"
                        "1. Charity for the Poor\n"
                        "2. Charity for the Disabled\n"
                        "3. Charity for Famine Relief\n"
                        "4. Charity for the Homeless\n"
                        "5. About Us"
                    ).format(user_response)
                else:
                    response = "END Please enter your name to register."
            elif session.stage == "main_menu":
                if user_response in ["1", "2", "3", "4", "5"]:
                    if user_response == "1":
                        session.stage = "choose_charity"
                        session.save()
                        response = (
                            "CON Select charity for the Poor:\n"
                            "1. Oxfam\n"
                            "2. World Vision\n"
                            "3. Save the Children"
                        )
                    elif user_response == "2":
                        session.stage = "choose_charity"
                        session.save()
                        response = (
                            "CON Select charity for the Disabled:\n"
                            "1. Special Olympics\n"
                            "2. Disabled American Veterans\n"
                            "3. Ability First"
                        )
                    elif user_response == "3":
                        session.stage = "choose_charity"
                        session.save()
                        response = (
                            "CON Select charity for Famine Relief:\n"
                            "1. UNICEF\n"
                            "2. World Food Programme\n"
                            "3. Action Against Hunger"
                        )
                    elif user_response == "4":
                        session.stage = "choose_charity"
                        session.save()
                        response = (
                            "CON Select charity for the Homeless:\n"
                            "1. Red Cross\n"
                            "2. Habitat for Humanity"
                        )
                    elif user_response == "5":
                        session.stage = "about_us"
                        session.save()
                        response = "END Charity Platform provides support to various charitable causes. Thank you for your interest!"
                else:
                    response = "END Invalid option. Please try again."
            elif session.stage == "choose_charity":
                if user_response in ["1", "2", "3"]:
                    if user_response == "1":
                        charity_name = "Oxfam"
                    elif user_response == "2":
                        charity_name = "World Vision"
                    else:
                        charity_name = "Save the Children"
                    charity = Charity.objects.get_or_create(name=charity_name)[0]
                    session.charity = charity_name
                    session.stage = "donation_method"
                    session.save()
                    response = "CON You have selected {}. Enter the donation method:\n1. Cash Donation\n2. Physical Item Donation".format(charity_name)
                else:
                    response = "END Invalid option. Please choose a charity."
            elif session.stage == "donation_method":
                if user_response == "1":
                    session.donation_method = "Cash"
                    session.stage = "enter_amount"
                    session.save()
                    response = "CON Enter the donation amount in KES:"
                elif user_response == "2":
                    session.donation_method = "Physical Item"
                    session.stage = "physical_item_details"
                    session.save()
                    response = "CON Please provide details about the physical item you wish to donate:"
                else:
                    response = "END Invalid option. Please try again."
            elif session.stage == "enter_amount":
                user_response = user_response.strip()
                if user_response.isdigit():
                    try:
                        donation_amount = int(user_response)
                        session.donation_amount = donation_amount
                        # Ensure donation method is set before creating Donation object
                        if session.donation_method:
                            # Process donation (simulate for now)
                            process_donation(session)
                            Donation.objects.create(session=session, charity=charity, donation_method=session.donation_method, donation_amount=session.donation_amount)
                            response = "END Thank you for your donation of {} KES to {}.".format(donation_amount, session.charity)
                        else:
                            response = "END Donation method is missing. Please select a valid donation method."
                    except Exception as e:
                        logging.error("Error processing donation: %s", e)
                        response = "END processing your donation. you will receive a prompt shortly."
                else:
                    response = "END Invalid amount. Please enter a valid numeric amount."
            elif session.stage == "physical_item_details":
                # Process physical item donation (simulate for now)
                process_physical_item_donation(session, user_response)
                response = "END Thank you for your physical item donation to {}.".format(session.charity)
            else:
                response = "END An error occurred. Please try again."

        except Exception as e:
            logging.error("An error occurred: %s", e)
            response = "END An unexpected error occurred. Please try again later."

        return HttpResponse(response, content_type="text/plain")
    else:
        return HttpResponse("Method Not Allowed", status=405)


def process_donation(session):
    phone_number = session.phone_number
    amount = session.donation_amount
    send_stk_push(phone_number, amount)
    logging.info("Donation processed successfully.")


def process_physical_item_donation(session, item_details):

    logging.info("Physical item donation processed successfully.")


def dashboard(request):
    return render(request, 'dashboard.html')
