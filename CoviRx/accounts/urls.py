from django.contrib import admin
from django.urls import path

from .views import *

urlpatterns = [
    path('api/social-auth', auth, name='social-auth'),
    path('api/invite-members', invite_members, name='invite-members'),
]
