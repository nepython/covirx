import uuid

from django.contrib.auth.models import (
    AbstractBaseUser, BaseUserManager, PermissionsMixin
)
from django.db import models
from django.urls import resolve
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import now

from .utils import tzinfo, INVITE_EXPIRY


def storage_path(instance, filename):
    """ file will be uploaded to MEDIA_ROOT/profile-pic/<datetime>-<filename> """
    return f'profile-pic/{datetime.now()}-{filename}'


class UserManager(BaseUserManager):
    def create_user(
            self, email, first_name, last_name, password=None,
            commit=True):
        """
        Creates and saves a User with the given email, first name, last name
        and password.
        """
        if not email:
            raise ValueError(_('Users must have an email address'))
        if not first_name:
            raise ValueError(_('Users must have a first name'))
        if not last_name:
            raise ValueError(_('Users must have a last name'))

        user = self.model(
            email=self.normalize_email(email),
            first_name=first_name,
            last_name=last_name,
        )

        user.set_password(password)
        if commit:
            user.save(using=self._db)
        return user

    def create_superuser(self, email, first_name, last_name, password):
        """
        Creates and saves a superuser with the given email, first name,
        last name and password.
        """
        user = self.create_user(
            email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            commit=False,
        )
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(
        verbose_name=_('email address'), max_length=255, unique=True, primary_key=True,
    )
    # password field supplied by AbstractBaseUser
    # last_login field supplied by AbstractBaseUser
    first_name = models.CharField(_('first name'), max_length=30, blank=True)
    last_name = models.CharField(_('last name'), max_length=150, blank=True)
    description = models.CharField(_('Short Description'), max_length=150, blank=True)
    email_notifications = models.BooleanField(
        _('Email Notifications'),
        default=True,
        help_text=_(
            'Allows you to enable or disable email notifications that '
            'shall be sent out on every new contact form submission.'
        ),
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_(
            'Designates whether the user can log into this admin site.'
        ),
    )
    # is_superuser field provided by PermissionsMixin
    # groups field provided by PermissionsMixin
    # user_permissions field provided by PermissionsMixin

    date_joined = models.DateTimeField(
        _('date joined'), default=timezone.now
    )

    google_oauth_id = models.TextField(_('Google Token ID'), help_text=_('Used for social oauth'), default=None, blank=True, null=True)
    pic = models.TextField(_('Profile picture link'), default='https://randomuser.me/api/portraits/lego/2.jpg')

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def get_full_name(self):
        """
        Return the first_name plus the last_name, with a space in between.
        """
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def __str__(self):
        return '{} <{}>'.format(self.get_full_name(), self.email)

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    def should_change_password(self):
        return self.check_password(self.google_oauth_id[-20:])


class Invitee(models.Model):
    """
    Used to store the list of individuals who have been invited to the project but are still to accept the invite,
    """
    email = models.EmailField(
        verbose_name=_('email address'), max_length=255, unique=True, blank=False, null=False
    )
    sent_on = models.DateField(_('Invite was sent out on'), null=False, auto_now=True)
    admin_access = models.BooleanField('Admin Access', default=False)

    def __str__(self):
        return self.email

    @property
    def expired(self):
        return (now().date()-self.sent_on).days>INVITE_EXPIRY

    class Meta:
        verbose_name = "Invite"
        verbose_name_plural = "Invite Members"


class Visitor(models.Model):
    """
    Record of a user visiting the site on a given day.
    This is used for tracking and reporting - knowing the volume of visitors
    to the site, and being able to report on someone's interaction with the site.
    We record minimal info required to identify user sessions, plus changes in
    IP and device. This is useful in identifying suspicious activity (multiple
    logins from different locations).
    Also helpful in identifying support issues (as getting useful browser data
    out of users can be very difficult over live chat).
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, primary_key=True)
    timestamp = models.DateField(
        help_text="The time at which the first visit of the day was recorded",
        default=timezone.now,
    )
    session_key = models.CharField(help_text="Django session identifier", max_length=40)
    page_visited = models.CharField(help_text="URL", max_length=40)
    drug_overview = models.BooleanField(default=False)

    class Meta:
        unique_together = ('session_key', 'page_visited', 'timestamp')

    def __str__(self):
        return self.session_key

    @classmethod
    def record(cls, request, drug_overview=None):
        """ Record the visitor if he hasn't visited the page previously """
        if not request.session.exists(request.session.session_key):
            request.session.create()
        sk = request.session.session_key
        page = resolve(request.path_info).url_name
        if drug_overview:
            page = f'{page}/{drug_overview}'
        ts = now().date()
        try:
            visitor = cls(session_key=sk, page_visited=page, timestamp=ts, drug_overview=bool(drug_overview))
            visitor.save()
        except:
            pass
        return request

    @classmethod
    def page_visitors(cls):
        """ Returns a dictionary with day as key and visitor count as value page wise """
        pages = cls.objects.values_list('page_visited').distinct()
        visits = dict()
        visits = list(Visitor.objects.filter()
            .exclude(drug_overview=True)
            .extra(select={'day': 'date( timestamp )'})
            .values('day', 'page_visited')
            .order_by('timestamp')
            .annotate(visits=models.Count('timestamp'))
        )
        return visits

    @classmethod
    def site_visitors(cls):
        """ Returns a dictionary with day as key and visitor count as value """
        visits = list(cls.objects.filter()
            .extra(select={'day': 'date( timestamp )'}) #TODO: Take care of time zone
            #.annotate(day=models.functions.TruncDate('timestamp', tzinfo=tzinfo))
            .values('day')
            .annotate(visits=models.Count('session_key', distinct=True))
        )
        return visits









