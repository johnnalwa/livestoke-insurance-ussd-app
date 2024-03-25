from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from .models import UserDetail, UserSession
import africastalking
import logging
from django.utils import timezone
from django.db.models import Count
from datetime import datetime, timedelta


logging.basicConfig(level=logging.ERROR)

# Set up Africa's Talking credentials
africastalking_username = "sidanApp"
africastalking_api_key = "4517d7cc71f90c18e234da01ecea9314c38830eed5d6a465f2de43012a914e2c"

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
            "id_number": None,
            "gender": None,
            "age": None,
        }
    return user_sessions[session_id]


def send_sms(phone_number, message):
    # Ensure phone number is in the correct format for Africa's Talking
    if not phone_number.startswith('+'):
        phone_number = '+' + phone_number

    try:
        response = sms.send(message, [phone_number])
        if response['SMSMessageData']['Recipients'][0]['status'] == 'Success':
            return True
        else:
            return False
    except Exception as e:
        # Log the error
        logging.error(f"Error sending SMS: {e}")
        return False


@csrf_exempt
def ussd_handler(request):
    response = ""  # Initialize response variable

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
                    response = "CON Welcome to Kenya Census System\nEnter your full name to register:"
                else:
                    response = "END Invalid option. Please try again."
            elif session.stage == "register_name":
                if text.strip():
                    session.name = user_response
                    session.stage = "register_id"
                    session.save()
                    response = "CON Enter your ID number:"
                else:
                    response = "END Please enter your name to register."
            elif session.stage == "register_id":
                if text.strip():
                    id_number = user_response
                    # Check if ID number already exists
                    if UserDetail.objects.filter(id_number=id_number).exists():
                        response = "END This ID number already exists. Please enter a different ID number."
                    else:
                        session.id_number = id_number
                        session.stage = "register_gender"
                        session.save()
                        response = "CON Enter your gender (M/F):"
                else:
                    response = "END Please enter your ID number."
            elif session.stage == "register_gender":
                if user_response.upper() in ["M", "F"]:
                    session.gender = user_response.upper()
                    session.stage = "register_age"
                    session.save()
                    response = "CON Enter your age:"
                else:
                    response = "END Invalid gender. Please enter 'M' for male or 'F' for female."
            elif session.stage == "register_age":
                try:
                    age = int(user_response)
                    if 0 < age < 150:  # Assuming reasonable age range
                        session.age = age
                        session.stage = "completed"
                        session.save()
                        # Save user details in the database
                        user_detail = UserDetail.objects.create(
                            phone_number=session.phone_number,
                            full_name=session.name,
                            id_number=session.id_number,
                            age=session.age,
                            gender=session.gender,
                            registration_date=timezone.now().date(),
                            registration_time=timezone.now().time()
                        )
                        # Send SMS when registration is completed successfully
                        sms_message = f"Thank you for registering with Kenya Census System. Your registration is now complete."
                        if send_sms(session.phone_number, sms_message):
                            response = "END Registration successful. Thank you! You will receive a confirmation SMS shortly."
                        else:
                            response = "END Failed to send confirmation SMS. Please contact support for assistance."
                    else:
                        response = "END Invalid age. Please enter a valid age."
                except ValueError:
                    response = "END Age must be a number. Please enter your age again."

        except Exception as e:
            response = "END An error occurred. Please try again later."

    return HttpResponse(response if response else "END Unknown error occurred.")




def dashboard(request):
    # Retrieve the count of all users
    total_users = UserDetail.objects.count()
    
    # Retrieve the count of male users
    male_users = UserDetail.objects.filter(gender='M').count()
    
    # Retrieve the count of female users
    female_users = UserDetail.objects.filter(gender='F').count()

    # Calculate daily counts of male and female users for the last 7 days
    today = datetime.now().date()
    last_week = today - timedelta(days=6)

        # Query to get daily counts of male users
    male_users_daily = UserDetail.objects.filter(gender='M', registration_date__range=(last_week, today)) \
                        .values('registration_date') \
                        .annotate(count=Count('pk'))

    # Query to get daily counts of female users
    female_users_daily = UserDetail.objects.filter(gender='F', registration_date__range=(last_week, today)) \
                        .values('registration_date') \
                        .annotate(count=Count('pk'))


    # Create dictionaries to store daily counts
    male_users_data = {entry['registration_date']: entry['count'] for entry in male_users_daily}
    female_users_data = {entry['registration_date']: entry['count'] for entry in female_users_daily}

    # Add any other necessary context data here
    context = {
        'total_users': total_users,
        'male_users': male_users,
        'female_users': female_users,
        'male_users_data': male_users_data,
        'female_users_data': female_users_data,
        # Add more context data if needed
    }
    
    return render(request, 'dashboard.html', context)