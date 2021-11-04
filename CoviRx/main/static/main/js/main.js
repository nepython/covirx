// Wait for window load
$(window).on('load', function(){
    $(".se-pre-con").fadeOut(1000);
});

function googleInit() {
    gapi.load('auth2', function() {
        auth2 = gapi.auth2.init({});
        element = document.getElementById('googleBtn');
        auth2.attachClickHandler(element, {}, onSignIn, onFailure);
     });
}
function onSignIn(googleUser) {
    var id_token = googleUser.getAuthResponse().id_token;
    sendID(id_token);
}
function sendID(id_token) {
    $.getJSON( "api/social-auth", {
        id_token: id_token
    }).done(function( data ) {
        console.log(data);
        if (data['admin']) {
            window.location.replace(data['admin']);
        }
        else {
            $('#msg').html(data['msg']).fadeIn('slow');
            $('#msg').delay(20000).fadeOut('slow');
        }
    });
}
function onFailure(error) {
    $('#msg').html(error).fadeIn('slow');
    $('#msg').delay(20000).fadeOut('slow');
}
