from .models import DrugBulkUpload
from .utils import static_version


def last_update_processor(request):
    previous_upload = DrugBulkUpload.objects.order_by('-date_uploaded').first()
    if previous_upload:
        last_update = previous_upload.date_uploaded
    else:
        last_update = "-NA-"
    return {'last_update': last_update}


def get_static_version(request):
    """
    We can force the static files to reload by changing the version
    """
    return {'static_version': static_version}
