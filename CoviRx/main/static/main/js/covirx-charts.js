// visitors charts weekly or monthly view switch
var isChanged = false;
var visitor_data;

function load_charts(requested_charts) {
    $.ajax({
        url: '/api/charts-json',
        headers: { "X-CSRFToken": $('input[name=csrfmiddlewaretoken]').val()},
        type: 'GET',
        data: requested_charts,
        dataType: "json",
        success: function(data) {
            google.charts.load('current', {'packages':['corechart']});
            timeout = setInterval(function () {
                if (google.visualization != undefined && google.visualization.arrayToDataTable!= undefined && google.visualization.PieChart!= undefined) {
                    clearInterval(timeout);
                    if (data['visitors'] != undefined) {
                        google.charts.setOnLoadCallback(VisitorsChart(data['visitors']));
                        visitor_data = data['visitors'];
                    }
                    google.charts.setOnLoadCallback(DrugCategories(data['categories'], data['total_drugs']));
                    google.charts.setOnLoadCallback(DrugLabels(data['labels']));
                    google.charts.setOnLoadCallback(DrugPhase(data['phase']));
                    $('.charts-visualisation').show();
                }
            }, 300);
        }
    });
}

function VisitorsChart(data) {
    for (i=1; i<data.length; i++)
        data[i][0] = new Date(data[i][0]); // converting to javascript date
    var data = google.visualization.arrayToDataTable(data);
    var options = {
        title : 'Daily Visitors across the website',
        vAxis: {title: 'Unique Visitors'},
        hAxis: {title: 'Days'},
        seriesType: 'bars',
        series: {5: {type: 'line'}},
        titleTextStyle: {italic: true},
        backgroundColor: '#e7f8ff',
        hAxis: {
            viewWindow: {
                min: new Date(Date.now() - 7*24*60*60*1000),
                max: new Date()
            },
            gridlines: {
                color: 'transparent'
            }
        },
    };
    if (isChanged) days = 30;
    else days = 7;
    options.hAxis.viewWindow.min = new Date(Date.now() - days * 24*60*60*1000);
    options.hAxis.viewWindow.max = new Date();
    var chart = new google.visualization.ComboChart(document.getElementById('visitor-chart'));
    chart.draw(data, options);
}
function DrugCategories(data, total_categories) {
    var data = google.visualization.arrayToDataTable(data);
    var options = {
        title: 'Categories of Drugs in database',
        pieHole: 0.3,
        titleTextStyle: {italic: true},
        backgroundColor: '#e7f8ff',
    };
    var chart = new google.visualization.PieChart(document.getElementById('drug-categories-chart'));
    chart.draw(data, options);
    // TODO: Uncomment below line once the invalidated drugs have been added
    // $('#categories-chart #labelOverlay').show();
    $('#labelOverlay span').html(total_categories);
}
function DrugLabels(data) {
    var data = google.visualization.arrayToDataTable(data);
    var options = {
        title: 'Label-wise classification of drugs in database',
        is3D: true,
        titleTextStyle: {italic: true},
        backgroundColor: '#e7f8ff',
        colors: ['white', 'green', 'red', '#FFBF00'],
    };
    var chart = new google.visualization.PieChart(document.getElementById('drug-labels-chart'));
    chart.draw(data, options);
}
function DrugPhase(data) {
    var data = google.visualization.arrayToDataTable(data);
    var options = {
        title: 'Clinical Phase',
        legend: { position: 'none' },
        titleTextStyle: {italic: true},
        backgroundColor: '#e7f8ff',
        bars: 'horizontal',
        axes: {x: { 0: { side: 'top', label: 'Number of Drugs'}}},
    };
    var chart = new google.visualization.BarChart(document.getElementById('drug-phase-chart'));
    chart.draw(data, options);
};

$(window).on('load', function() {
    var button = document.getElementById('visitors-view');
    if (button!= undefined) {
        button.onclick = function () {
            isChanged = !isChanged;
            VisitorsChart(visitor_data);
            if (isChanged)
                {button.innerHTML= 'Change to Weekly View';}
            else
                {button.innerHTML = 'Change to Monthy View';}
        };
    }
});
