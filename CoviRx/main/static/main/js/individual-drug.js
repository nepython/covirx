$(document).ready(function(){
    // Add hyperlinks to identifiers
    let identifiers = ["ChEMBL ID", "CAS Number", "PubChem ID", "Drug Bank", "ChEBI"]
    $.each(identifiers, function(index, identifier) {
        let element = $(`div[title='${identifier}']`)[0]
        let val = element.innerHTML;
        let content = val;
        if (val!="-NA-") {
            if (index==0) {
                content = `<a class="link-no-decoration" href="https://www.ebi.ac.uk/chembl/compound_report_card/${val.split("|")[0]}/" target="_blank">${val}</a>`
            }
            else if (index==1) {
                content = `<a class="link-no-decoration" href="https://commonchemistry.cas.org/detail?cas_rn=${val.split("|")[0]}" target="_blank">${val}</a>`
            }
            else if (index==2) {
                content = `<a class="link-no-decoration" href="https://pubchem.ncbi.nlm.nih.gov/compound/${val.split("|")[0]}" target="_blank">${val}</a>`
            }
            else if (index==3) {
                content = `<a class="link-no-decoration" href="https://go.drugbank.com/drugs/${val.split("|")[0]}" target="_blank">${val}</a>`
            }
            else if (index==4) {
                content = `<a class="link-no-decoration" href="https://www.ebi.ac.uk/chebi/searchId.do?chebiId=${val.split("|")[0]}" target="_blank">${val}</a>`
            }
            element.innerHTML = content;
        }
    });

    // COPY LINK TO CLIPBOARD
    var $temp = $("<input>");
    var $url = $(location).attr('href');
    $('#share-drug').on('click', function() {
        $("body").append($temp);
        $temp.val($url).select();
        document.execCommand("copy");
        $temp.remove();
        $("#share-drug-info").fadeIn();
        $("#share-drug-info").fadeOut(2000);
    });

    // SEARCH PANE
    var identifier = "name";
    var suggestions = 5;
    function isEmptyObject(obj) {  // returns bool value whether the object is empty
        for(var key in obj) {
            if (obj[key])  return false;
        }
        return true;
    }
    // search for every key press on main search
    $('#keyword').on('input', function(e) {
        var key = $('#keyword').val();
        var keyword = {};
        keyword[`${identifier}`] = key;
        setTimeout(function() {
            showSuggestions(keyword);
        }, 200);
    });
    function showSuggestions(keyword) { // handle debounce
        if (keyword[`${identifier}`]==$('#keyword').val()) {
            $('#suggestions .suggestion').remove();  // clear previous suggestions
            $.getJSON( "/api/drugs-metadata", {
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
                            title: val['name'],
                            onclick: `location.href='/drug/${val['id']}';`
                        }).appendTo("#suggestions");
                        var suggestion = $(`div[id='${key}']`);
                        suggestion.prepend("<div class='col-7 one'></div><div class='col-5 two'></div>");
                        addFields(key, val, suggestion, 'search-suggestions');
                    });
                }
            });
        }
    }
    function addNoMatch(keyword) {
        var fields = [];
        $.each(keyword, function(k, v) {
            if (!isEmptyObject(v)) fields.push(`<b>${k}="${v}"</b>`);
        });
        $("<div/>", {
            id: "no-match",
            "class": "no-match suggestion row",
            title: "No results found!"
        }).appendTo("#suggestions")
        $("#no-match").html(`<i class="bi bi-emoji-frown"></i>
        <p>Sorry, we could not find a drug starting with the keywords ${fields}
        in our database.</p>`);
    }
    function addFields(key, val, suggestion, purpose) {
        $("<div/>", {
            id: `${purpose}-${key}-suggestion-field-name`,
            "class": `suggestion-field suggestion-field-name`,
        }).appendTo(suggestion[0].children[0]);
        $(`div[id='${purpose}-${key}-suggestion-field-name']`).html(val['name']!=null?val['name']:"-NA-");
        addSMILESVisualization(key, 'smiles', val['smiles'], suggestion[0].children[1]);
    }
    function addSMILESVisualization(key, k, v, parent) {
        $("<canvas/>", {
            id: `${key}-suggestion-field-canvas`,
            "class": `suggestion-field-canvas`,
        }).appendTo(parent);
        let options = {
            width: 80,
            height: 80,
            terminalCarbons:true,
            compactDrawing:false,
            explicitHydrogens:false
        };
        // Initialize the drawer to draw to canvas
        let smilesDrawer = new SmilesDrawer.Drawer(options);
        theme = (localStorage.getItem("covirx-dark-mode") == 'on')?"dark":"light";
        SmilesDrawer.parse(v, function(tree) {
            smilesDrawer.draw(tree, `${key}-suggestion-field-canvas`, theme, false);
        });
    }

    // SIMILAR DRUGS
    var drug_id = $url.split('/')[$url.split('/').length-1];
    $.getJSON( `/api/similar/${drug_id}`, {
    }).done(function( data ) {
        $(".flat-loader").css('display', 'none');
        if (isEmptyObject(data)) {
            $("<div/>", {
                id: "no-similar-match",
                "class": "no-similar-match suggestion row",
                title: "No results found!"
            }).appendTo("#similar_drugs")
            $("#no-similar-match").html("<p>No similar drug found in our database.</p>");
        }
        else {
            $.each(data, function(key, val) {
                $("<div/>", {  // add a single suggestion div
                    id: key,
                    "class": "suggestion row",
                    title: val['name'],
                    onclick: `location.href='/drug/${val['id']}';`
                }).appendTo("#similar_drugs");
                var suggestion = $(`div[id='${key}']`);
                suggestion.prepend("<div class='col-12 one'></div><div class='col-6 two'></div>");
                addFields(key, val, suggestion, 'similar-drugs');
            });
        }
    });

    // Overflow
    $(".property-value").each(function(i, elem) {
        if(elem.clientWidth < elem.scrollWidth) {
            elem.classList.add("hide-overflow");
            elem.classList.add("wrap");
        }
    });
});

function downloadPDF() {
    $("body > div").not('.container').not($(".container").find("*")).add(".btn").add(".input-group")
        .add(".dropdown-menu").add("#dark-mode-toggle").add("#google_translate_element").addClass('d-none');
    window.print();
    $(".d-none").removeClass("d-none");
}
