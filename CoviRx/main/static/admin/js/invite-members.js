$(document).ready(function(){
    $("#recipient-name").email_multiple({
        data: []
    });
    $('.enter-mail-id').addClass('form-control');
});

$('#send-invites').click(function() {
    $.getJSON( "/api/invite-members", {
        members: $('#recipient-name')[0].value,
        adminAccess: $('#adminAccessInvitee')[0].checked,
    }).done(function( data ) {
        $('#recipient-name')[0].value = null;
        $('#adminAccessInvitee')[0].checked=false;
        $('.all-mail').children().remove();
        location.reload();
    });
});
