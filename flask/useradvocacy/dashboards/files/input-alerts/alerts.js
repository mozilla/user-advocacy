(function($, d3, window, _) {

var parameters, filters, sent_params, param_string;
var results = {};

function startup() {
    parameters = $.deparam(document.location.search.substring(1));
    filters = location.hash.substring(1);
    setGlobals();
    run();
}

function run() {
    url = '/data/static/json/input_alerts.json';
    $('#loading-throbber').show();
    $('#main').hide();
    $('#error-message').hide();
    d3.json(url,function (error, json) {
        if (error) {
            console.log(error);
            showErrorMessage(true, error);
            return;
        }
        if (_.size(json.alerts) == 0) {
            showErrorMessage(true);
            return;
        } else {
            showErrorMessage(false);
        }
        results = _(json.alerts).map(function (d){
            parsed_summary = summary_parse(d.summary);
            if (parsed_summary === null){
                console.log(d.summary);
                return d;
            } else {
                d.word = parsed_summary.word;
                d.percent = parsed_summary.percent;
                d.datetime = new Date(d.start_time.replace("Z","+0000"));
                return d;
            }
        })
        .sortBy(['datetime', 'severity']).reverse().value();
        updateChange(true);
    });

}

function drawTables() {
    var selection = d3.select("#alert-list");
    $(selection[0]).empty();
    var all_rows = selection.selectAll('.alerts').data(results).enter();
    var alerts = all_rows.append('div').classed('alerts', true);
    alerts.style("background-color", function(d) {
        return severityScale(d.severity);
    });
    alerts.append('h4').text(function(d) {return d.word});
    alerts.append('p').classed('datetext', true).text( function(d){
        return d.datetime.toLocaleString()
    });
    alerts.append('p').classed('sevtext', true).text(function(d){
        return "Severity: " + d.severity;
    });
    
// POLISH

}

// Utilities

function summary_parse(summary) {
    var re = /^(.+) is trending up by ([\d.]+|inf)$/;
    matches = re.exec(summary);
    if (matches === null) {
        return null;
    } else {
        if (matches[2] == 'inf') {
            return {
                'word': matches[1],
                'percent': Infinity
            }
        } else {
            return {
                'word': matches[1],
                'percent': matches[2]
            }
        }
    }
}

severityScale = d3.scale.linear()
    .domain([10,9,8,7,6,5,4,3,2])
    .clamp(true)
    .range([
        'rgb(215,48,39)',
        'rgb(244,109,67)',
        'rgb(253,174,97)',
        'rgb(254,224,144)',
        'rgb(255,255,191)',
        'rgb(224,243,248)',
        'rgb(171,217,233)',
        'rgb(116,173,209)',
        'rgb(69,117,180)'
    ]);

// Global flow control functions

function adjustControls() {
/*
    if(diff){
        $(".no-diff").hide();
        $(".diff-only").show();
    } else {
        $(".diff-only").hide();
        $(".no-diff").show();
    }
    $(".control-sort").removeClass("active");
    $("#sort-ctrl-" + sort_order).addClass("active");
    $(".control-value").removeClass("active");
    $("#value-ctrl-" + show_value).addClass("active");
    if (show_value == 'default') {
        $("#value-ctrl-summary").addClass("active");
        $("#value-ctrl-summary_count").addClass("active");
    }
    $(".control-filter").removeClass("active");
    $("#filter-ctrl-" + filter).addClass("active");
    $(".control-category").removeClass("active");
    $("#cat-ctrl-" + cat_filter).addClass("active");
    */
}

function updateChange(redraw) {
    setGlobals();
    var url = document.location.pathname;
    url = url + '?' + $.param(removeDefaultParams(parameters));
    history.pushState(parameters, 'Alerts dashboard', url);
    if (redraw) {
        drawTables();
    }
    filterTables();
}

function filterTables(){    
    d3.selectAll('.telemetry-table')
    .classed('hidden', function (d) {
        if (filter == 'default' || filter_hash != '') {
            return false;
        } else if (d.name != filter) {
            return true;
        } else {
            return false;
        }
    });
    
    d3.selectAll('.telemetry-row')
    .classed('hidden', function (d) {
        if (cat_filter == 'default' || filter_hash != '') {
            return false;
        } else if (d.category === null && cat_filter == 'unspecified') {
            return false;
        } else if (d.category != cat_filter) {
            return true;
        } else {
            return false;
        }
    });
}

function setGlobals() {
/*
    sort_order = parameters.sort_order ? parameters.sort_order : 'default';
    filter = parameters.filter ? parameters.filter : 'default';
    show_value = parameters.show_value ? parameters.show_value : 'default';
    cat_filter = parameters.cat_filter ? parameters.cat_filter : 'default';
*/
}

function removeKnownParams (p) {
    var out = _.clone(p);
    for (i in controls) {
        delete out.i
    }
    return out;
}

function removeDefaultParams (p) {
    var out = _.clone(p);
    for (i in out) {
        if (out[i] === null || out[i] == 'default' || out[i] == '') {
            delete out[i];
        }
    }
    return out;
}

function changeParam(type, value) {
    parameters[type] = value ? value : 'default';
    updateChange(true);
}

window.changeParam = changeParam;

window.addEventListener('popstate', function(event) {
    if (event.state !== null) {
        parameters = event.state;
        updateChange(true);
    } else {
        startup();
    }
});

startup();

// Controls for choosing things.

function updateForm() {
    var type;
    var timeframe;
    if (parameters.version && !parameters.base_version) {
        type = "version"
        timeframe = 'version';
    } else if (parameters.date && !parameters.base_date) {
        type = "cs-week";
        timeframe = 'week';
    } else if (parameters.version && parameters.base_version) {
        type = "version-diff"
        timeframe = 'version';
    } else if (parameters.date && parameters.base_date) {
        type = "week-diff"
        timeframe = 'week';
    } else {
        type = "cs-week";
        timeframe = 'week';
    }
    
    $("input[type='radio']#type-" + type).click();
    $("input[type='radio']#timeframe-" + timeframe).click();
    var os = parameters.os?parameters.os:"default";
    $("input[type='radio']#os-" + os).click();
    var channel = parameters.channel?parameters.channel:"release";
    $("input[type='radio']#channel-" + channel).click();
    var params = ['date', 'base_date', 'version', 'base_version'];
    _(params).forEach(function (param){
        if (parameters[param] && parameters[param] != 'default') {
            $("select#" + param + " [value='" + parameters[param] + "']")
                .prop('selected', true);
        } else if (parameters[param] != 'default') {
            $("select#" + param + " [value='latest']")
                .prop('selected', true);
        }
    })

}


function showErrorMessage (state, text) {
    if (state && (text === undefined || text == '' || text === null)) {
        $('#loading-throbber').hide();
        $('#main').hide();
        $('#error-message').show();
        $('#blank-text').show();
    } else if (state) {
        $('#loading-throbber').hide();
        $('#main').hide();
        $('#error-message').show();
        $('#blank-text').hide();
        $('#error-text').empty().text(text);
    } else {
        $('#loading-throbber').hide();
        $('#main').show();
        $('#error-message').hide();

    }
}

function uppercaseFirst(string) {
    var index = string.search("\\w");
    if (index < 0) return string;
    return string.substr(0, index) + string.substr(index, 1).toUpperCase() + string.substr(index+1);
}


}(jQuery, d3, window, _));
