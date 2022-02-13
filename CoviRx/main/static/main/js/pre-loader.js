function hidePreLoader() {
    if (dissappearPreLoader) {
        $("#preLoader").fadeOut(400);
        circle1.pause();
        circle2.pause();
        circle3.pause();
        circle4.pause();
        preloader_loading.pause();
    }
    else {
        setTimeout(function() {
            hidePreLoader();
        }, 100);
    }
}
