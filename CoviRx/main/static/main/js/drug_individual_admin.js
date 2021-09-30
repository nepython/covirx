$(document).ready(function() {
    setTimeout( function() {
        $(".flat-json-key").css("border", 'unset');
        $(".flat-json-key").attr('disabled', 'true');
        if ($(".form-row .flat-json-key").length!=0) {
            if (!$(".form-row .flat-json-key").get(-1).value) $(".form-row .flat-json-key").parent().css("display", "none");
        }
    }, 10);
});
