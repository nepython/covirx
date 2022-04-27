$(document).ready(function(){
    $("#recipient-name").email_multiple({
        data: []
    });
    $('.enter-mail-id').addClass('form-control');
});

$('#send-invites').click(function() {
    if (!$('#recipient-name').val())
        alert("Could not send the Invite. Please read the Note!\n\n 1. Enter valid email IDs and press enter.\n\n 2. To submit click on send invite.\n\n 3. The invite link will expire after 7 days.\n");
    else
        $.getJSON( "/api/invite-members", {
            members: $('#recipient-name')[0].value,
            adminAccess: $("input[class='user-type']:checked").val(),
        }).done(function( data ) {
            $('#recipient-name')[0].value = null;
            $("input[class='user-type']:checked").checked=false;
            $("input[class='user-type']")[0].checked=true;
            $('.all-mail').children().remove();
            location.reload();
        });
});
