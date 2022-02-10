// createComponents
function createElement(element, attribute, innerHTML) {
    var el = document.createElement(element);
    for (var key in attribute)
        el.setAttribute(key, attribute[key]);
    el.innerHTML = innerHTML;
    document.getElementsByTagName('html')[0].appendChild(el);
}

createElement('div', {"id": "dark-mode-toggle"},
`<input type="checkbox" class="checkbox" id="darkModeToggle" onclick="darkModeToggle()">
    <label for="darkModeToggle" class="label">
        <i class="bi bi-moon-stars"></i>
        <i class="bi bi-sun"></i>
        <div class="ball">
    </label>`);
createElement('div', {"id": "google_translate_element"}, null);

// Google Translate
function googleTranslateElementInit() {
    new google.translate.TranslateElement({pageLanguage: 'en'}, 'google_translate_element');
}

if (localStorage.getItem("covirx-dark-mode") == 'on') {
    disableDarkReaderLog();
    DarkReader.enable();
    document.getElementById('darkModeToggle').checked=true;
}

// Dark Mode, Light mode toggle
async function darkModeToggle() {
    if (localStorage.getItem("covirx-dark-mode") == 'on') {
        localStorage.setItem("covirx-dark-mode", 'off');
        DarkReader.disable();
        return;
    }
    localStorage.setItem("covirx-dark-mode", 'on');
    disableDarkReaderLog();
    DarkReader.enable();
    msgAboutSmiles();
}
function disableDarkReaderLog() {
    // logs are disabled for 5s as darkReader (external library) logs are not useful to us
    var old_console_error = console.error;
    console.error = () => {};
    setTimeout(function () {
        console.error = old_console_error;
    }, 5000);
}

function msgAboutSmiles() {
    if (document.getElementsByTagName("canvas").length==0)
        return;
    document.getElementById("msg").innerHTML = "The page contains Drug structure figures which might be displayed incorrectly.\n Reload the page to display them properly."
}

// Give alert to user on him going offline
window.addEventListener('offline', () => $("#msg").html("You are offline please turn on internet connection to run website."));
