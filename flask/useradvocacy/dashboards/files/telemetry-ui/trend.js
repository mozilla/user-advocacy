(function($, d3, window, _) {

var parameters, filter_hash, sent_params, param_string;

var diff_signif_percent = 2;
var max_width = 80;
var sort_order, filter, show_value, filter_hash, cat_filter;
var week = 0;
var bar_color = '#6A0000'

var special_tables = ['clicks'];

window.addEventListener("message", function (event) {
    if (event.data === 'whimsy:enabled') {
        whimsify(true);
    }
}, false);

var singulars = {
    'clicks' : 'click',
    'searches' : 'search',
    'actions' : 'action'
}

var results = {};
var filter_tables = [];
var filter_cats = [];

var bilateralColor = d3.scale.linear().domain([-diff_signif_percent, 0, diff_signif_percent]).clamp(true)
    .range(['#0849DE','#FFF','#FF7400']);
var singleNew = d3.scale.linear().domain([0,100]).clamp(true)
    .range(['#FFF','#7A05DF']);
var singleOld = d3.scale.linear().domain([0,100]).clamp(true)
    .range(['#FFF','#2E4334']);
var singleDiff = d3.scale.linear().domain([0,diff_signif_percent * 3]).clamp(true)
    .range(['#FFF','#6A0000']);

function startup() {
    parameters = $.deparam(document.location.search.substring(1));
    console.log(parameters);
    run();
    getAvailDates();
}

function run() {
var param_string = $.param(parameters);
url = '/data/api/v1/telemetry_stat?' + param_string;
console.log(url);
$('#loading-throbber').show();
$('#main').hide();
$('#error-message').hide();
d3.json(url,function (error, json) {
//d3.json("hellofeedback.json",function (error, json) {
    if (error) {
        console.log(error);
        showErrorMessage(true, error);
        return;
    }
    var returnMessage = _.values(json.messages).join(" -- ");
    documentParams(json.parameters);
    week = (json.parameters.timestep == 'week')?1:0;
    if (json.status != 200 ) {
        showErrorMessage(true, returnMessage);
        return;
    } else if (_.size(json.results) == 0) {
        showErrorMessage(true);
        return;
    } else {
        $("#warning-message").empty();
        if (_.keys(json.messages).length > 0) {
            returnMessage = "Warning: " + returnMessage;
            $("#warning-message").text(returnMessage);
        }
        showErrorMessage(false);
    }
    
    var uniq_values = {};
    
    results = _(json.results).sortBy(["sort", "measure"]).map(function (d) {
        var source = _.clone(d, true);
        delete source["times"];
        var new_times = _.map(d.times, function(e) {
            return _.assign(e, source);
        });
        new_times = _.map(new_times, function (i) {
            var i_source = _.clone(i, true);
            delete i_source["users"];
            var base_potential_users = i.base_potential_users ? i.base_potential_users : 0;
            var potential_users = i.potential_users ? i.potential_users : 0;
            var values = _(i.users).map( function (j) {
                var split_value = j.value.split('-');
                var sort_key = split_value[0];
                var name = j.value;
                if (i.type == 'bucket') {
                    sort_key = parseInt(sort_key,10);
                    name = split_value[1] == split_value[0] ?
                        split_value[0] : name;
                    var smart_table = i.table;
                    if (i.table == 'unspecified' || i.table == '') {
                        smart_table = 'actions'
                    }
                    if(split_value[1] == 1 && singulars[smart_table] !== undefined){
                        smart_table = singulars[smart_table];
                    }
                    name = name + ' ' + smart_table;
                }
                if (sort_key == 'other') {
                    sort_key = '|';
                }
                j["name"] = name;
                j["sort_key"] = sort_key;
                var item = {};
                item[i.table] = {};
                item[i.table][name] = 1;
                return j;
            });
            values = values.map(function (j){
                var count = typeof j.count === 'undefined' ? 0 : j.count;
                var percent = count / potential_users * 100;
                var split_value = j.value.split('-');
                return {
                    "name" : j.name,
                    "sort_key" : j.sort_key,
                    "percent" : percent,
                    "count" : count
                }
            })
            values = values.filter(function (d) {
                    return (!(d.sort_key == '|' || d.name.substr(-1) == '+')
                        || d.percent > 0.01);
                })
                .value();
            values = _.sortBy(values, "sort_key");
            var oddity = 1 - _.max(values, "percent").percent;
            var measure_name = i.alias?i.alias:i.measure;
            return _.assign({ 
                "measure": measure_name,
                "measure_lc": measure_name.toLocaleLowerCase(),
                "full-name": i.measure, 
                "table": i.table.trim() == ""? "unspecified" : i.table.trim(),
                "category": i.category.trim() == ""? null : i.category.trim(), 
                "given_sort" : i.sort,
                "values": values,
                "description": i.description ? i.description : "<No Description>",
                "oddity": oddity
            }, i_source);
        })
        d.times = new_times;
        return d;
    }).value();
    console.log('results', results);
    updateChange(true);
    _.forEach(results, function(i) {
        $('#results').append('<div id="' + i.measure + '">');
        drawGraph(i);
    });
});

}


function documentParams(params) {
    console.log("document:", params);
}

function drawGraph(item) {
    var selection = d3.select("#" + item.measure);
    $(selection[0]).empty();
    selection.append('h3').classed('measure-name', true)
        .text(item.alias + " (" + item.table + ")");
    selection.append('p').classed('measure-description', true).text(item.description);
    var display = selection.append('div').classed('row', true)
    var graph = display.append('div').classed({
        'measure-chart': true,
        'col-md-6' : true
        })
        .attr('id', item.measure + '-graph');
    var hover_table = display.append('div').classed({
        'measure-table': true,
        'col-md-6' : true
        })
        .attr('id', item.measure + '-table')
        .append('p').classed('table-error', true)
            .text("Please select a bar to see telemetry breakdown");
    var ymax = _.max(item.times,function(d) { return d.active_users / d.potential_users });
    
    ymax_value = ymax.active_users / ymax.potential_users * 100;
    
    console.log(ymax);
    
    var chart = barChart()
        .x(function(d) { return d.time })
        .y(function(d) { return d.active_users / d.potential_users * 100})
        .ymax(ymax_value)
        .ymin(0)
        .ylabel("Percentage of users")
        .fillcolor("#E68A2E");
        
    if(!week) {
        chart.xlabel("Version");
    } else {
        chart.xlabel("Week");
    }
    
    graph.datum(item.times).call(chart);
    graph.selectAll('.bar').on('click', generateTable);
    
    
    function generateTable (table_data) {
        
        var $table = $(this).parents('.measure-chart')
            .parent('.row').children('.measure-table');
        var this_graph = $(this).parents('.measure-chart').toArray()[0];
        var this_table = $table.toArray()[0];
        $table.empty();
        if (d3.select(this).classed('selected-bar')) {
            d3.select(this_graph).selectAll(".bar")
                .style("fill","#E68A2E").classed('selected-bar', false);
            d3.select(this_table)
                .append('p').classed('table-error', true)
                .text("Please select a bar to see telemetry breakdown");
            return;
        }
        $table.append($('<h3></h3>')
            .text("Details for " + table_data.original_datum.time));
        d3.select(this_graph).selectAll(".bar")
            .style("fill","#E68A2E").classed('selected-bar', false);
        d3.select(this).style("fill", bar_color).classed('selected-bar', true);
        d3_table = d3.select(this_table).append('table');
        table_head = d3_table.append('tr').classed('tablehead', true);
        table_head.append('th').text("Value");
        table_head.append('th').text("Count");
        table_head.append('th').text("Percent");
        d3_table.selectAll('.tablerow').data(table_data.original_datum.values)
            .enter()
            .append('tr').classed('tablerow', true);
        var table_rows = d3_table.selectAll('.tablerow');
        table_rows.append('td').append('p')
            .text(function (d) {return d.name});
        table_rows.append('td').append('p')
            .text(function (d) {return sessionsFormat(d.count)})
            .classed('.value-number', true);
        table_rows.append('td').append('p')
            .text(function (d) {return percentFormat(d.percent)})
            .classed('.value-number', true);
        table_rows.style('background-color', function(d) { return singleNew(d.percent)})
        table_rows.style('color', function(d) {
            var bg = $(this).css('background-color');
            return (d3.hsl(bg).l < 0.6)?'white':null;
        });

    }
}

// Utilities


var singleNew = d3.scale.linear().domain([0,100]).clamp(true)
    .range(['#FFF','#7A05DF']);

function percentFormat(value) {
    var formatter = d3.format('2.2%')
    if (value == 0){
        return '--';
    } else if (value < 0.01) {
        return '<0.01%';
    } else {
        return formatter(value/100)
    }
}

function sessionsFormat(count){
    var formatter = d3.format(',d');
    if (count == 0){
        return 'No sessions';
    } else if (count == 1) {
        return '1 session';
    } else {
        return formatter(count) + ' sessions'
    }
}

function updateChange() {
    console.log(parameters);
    var url = document.location.pathname;
    url = url + '?' + $.param(removeDefaultParams(parameters));
    history.pushState(parameters, 'Telemetry Single Stat View', url);
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
$('#form-timeframe').change(showHideVersionWeek);

// Controls for choosing things.

function updateForm() {
    var type;
    var timeframe = parameters.timestep;    
    $("input[type='radio']#timeframe-" + timeframe).click();
    var os = parameters.os?parameters.os:"default";
    $("input[type='radio']#os-" + os).click();
    var channel = parameters.channel?parameters.channel:"release";
    console.log('channel', channel);
    $("input[type='radio']#channel-" + channel).click();
    var params = ['start_date', 'end_date', 'start_version', 'end_version'];
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

function showHideVersionWeek() {
    var selected_timeframe = $("input[type='radio'][name='timeframe']:checked").val();
    console.log("selected_timeframe", selected_timeframe);
    var params = ['start_date', 'end_date', 'start_version', 'end_version'];
    _(params).forEach(function (param){
        $("select#" + param).hide();
        $("#form-label-"+param).hide();
    });
    if (selected_timeframe == 'week') {
        $(".show-week").show();
        $(".show-version").hide();
        $("select#end_date").show();
        $("select#start_date").show();
        $("#form-label-end_date").show();
        $("#form-label-start_date").show();
    } else if (selected_timeframe == 'version') {
        $(".show-week").hide();
        $(".show-version").show();
        $("select#start_version").show();
        $("select#end_version").show();
        $("#form-label-start_version").show();
        $("#form-label-end_version").show();
    } else  {
        $(".show-week").hide();
        $(".show-version").hide();
    }
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

// Form control window methods


window.toggleForm = function () {
    $('#data-form').toggle()
}

window.toggleDisplay = function () {
    $('#display-settings').toggle()
}


function whimsify(status) {
    if (status) {
        bar_color = 'url(#rainbow)'
    } else {
        bar_color = '#6A0000'
    }
}

function getAvailDates() {
    d3.json('/data/api/v1/telemetry/params', function (error, json) {
        if (error) {
            console.log(error);
            return;
        }
        var valid_weeks = json.weeks.reverse();
        var valid_versions = json.versions.reverse();
        $('#start_date').empty();
        $('#end_date').empty();
        ['#start_date', '#end_date'].forEach( function (selector) {
            var selection = d3.select(selector);
            selection.selectAll("option").data(valid_weeks).enter()
                .append('option').attr('value', function (d) {
                    return d;
                }).text(function (d) { return d;})
        });
        $('#end_version').empty();
        $('#start_version').empty();
        ['#start_version', '#end_version'].forEach( function (selector) {
            var selection = d3.select(selector);
            selection.selectAll("option").data(valid_versions).enter()
                .append('option').attr('value', function (d) {
                    return d;
                }).text(function (d) { return d;})
        });
        updateForm();
        showHideVersionWeek();
    });
}

window.submitForm = function () {
    var new_params = {};
    var selected_type = $("input[type='radio'][name='timeframe']:checked");
    if (selected_type.length > 0) {
        new_params['timestep'] = selected_type.val();
    }
    var selected_os = $("input[type='radio'][name='OS']:checked");
    if (selected_os.length > 0) {
        new_params['os'] = selected_os.val();
    }
    var selected_channel = $("input[type='radio'][name='channel']:checked");
    if (selected_os.length > 0) {
        new_params['channel'] = selected_channel.val();
    }
    if (new_params['timestep'] == 'week') {
        new_params['end_date'] = $("select#end_date").val();
        new_params['start_date'] = $("select#start_date").val();
    } else {
        new_params['end_date'] = null;
        new_params['start_date'] = null;
    }
    if (new_params['timestep'] == 'version') {
        new_params['end_version'] = $("select#end_version").val();
        new_params['start_version'] = $("select#start_version").val();
    } else {
        new_params['end_version'] = null;
        new_params['start_version'] = null;
    }
    console.log("new_params", new_params);
    console.log("before params", parameters);
    parameters = _.assign(parameters, new_params);
    parameters = removeDefaultParams(parameters);
    console.log("after params", parameters);
    var url = document.location.pathname;
    url = url + '?' + $.param(removeDefaultParams(parameters));
    history.pushState(parameters, 'Single Telemetry Stat', url);
    run();
}



}(jQuery, d3, window, _));


(function($, d3, window, _) { 


}(jQuery, d3, window, _));
