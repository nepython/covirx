from .models import DrugBulkUpload

def last_update_processor(request):
    previous_upload = DrugBulkUpload.objects.order_by('-date_uploaded').first()
    if previous_upload:
        last_update = previous_upload.date_uploaded
    else:
        last_update = "-NA-"
    return {'last_update': last_update}
