"""CoviRx URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path('', include('main.urls')),
    path('login/', auth_views.LoginView.as_view(template_name='main/login.html'),name='login'),
    path('logout', auth_views.LogoutView.as_view(template_name='main/logout.html'),name='logout'),
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),
]
# Needed for django-admin-interface
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.index_title  =  "Welcome to the Admin Panel"
