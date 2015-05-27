(function($, d3, window, _) {

var parameters, sent_params, param_string;
var min_severity, product;
var results = {};
var input_json = {};
var urls = {
    'desktop': '/data/static/json/input_alerts.json',
    'android': '/data/static/json/android_input_alerts.json'
};
var reportUrls = {
    'desktop': '/reports/AlertReports/api.json',
    'android': '/reports/AlertReportsAndroid/api.json'
};
var reloadParams = {
    'product': true
}

function startup() {
    parameters = $.deparam(document.location.search.substring(1));
    setGlobals();
    adjustControls();
    run();
}

function run() {
    if (!(product in urls)) {
        showErrorMessage(true, "Invalid Product: " + product);
        return;
    }
    getReports();
    url = urls[product];
    $('#loading-throbber').show();
    $('#alert-list').hide();
    $('#error-message').hide();
    d3.json(url,function (error, json) {
        if (error) {
            console.log(error);
            showErrorMessage(true, "Server returned: " + error.statusText);
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
            d.datetime.setSeconds(0);
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
        updateChange(true, false);
    });

}

function getReports() {
    $('#report-list').empty();
    d3.json(reportUrls[product], function(error,json) {
        if (error) {
            $('#report-list').addClass('report-error')
            .text('No alert data found.');
            return
        }
        data = json.results;
        if (data.length < 1) {
            $('#report-list').addClass('report-error')
            .text('No alert data found.');
            return
        }
        data = _(data).sortBy('updated') // Change to 'created' if needed
            .reverse().value();
        data = data.slice(0,5); // Edit this number to set number of reports shown
        report_list = d3.select('#report-list');
        report_items = report_list.selectAll('.report-item').data(data)
            .enter()
            .append('a')
            .attr('href', function (d) { return d.path })
            .classed({
                'report-item': true
            });
        report_items.append('p')
            .text(function (d) {
                return d.title
            })
            .classed({
                'report-title': true,
            })
        report_items
            .append('p')
            .text(function (d) {
                var dt = new Date(d.updated);
                return "Updated: " + dt.toLocaleFormat('%b %e %l:%M%p') 
            })
            .classed({
                'report-date': true,
                'text-right': true
            });
        
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
    details.append('p').append('a').attr({ 'href': function(d) {
        return "https://input.mozilla.org/en-US/?product=Firefox&q=" + d.word;
    }}).text(function(d) {
        return "Search input for " +  d.word;
    });
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
    var truncated = 0;
    var process_list = list;
    if (list.length > 10) {
        truncated = (list.length - 10);
        process_list = list.slice(0,10);
    }
    $(link_list[0]).empty();
    link_list.selectAll(".links").data(process_list).enter().append('li')
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
    if (truncated > 0){
        d3.select(this)
            .append('li')
            .text('And '+truncated+' more...')
    }
    $(".details a").click( function(event) {
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
    }).map("id").slice(0,10).value();
    if (links_to_get.length > 0) {
        getInputData(links_to_get, makeLinks, link_list[0][0]);
    } else {
        makeLinks.call(link_list[0][0]);
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

var severityScale = d3.scale.linear()
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
    $("#min_severity").val(min_severity);
    $("#product").val(product);
}

function updateChange(redraw, reload) {
    var url = document.location.pathname;
    url = url + '?' + $.param(removeDefaultParams(parameters));
    history.pushState(parameters, 'Alerts dashboard', url);
    setGlobals();
    if (reload) {
        run();
    } else if (redraw) {
        drawTables();
    }
    adjustControls();
}

function setGlobals() {
    min_severity = parameters.min_severity ? parameters.min_severity : 'default';
    product = parameters.product ? parameters.product : 'desktop';
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
    if (typeof value == "undefined"){
        value = $("#" + type).val()
    }
    parameters[type] = value ? value : 'default';
    if (type in reloadParams) {
        updateChange(true, true);
    } else {
        updateChange(true, false);
    }
}

window.changeParam = changeParam;

window.addEventListener('popstate', function(event) {
    if (event.state !== null) {
        parameters = event.state;
        updateChange(true, false);
    } else {
        startup();
    }
});

startup();

// Controls for choosing things.

function updateForm() {

}


function showErrorMessage (state, text) {
    if (state && (text === undefined || text == '' || text === null)) {
        console.log("showing error message (blank)");
        $('#loading-throbber').hide();
        $('#alert-list').hide();
        $('#error-message').show();
        $('#blank-text').show();
    } else if (state) {
        console.log("showing error message " + text);
        $('#loading-throbber').hide();
        $('#alert-list').hide();
        $('#error-message').show();
        $('#blank-text').hide();
        $('#error-text').empty().text(text);
    } else {
        $('#loading-throbber').hide();
        $('#error-message').hide();
        $('#alert-list').show();
    }
}


}(jQuery, d3, window, _));
