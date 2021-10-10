from collections import OrderedDict
import logging

from django.conf import settings
from django.core.mail import EmailMessage
from premailer import transform

from .models import Drug

# Fields to be used to search on home page
search_fields = ['name', 'smiles', 'inchi', 'synonyms', 'cas', 'chebl', 'pubchem']

# Fields which have been name differently in excel sheet and in our Drug model
# It should be in lowercase with spaces replaced by underscore
verbose_names = {
    'indication': 'indication_class'
}

# Fields that need to be stored during a bulk drug upload
ignore_fields = ['id'] + list(verbose_names.values())
store_fields = [f.name for f in Drug._meta.get_fields() if f.name not in ignore_fields]

# Dictionary contains the list of all invalidated drugs during drug upload
invalid_drugs = OrderedDict()


def sendmail(html, subject, recepients, bcc=list(), log=None):
    """
    Utility function to send emails. Currently being used for:-
    1) Contact form emails
    2) Sharing invalid drugs during drug upload
    3) Inviting members to the admin panel
    Args:
        html (string/template): Pass on the html template which needs to be sent as message
        subject (string): Subject of the email
        recepients (list): The individuals who need to be sent email
        bcc ([list], optional): If any individuals need to be sent email without them finding
                                out any other member in the mailing list.
        log ([string], optional): If anything needs to be logged on successful email,
                                  can be passed here.
    """
    message = transform(
        html,
        allow_insecure_ssl=True,
        disable_leftover_css=True,
        strip_important=False,
        disable_validation=True,
    )
    msg = EmailMessage(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        recepients,
    )
    msg.content_subtype = "html"
    if recepients:
        msg.send(fail_silently=False)
    if bcc: # Useful to send emails when we don't want recipient to know others in email list
        msg.to = []
        msg.bcc = bcc
        msg.send(fail_silently=False)
    if log:
        logging.getLogger('info_logger').info(log)
