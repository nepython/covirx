// Wait for window load
$(window).on('load', function(){
    $(".se-pre-con").fadeOut(1000);
    $('.site-header').on('DOMSubtreeModified', function(){
        $(".container.slide-up").css("margin-top", 15+$(".site-header").height());
    });
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
function cookieAccept() {
    document.cookie = "cookie-accept=1 path=/";
    $("#CookielawBanner").css('display', 'none');
}
function checkCookieAccept() {
    return document.cookie.match(/^(.*;)?\s*cookie-accept\s*=\s*[^;]+(.*)?$/);
}
if (checkCookieAccept())
    $("#CookielawBanner").css('display', 'none');

// Google Translate
function googleTranslateElementInit() {
    new google.translate.TranslateElement({pageLanguage: 'en'}, 'google_translate_element');
}
