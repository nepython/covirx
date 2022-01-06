var upload = true;
var pk = '';
var invalid_count = 0;

$('form').submit(function(e) {
    e.preventDefault();
    // Cancel the upload
    if (!upload) return; // to be handled by Modal confirmation
    // Upload the CSV file
    $("#upload-button").addClass("btn-danger");
    $("#upload-button").prop("value", "Cancel Upload");
    $("#upload-button").attr("data-bs-toggle", "modal");
    $("#upload-button").attr("data-bs-target", "#drug-cancel-modal");
    upload = false;
    $.ajax({
        xhr: function() {
            var xhr = new window.XMLHttpRequest();
            return showFileUpload(xhr);
        },
        url: '',
        headers: { "X-CSRFToken": $('input[name=csrfmiddlewaretoken]').val()},
        type: 'POST',
        data: new FormData(document.getElementById("uploadForm")),
        contentType: false,
        processData: false,
        success: function(data) {
            $("#updates").css("display", "block");
            if (data.hasOwnProperty('error'))
                $('#msg').html(data['error']);
            else {
                pk = data['csv-id'];
                var fields = data['invalid-headers'].join(", ");
                $('#msg').html(`Started databse update. The following fields were ignored, kindly add them as custom fields in the admin if they need to be stored in the database. <b>${fields}<b>`).fadeIn('slow');
                showUpdate(0, 0, -1);
            }
        }
    });

    const format = (num, decimals) => num.toLocaleString('en-US', {  // redude to two decimal places
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    });

    function showUpdate(valid, invalid, total) {
        $.ajax({
            url: 'drug-bulk-upload-update',
            headers: { "X-CSRFToken": $('input[name=csrfmiddlewaretoken]').val()},
            type: 'POST',
            dataType: 'json',
            data: JSON.stringify({'pk': pk, 'invalid_count': invalid_count, 'email': $('#recipient-name')[0].value}),
            contentType: false,
            processData: false,
            success: function(data) {
                if (valid>data['valid']) return // update completed
                var v = `${format(100*data['valid']/Math.max(data['total'], 1))}%`;
                var i = `${format(100*data['invalid']/Math.max(data['total'], 1))}%`
                $('.valid').css('width', v);
                $('.valid').html(`${v} drugs added in db`);
                $('.valid').prop('title', `${v} drugs added in db`);
                $('.invalid').css('width', i);
                $('.invalid').html(`${i} drugs rejected`);
                $('.invalid').prop('title', `${i} drugs rejected`);
                if (data['total']!=0) {
                    $('#show-total').html(data['total']);
                    $('#show-valid').html(data['valid']);
                    $('#show-invalid').html(data['invalid']);
                }
                $.each(data['invalid_drugs'], function(k, v) {
                    if (!$(`li[class="invalid-drugs-list"][title="${k}"]`).length) { // avoid duplicates in any case
                        $("<li/>", {
                            id: `invalid-drug-${k}`,
                            "class": `invalid-drugs-list`,
                            title: k
                        }).appendTo($('#invalidated-drugs')[0]);
                        $(`li[id='invalid-drug-${k}']`).html(`<div class="row"><div class="col-3 text-danger text-start">
                        ${k}:</div><div class="col-9">${v!=null?v:"-NA-"}</div></div>`);
                        invalid_count++;
                    }
                });
                // if no updates happening, show connection error
                if (upload) return;
                setTimeout(function() {
                    showUpdate(pk, data['valid'], data['invalid'], data['total']);
                }, 300);
            }
        });
    }

    // to show the upload progress bar
    function showFileUpload(xhr) {
        $("#upload").css("display", "block");
        xhr.upload.addEventListener("progress", function(evt) {
            if (evt.lengthComputable) {
                var percentComplete = format(100 * evt.loaded / evt.total);
                $(".file-upload-progress").css("width", `${percentComplete}%`);
                $(".file-upload-progress").html(`${percentComplete}% file uploaded`);
            }
        }, false);
        return xhr;
    }
});
$("#confirmed-cancel").click(function() {
    $("#upload-button").prop("value", "Upload CSV");
    $('#updates').css('display', 'none');
    $('#upload').css('display', 'none');
    $("#id_csv_file").val("");
    upload = true;
    // give some warning to the user
    $.ajax({
        url: 'drug-bulk-upload-update',
        headers: { "X-CSRFToken": $('input[name=csrfmiddlewaretoken]').val()},
        type: 'GET',
        data: {'cancel-upload': pk},
        success: function(data) {
            $('#msg').html(data[pk]).fadeIn('slow');
            $('#msg').delay(10000).fadeOut('slow');
        }
    });
    $("#upload-button").removeClass("btn-danger");
    $("#upload-button").removeAttr("data-bs-toggle");
    $("#upload-button").removeAttr("data-bs-target");
    $('#invalidated-drugs').html('');
    invalid_count = 0;
    return;
});

$(document).ready(function(){
    $("#recipient-name").email_multiple({
        data: []
    });
    $('.enter-mail-id').addClass('form-control');
});
