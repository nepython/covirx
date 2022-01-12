var identifier = "name";
var mode = false; // advanced search mode
var suggestions = 5;
$("#showIdentifier").html(identifier);
function toggleAdvancedSearch() {
    $("#advanced-search-btn").toggleClass("btn-danger");
    $("body").toggleClass("advanced-mode");
    mode = !mode;
    if (mode) {
        $("#advanced-search-btn").html("Disable Advanced Search");
        $("#change-identifier-btn").attr("disabled", "true");
        // disappear other search boxes and make the main search box reappear
        mode = true;
    }
    else {
        $("#advanced-search-btn").html("Enable Advanced Search");
        $("#change-identifier-btn").removeAttr("disabled");
        mode = false;
        suggestions = 5;
    }
}

$(document).ready(function(){
    $('.nav-link')[0].classList.add('active'); // highlights the Home nav item
    $('#msg').html("Kindly use English when using search. Since search feature currently doesn't support input in any other languages.");

    function isEmptyObject(obj) {  // returns bool value whether the object is empty
        for(var key in obj) {
            if (obj[key])  return false;
        }
        return true;
    }

    function hasValue(elem) {  // for advanced search returns if any input contains a value
        return $(elem).filter(function() { return $(this).val(); }).length > 0;
    }

    // change identifier post update
    $('#identifiers').change(function(){
        identifier = $("input[class='identifier']:checked").val();
        $("#showIdentifier").html(identifier);
    });

    // search for every key press on main search
    $('#keyword').on('input', function(e) {
        var key = $('#keyword').val();
        slideContainer(key.length==0);
        var keyword = {};
        keyword[`${identifier}`] = key;
        setTimeout(function() {
            showSuggestions(keyword);
        }, 200); // handle debounce
    });

    // advanced search
    $("#advanced-search input").on('input', function() {
        var keyword = {};
        $("#advanced-search input").each(function() {
            keyword[this.placeholder] = this.value;
        });
        slideContainer(!hasValue($("#advanced-search input")));
        setTimeout(function() {
            showSuggestions(keyword);
        }, 200); // handle debounce
    });

    function slideContainer(noKey) {
        if (noKey) {
            $(".container").removeClass('slide-up', 300, 'linear');
        }
        else {
            if(!$(".container").hasClass('slide-up')) $(".container").addClass('slide-up', 300, 'linear');
        }
    }

    function showSuggestions(keyword) {
        if (mode==true || keyword[`${identifier}`]==$('#keyword').val()) {
            $('.suggestion').remove();  // clear previous suggestions
            $.getJSON( "api/drugs-metadata", {
                suggestions: suggestions,
                keyword: JSON.stringify(keyword)
            }).done(function( data ) {
                if (!isEmptyObject(keyword) && isEmptyObject(data)) {
                    addNoMatch(keyword);
                }
                else {
                    $.each(data, function(key, val) {
                        $("<div/>", {  // add a single suggestion div
                            id: key,
                            "class": "suggestion row",
                            onclick: `location.href='/drug/${val['id']}';`
                        }).appendTo("#suggestions");
                        var suggestion = $(`div[id='${key}']`);
                        suggestion.prepend("<div class='zero'></div><div class='one col-3'></div>"+
                        "<div class='two col-7'></div> <div class='three col-2'></div>");
                        addFields(key, val, suggestion);
                    });
                    $(`.suggestion-field-${identifier}`).css("font-weight", "bold");
                }
            });
        }
    }

    function addNoMatch(keyword) {
        var fields = [];
        $.each(keyword, function(k, v) {
            if (!isEmptyObject(v)) fields.push(`<span class="no-match-field"><b>${k}</b>="${v}"</span>`);
        });
        $("<div/>", {
            id: "no-match",
            "class": "no-match suggestion row",
            title: "No results found!"
        }).appendTo("#suggestions")
        $(".suggestion").html(`<i class="bi bi-emoji-frown"></i>
        <p>Sorry, we could not find a drug starting with the keywords ${fields}
        in our database.</p>`);
    }

    var colMap = {
        'label': 0,
        'name': 1,
        'synonyms': 1,
        'chebl': 1,
        'pubchemcid': 1,
        'cas_number': 2,
        'smiles': 2,
        'inchi': 2,
        'indication_class': 2,
    };
    var label = {
        '1': 'white',
        '2': 'green',
        '3': 'red',
        '4': '#FFBF00',
    };

    function addFields(key, val, suggestion) {
        $.each(val, function(k, v) {
            if (k=="label") {
                suggestion[0].children[colMap[k]].style.background = label[v];
            }
            else {
                $("<div/>", {
                    id: `${key}-suggestion-field-${k}`,
                    "class": `suggestion-field suggestion-field-${k}`,
                }).appendTo(suggestion[0].children[colMap[k]]);
                var elem = $(`div[id='${key}-suggestion-field-${k}']`);
                elem.html(v!=null?v:"-NA-");
                if(elem[0]!=undefined && elem[0].clientWidth < elem[0].scrollWidth) {
                    elem[0].classList.add("hide-overflow");
                }
                if (k=="smiles") { addSMILESVisualization(key, k, v, suggestion[0].children[3]); }
            }
        });
    }

    function addSMILESVisualization(key, k, v, parent) {
        $("<canvas/>", {
            id: `${key}-suggestion-field-canvas`,
            "class": `suggestion-field-canvas`,
        }).appendTo(parent);
        let options = {
            width: 140,
            height: 140,
            terminalCarbons:true,
            compactDrawing:false,
            explicitHydrogens:false
        };
        // Initialize the drawer to draw to canvas
        let smilesDrawer = new SmilesDrawer.Drawer(options);
        SmilesDrawer.parse(v, function(tree) {
            smilesDrawer.draw(tree, `${key}-suggestion-field-canvas`, "light", false);
        });
    }

    // suggestions count slider
    $.extend( $.ui.slider.prototype.options, {
        animate: 300
    });

    $("#flat-slider-vertical-3")
        .slider({
            max: 20,
            min: 1,
            range: "min",
            value: 5,
            orientation: "vertical"
        });
        $("#flat-slider-vertical-3")
        .slider("pips", {
            first: "pip",
            last: "pip"
        })
        .slider("float");
    $('.ui-slider-tip').on('DOMSubtreeModified', function(){
        suggestions = parseInt($('.ui-slider-tip').html());
    });
});

function openNav() {
    $("#identifier-sidenav").addClass("open");
    $(".sidenav-modal").css("display", "block");
}

function closeNav() {
    $("#identifier-sidenav").removeClass("open");
    $(".sidenav-modal").css("display", "none");
}
