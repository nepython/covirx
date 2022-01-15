from .utils import previous_upload

def last_update_processor(request):
    last_update = previous_upload.date_uploaded
    return {'last_update': last_update}
