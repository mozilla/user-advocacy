(function($, d3, window, _) {

var parameters, min_severity, sent_params, param_string;
var results = {};
var input_json = {};

function startup() {
    parameters = $.deparam(document.location.search.substring(1));
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
        results = _(json.alerts).filter(function (d){
            var parsed_summary = summary_parse(d.summary);
            if (parsed_summary === null){
                console.log("Not processed:", d);
                return false;
            }
            return true;
        }).map(function (d) {
            var parsed_summary = summary_parse(d.summary);
            d.word = parsed_summary.word;
            d.percent = parsed_summary.percent;
            d.datetime = new Date(d.start_time.replace("Z","+0000"));
            d.split_desc = d.description.split("\n");
            d.links = _.map(d.links, function (e) {
                var re = /input\.mozilla\.org\/dashboard\/response\/(\d+)/;
                matches = re.exec(e.url);
                if (matches) {
                    e.id = matches[1];
                }
                return e;
            })
            return d;
        }).sortBy(['datetime', 'severity']).reverse().value();
        updateChange(true);
    });

}

function drawTables() {
    var selection = d3.select("#alert-list");
    $(selection[0]).empty();
    sev_cutoff = min_severity == 'default'?6:min_severity;
    var drawlist = _(results).filter(function(d) {
        return (d.severity >= sev_cutoff);
    }).slice(0, 200).value();
    var all_rows = selection.selectAll('.alerts').data(drawlist).enter();
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
    var details = alerts.append('div').classed({'details': true});
    details.append('h5').text('Details:');
    var description = details.append("div").classed({"desc": true});
    
    var desc_lines = description.selectAll(".desc_lines").data(function (d) {
        return d.split_desc;
    }).enter();
    desc_lines.append('p').text(function(d){return d});
    alerts.on("click", displayDetails);
    $(".details").hide();
    details.append('h5').text('Links:');
    var link_list = details.append('ul').classed({'link-list': true});
    $(link_list[0]).empty();
    link_list.each(makeLinks)
// POLISH

}

// Utilities

String.prototype.truncate =
     function (n, useWordBoundary) {
         var tooLong = this.length > n,
             s_ = tooLong ? this.substr(0,n-1) : this;
         s_ = useWordBoundary && tooLong ? s_.substr(0,s_.lastIndexOf(' ')) : s_;
         return  tooLong ? s_ + '&hellip;' : s_;
      };
      
function escapeHtml(str) {
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;")
        .replace(/\//g, "&#x2F;")
}

function makeLinks() {
    var link_list = d3.select(this);
    var list = link_list.datum().links;
    $(link_list[0]).empty();
    link_list.selectAll(".links").data(list).enter().append('li')
        .classed({"links": true}).each(function (e) {
            elink = d3.select(this);
            if (e.id !== undefined && input_json[e.id] !== undefined){
                var feedback = input_json[e.id];
                var short_desc = escapeHtml(feedback.description)
                    .truncate(300, true).replace("\n", "<br/>");
                elink.append('p')
                .append('a').attr('href', function (d) { return d.url })
                    .html(short_desc);
            } else {
                elink.append('a').attr('href', function (d) { return d.url })
                    .text(function (d) { return d.name });
            }
        })
    $(".links a").click( function(event) {
            event.stopPropagation();
            return true;
        });
}

function displayDetails () {
    var alert = d3.select(this);
    var details = alert.select('.details');
    var link_list = details.select('.link-list');
    $(details[0]).slideDown();
    var links = details.datum().links;
    var links_to_get = _(links).filter(function (d) {
        if (d.id === undefined || input_json[d.id] !== undefined) {
            return false;
        }
        return true;
    }).map("id").value();
    if (links_to_get.length > 0) {
        getInputData(links_to_get, makeLinks, link_list[0][0])
    };
    alert.on("click", null);
    alert.on("click", hideDetails);
}

function getInputData(link_ids, callback, this_context) {
    var url = 'https://input.mozilla.org/api/v1/feedback/?id=' +  link_ids.join(',');
    d3.json(url, function (error, json) {
        if (error) {
            console.log(error);
            return;
        }
        if (json.results.length == 0) {
            console.log("No results of input query")
            return;
        }
        var array = json.results;
        console.log(array);
        for (var i = 0; i < array.length; i++) {
            delete array[i].description_bigrams;
            input_json[array[i].id] = array[i];
        }
        callback.call(this_context);
    });
}

function hideDetails () {
    var alert = d3.select(this);
    var details = alert.select('.details');
    $(details[0]).slideUp();
    alert.on("click", null);
    alert.on("click", displayDetails);
}

function summary_parse(summary) {
    var re = /^(.+) is trending up by ([\d.]+|inf)$/;
    var matches = re.exec(summary);
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
    .domain([2,3,4,5,6,7,8,9,10])
    .clamp(true)
    .range(['rgba(255,255,204,0.8)',
            'rgba(255,237,160,0.8)',
            'rgba(254,217,118,0.8)',
            'rgba(254,178,76,0.8)',
            'rgba(253,141,60,0.8)',
            'rgba(252,78,42,0.8)',
            'rgba(227,26,28,0.8)',
            'rgba(189,0,38,0.8)',
            'rgba(128,0,38,0.8)'
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
        if (filter == 'default') {
            return false;
        } else if (d.name != filter) {
            return true;
        } else {
            return false;
        }
    });
    
    d3.selectAll('.telemetry-row')
    .classed('hidden', function (d) {
        if (cat_filter == 'default') {
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
    min_severity = parameters.min_severity ? parameters.min_severity : 'default';
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
