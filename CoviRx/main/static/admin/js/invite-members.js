$(document).ready(function(){
    $("#recipient-name").email_multiple({
        data: []
    });
    $('.enter-mail-id').addClass('form-control');
});

$('#send-invites').click(function() {
    $.getJSON( "/api/invite-members", {
        members: $('#recipient-name')[0].value
    }).done(function( data ) {
        $('#recipient-name')[0].value = null;
        $('.all-mail').children().remove();
        location.reload();
    });
});
