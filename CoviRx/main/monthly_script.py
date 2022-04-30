import base64
import mimetypes
import os
from datetime import datetime, timedelta
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from io import BytesIO

from django.conf import settings
from django.core.management import call_command

import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from premailer import transform

from accounts.models import Visitor

# If modifying these scopes, delete the file token.json.
SCOPES = [
    'https://mail.google.com/',
    'https://www.googleapis.com/auth/drive'
]


def google_authenticate():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                '/home/hardik/project-courses/CS_f266/code/CoviRx/main/credentials.json', SCOPES)
            creds = flow.run_local_server(port=5000)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds


def gmail_send_message_with_attachment(to, bcc, subject, html, attachment=None):
    """Create and send an email message with attachment
        Print the returned  message id
        Returns: Message object, including message id
        Load pre-authorized user credentials from the environment.
        TODO(developer) - See https://developers.google.com/identity
        for guides on implementing OAuth2 for the application.
    """
    creds = google_authenticate()
    if isinstance(to, list):
        to = ",".join(to)
    if bcc and isinstance(bcc, list):
        bcc = ",".join(bcc)
    body = transform(
        html,
        allow_insecure_ssl=True,
        disable_leftover_css=True,
        strip_important=False,
        disable_validation=True,
    )
    try:
        service = build('gmail', 'v1', credentials=creds)
        mime_message = MIMEMultipart()
        mime_message['to'] = to
        if bcc:
            mime_message['bcc'] = bcc
        mime_message['subject'] = subject
        text_part = MIMEText(body, 'html')
        mime_message.attach(text_part)
        # Store larger files to Google Drive and use links
        if attachment:
            file_attachment = build_file_part(file=attachment)
            mime_message.attach(file_attachment)
        # encoded message
        encoded_message = base64.urlsafe_b64encode(mime_message.as_bytes()).decode()
        send_message_request_body = {'raw': encoded_message}
        # pylint: disable=E1101
        send_message = service.users().messages().send(userId='me', body=send_message_request_body).execute()
        print(f'Message Id: {send_message["id"]}')
    except HttpError as error:
        print(f'An error occurred: {error}')
        send_message = None
    return send_message


def build_file_part(file):
    """Creates a MIME part for a file.
    Args:
      file: The path to the file to be attached.
    Returns:
      A MIME part that can be attached to a message.
    """
    content_type, encoding = mimetypes.guess_type(file)
    if content_type is None or encoding is not None:
        content_type = 'application/octet-stream'
    main_type, sub_type = content_type.split('/', 1)
    if main_type == 'text':
        with open(file, 'rb'):
            msg = MIMEText('r', _subtype=sub_type)
    elif main_type == 'image':
        with open(file, 'rb'):
            msg = MIMEImage('r', _subtype=sub_type)
    elif main_type == 'audio':
        with open(file, 'rb'):
            msg = MIMEAudio('r', _subtype=sub_type)
    else:
        with open(file, 'rb') as FILE:
            msg = MIMEBase(main_type, sub_type)
            msg.set_payload(FILE.read())
    filename = os.path.basename(file)
    msg.add_header('Content-Disposition', 'attachment', filename=filename)
    return msg


def gdrive_upload_file(file_path):
    """Insert new file.
    Returns : Id's of the file uploaded, URL to view the file
    Load pre-authorized user credentials from the environment.
    TODO(developer) - See https://developers.google.com/identity
    for guides on implementing OAuth2 for the application.
    """
    creds = google_authenticate()
    file_name = f"{datetime.now().date()}-{file_path.split('/')[-1]}"
    try:
        # create drive api client
        service = build('drive', 'v3', credentials=creds)
        file_metadata = {'name': file_name}
        media = MediaFileUpload(file_path, mimetype=mimetypes.guess_type(file_path)[0], resumable=True)
        # pylint: disable=maybe-no-member
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    except HttpError as error:
        print(f'An error occurred: {error}')
        file = None
        return
    return file.get('id')


def gdrive_download_file(real_file_id):
    """Downloads a file
    Args:
        real_file_id: ID of the file to download
    Returns : IO object with location.
    Load pre-authorized user credentials from the environment.
    TODO(developer) - See https://developers.google.com/identity
    for guides on implementing OAuth2 for the application.
    """
    creds = google_authenticate()
    try:
        # create drive api client
        service = build('drive', 'v3', credentials=creds)
        file_id = real_file_id
        # pylint: disable=maybe-no-member
        request = service.files().get_media(fileId=file_id)
        file = BytesIO()
        downloader = MediaIoBaseDownload(file, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            # print(f'Download {int(status.progress() * 100)}.')
    except HttpError as error:
        print(f'An error occurred: {error}')
        file = None
    return file.getvalue()


def create_backup_and_send_restore_email():
    to = settings.EMAIL_HOST_USER
    subject = f'Restore CoviRx database as on {datetime.now().date()}'
    with open(f'{settings.BASE_DIR}/templates/mail_templates/recovery.html','r') as file:
        html = file.read()
        html = html.replace("{{date}}", str(datetime.now().date()))
    backup = f'{settings.BASE_DIR}/db_backup.json.gz'
    # we store the sqlite dump in gdrive to use for a backup
    call_command('dumpdata', '--all', f'-o={backup}', '--exclude=admin_interface.Theme')
    upload_id = gdrive_upload_file(backup)
    #TODO: Find another way to get hostname
    domain_name = 'http://localhost:8000' if settings.DEBUG else 'https://www.covirx.org'
    restore_link = f'{domain_name}/api/restore/{upload_id}'
    html = html.replace("{{restore_link}}", restore_link)
    gmail_send_message_with_attachment(to, None, subject, html, None)
    os.remove(backup)
    Visitor.objects.filter(timestamp__lte=datetime.now()-timedelta(31)).delete()
