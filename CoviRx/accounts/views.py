from datetime import timedelta
from threading import Thread

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import user_passes_test
from django.http import JsonResponse
from django.shortcuts import render, reverse
from django.template.loader import get_template
from django.utils.timezone import now
from google.oauth2 import id_token
from google.auth.transport import requests

from .models import User, Invitee
from .utils import INVITE_EXPIRY
from main.utils import sendmail


def auth(request):
    token = request.GET.get('id_token')
    idinfo = id_token.verify_oauth2_token(token, requests.Request(), settings.GOOGLE_CLIENT_ID)
    token = idinfo['sub']
    user_email = idinfo['email']
    user_email_verified = idinfo['email_verified']
    user_fname = idinfo['given_name']
    user_lname = idinfo['family_name']
    user_picture = idinfo['picture']
    msg = str()
    try:
        user = User.objects.get(email=user_email)
        if ((not user_email_verified) or (user.google_oauth_id and user.google_oauth_id != token)):
            msg = f'We cannot verify your email id {user_email}.'
        if user.google_oauth_id is None:
            user.google_oauth_id = token
            user.save()
    except: # User not present in db
        try: # Check if user has been sent an invite in past 7 days
            invites = Invitee.objects.filter(email=user_email, sent_on__gte=(now()-timedelta(INVITE_EXPIRY)).date())
            if (len(invites)==0):
                raise ValueError(f'No active invite was found for {user_email}.')
            user = User(
                email=user_email,
                first_name=user_fname,
                last_name=user_lname,
                google_oauth_id=token,
                is_superuser=invites[0].admin_access==2,
                is_staff=invites[0].admin_access>0,
                is_active=True,
                pic=user_picture)
            user.set_password(token[-20:])
            user.save()
            invites.delete()
        except ValueError:
            msg = (f'Sorry, your email id {user_email} does not have access to the admin panel.\n'
            'If you are associated with the project, please contact the website developers '
            'using the Contact form for the same.')
    if not msg:
        authenticate(request, email=user.email, password=user.password)
        login(request, user)
        if user.is_staff:
            if user.should_change_password:
                messages.info(request, 'Please change you password using the change password button.')
            return JsonResponse({'admin': reverse('admin:index')})
        else:
            return JsonResponse({'admin': reverse('home')})
    return JsonResponse({'msg': msg})


@user_passes_test(lambda u: u.is_staff, login_url='/login')
def invite_members(request):
    invitees = request.GET.get('members').split(';') if request.GET.get('members') else []
    if not invitees:
        return JsonResponse({})
    admin_access = int(request.GET.get('adminAccess', '0'))
    for invitee in invitees:
        Invitee(email=invitee, admin_access=admin_access).save()
    messages.info(request, f'{len(invitees)} users have been invited to the CoviRx.')
    html = get_template('mail_templates/invitation.html').render({
        'invited_by': request.user.get_full_name(),
        'login_link': request.build_absolute_uri(reverse('login')),
        'expiry': INVITE_EXPIRY,
        'admin_access': admin_access
    })
    if admin_access:
        subject = 'You have been invited to join CoviRx admin'
    else:
        subject = 'You have been invited to contribute drugs to CoviRx'
    log = f'Mail successfully sent to {len(invitees)} users for membership invitation'
    # async from the process so that the view gets returned post successful save
    Thread(target = sendmail, args = (html, subject, list(), invitees, log)).start()
    return JsonResponse({})
