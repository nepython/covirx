function hidePreLoader() {
    if (dissappearPreLoader) {
        $("#preLoader").fadeOut(400);
    }
    else {
        setTimeout(function() {
            hidePreLoader();
        }, 100);
    }
}
