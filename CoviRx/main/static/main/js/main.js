// Wait for window load
$(window).on('load', function(){
    hidePreLoader();
    $(".container").css("margin-top", `${15+$(".site-header").height()}px`);
    $('.site-header').on('DOMSubtreeModified', function(){
        $(".container.slide-up").css("margin-top", `${15+$(".site-header").height()}px`);
    });
});

function googleInit() {
    gapi.load('auth2', function() {
        auth2 = gapi.auth2.init({
            client_id: '451260237676-sokoabp2tb0e73tgveglhhid0atq285r.apps.googleusercontent.com',
            cookiepolicy: 'single_host_origin',
        });
        element = document.getElementById('googleBtn');
        auth2.attachClickHandler(element, {}, onSignIn, onFailure);
     });
}
function onSignIn(googleUser) {
    var id_token = googleUser.getAuthResponse().id_token;
    sendID(id_token);
}
function sendID(id_token) {
    $.get( "/api/social-auth", {
        id_token: id_token
    }).done(function( data ) {
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
