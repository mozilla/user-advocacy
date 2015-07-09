/* eslint-env browser */
/* global jQuery:false, d3:false, _:false */
/* eslint camelcase:[0] */

'use strict';

(function($, d3, window, _) {

var cat_filter;
var filter;
var filter_hash;
var parameters;
var show_value;
var sort_order;

var diff = 0;
var diff_signif_percent = 2;
var max_width = 80;

var controls = ['sort_order', 'filter', 'show_value', 'cat_filter'];
var special_tables = ['clicks'];

var singulars = {
    'clicks': 'click',
    'searches': 'search',
    'actions': 'action'
};

var results = {};
var filter_tables = [];
var filter_cats = [];

var bilateralColor = d3.scale.linear().domain([-diff_signif_percent, 0, diff_signif_percent]).clamp(true)
    .range(['#0849DE', '#FFF', '#FF7400']);
var singleNew = d3.scale.linear().domain([0, 100]).clamp(true)
    .range(['#FFF', '#7A05DF']);
var singleOld = d3.scale.linear().domain([0, 100]).clamp(true)
    .range(['#FFF', '#2E4334']);
var singleDiff = d3.scale.linear().domain([0, diff_signif_percent * 3]).clamp(true)
    .range(['#FFF', '#6A0000']);

function setGlobals() {
    sort_order = parameters.sort_order ? parameters.sort_order : 'default';
    filter = parameters.filter ? parameters.filter : 'default';
    show_value = parameters.show_value ? parameters.show_value : 'default';
    cat_filter = parameters.cat_filter ? parameters.cat_filter : 'default';
}

function removeKnownParams (p) {
    var out = _.clone(p);
    for (var i in controls) {
        delete out[i];
    }
    return out;
}

function documentParams(params) {
    var title = '';
    var same = [];
    if (diff) {
        var nonbase = [];
        var base = [];
        var array = ['date', 'version', 'os', 'channel'];
        for (var i = 0; i < array.length; i++) {
            var v = array[i];
            if (!_.isUndefined(params[v])) {
                var a = params[v];
                if (!_.isUndefined(params['base_' + v])
                        && params['base_' + v] !== params[v]) {
                    var b = params['base_' + v];
                    if (v === 'os') {
                        nonbase.push(a === 'all' ? 'all OSes' : uppercaseFirst(a));
                        base.push(b === 'all' ? 'all OSes' : uppercaseFirst(b));
                    } else if (v === 'version') {
                        nonbase.push('Firefox ' + a);
                        base.push('Firefox ' + b);
                    } else {
                        nonbase.push(uppercaseFirst(a));
                        base.push(uppercaseFirst(b));
                    }
                } else {
                    if (v === 'os') {
                        same.push(a === 'all' ? 'all OSes'
                            : uppercaseFirst(a));
                    } else if (v === 'version') {
                        same.push('Firefox ' + a);
                    } else {
                        same.push(uppercaseFirst(a));
                    }

                }
            }

        }

        title += 'Comparing ' + nonbase.join(' and ') + ' to ' + base.join(' and ')
            + ' for ' + same.join(' and ');

    } else {
        title += 'Showing telemetry UI data for ';
        if (!_.isUndefined(params.date)) {
            title += params.date;
            title += ' ';
        }
        if (!_.isUndefined(params.version)) {
            title += 'Firefox ' + params.version;
            title += ' ';
        }
        title += 'on ';
        if (!_.isUndefined(params.os)) {
            same.push(params.os === 'all' ? 'all OSes' : uppercaseFirst(params.os));
        }
        if (!_.isUndefined(params.channel)) {
            same.push(uppercaseFirst(params.channel));
        }
        title += same.join(' and ');

    }
    $('#title-string').empty().text(title);
}

function removeDefaultParams (p) {
    var out = _.clone(p);
    for (var i in out) {
        if (out[i] === null || out[i] === 'default' || out[i] === '') {
            delete out[i];
        }
    }
    return out;
}

function adjustControls() {
    if(diff){
        $('.no-diff').hide();
        $('.diff-only').show();
    } else {
        $('.diff-only').hide();
        $('.no-diff').show();
    }
    $('.control-sort').removeClass('active');
    $('#sort-ctrl-' + sort_order).addClass('active');
    $('.control-value').removeClass('active');
    $('#value-ctrl-' + show_value).addClass('active');
    if (show_value === 'default') {
        $('#value-ctrl-summary').addClass('active');
        $('#value-ctrl-summary_count').addClass('active');
    }
    $('.control-filter').removeClass('active');
    $('#filter-ctrl-' + filter).addClass('active');
    $('.control-category').removeClass('active');
    $('#cat-ctrl-' + cat_filter).addClass('active');
}

function filterTables(){
    d3.selectAll('.telemetry-table')
    .classed('hidden', function (d) {
        if (filter === 'default' || filter_hash !== '') {
            return false;
        } else if (d.name !== filter) {
            return true;
        } else {
            return false;
        }
    });

    d3.selectAll('.telemetry-row')
    .classed('hidden', function (d) {
        if (cat_filter === 'default' || filter_hash !== '') {
            return false;
        } else if (d.category === null && cat_filter === 'unspecified') {
            return false;
        } else if (d.category !== cat_filter) {
            return true;
        } else {
            return false;
        }
    });
}

function updateChange(redraw) {
    setGlobals();
    var url = document.location.pathname;
    url = url + '?' + $.param(removeDefaultParams(parameters));
    history.pushState(parameters, 'Telemetry UI dashboard', url);
    adjustControls();
    if (redraw) {
        sortResults();
        drawTables();
    }
    filterTables();
}

function createFilters() {
    var filter_controls = d3.select('#filter-controls');
    $(filter_controls[0]).empty();
    var filters = filter_controls.selectAll('.control-filter')
        .data(filter_tables).enter();
    filters.append('button')
        .classed({'btn': true, 'btn-default': true, 'control-filter': true})
        .attr('id', function(d) { return 'filter-ctrl-' + d; })
        .text(function (d) { return d; })
        .on('click', function(d){
            parameters.filter = d;
            updateChange(false);
        });
    filter_controls.insert('button', ':first-child')
        .classed({'btn': true, 'btn-default': true, 'control-filter': true})
        .attr('id', 'filter-ctrl-default')
        .text('Show All')
        .on('click', function(){
            parameters.filter = 'default';
            updateChange(false);
        });

    var cat_controls = d3.select('#category-controls');
    $(cat_controls[0]).empty();
    var cats = cat_controls.selectAll('.control-category')
        .data(filter_cats).enter();
    cats.append('button')
        .classed({'btn': true, 'btn-default': true, 'control-category': true})
        .attr('id', function(d) { return 'cat-ctrl-' + d; })
        .text(function (d) { return d; })
        .on('click', function(d){
            parameters.cat_filter = d;
            updateChange(false);
        });
    cat_controls.insert('button', ':first-child')
        .classed({'btn': true, 'btn-default': true, 'control-category': true})
        .attr('id', 'cat-ctrl-default')
        .text('Show All')
        .on('click', function(){
            parameters.cat_filter = 'default';
            updateChange(false);
        });

}

function run() {
  var sent_params = removeKnownParams(parameters);
  var param_string = $.param(sent_params);
  var url = '/data/api/v1/telemetry?' + param_string;
  $('#loading-throbber').show();
  $('#main').hide();
  $('#error-message').hide();
  d3.json(url, function (error, json) {
  //d3.json("hellofeedback.json", function (error, json) {
      if (error) {
          showErrorMessage(true, error);
          return;
      }
      var returnMessage = _.values(json.messages).join(' -- ');
      if (json.status !== 200 ) {
          showErrorMessage(true, returnMessage);
          return;
      } else if (_.size(json.results) === 0) {
          showErrorMessage(true);
          return;
      } else {
          $('#warning-message').empty();
          if (_.keys(json.messages).length > 0) {
              returnMessage = 'Warning: ' + returnMessage;
              $('#warning-message').text(returnMessage);
          }
          showErrorMessage(false);
      }
      diff = json.resolved_parameters.is_diff;
      documentParams(json.resolved_parameters);
      var uniq_values = {};

      results = _.map(json.results, function (i) {
          var users = i.users;
          var table = i.table === null ? 'unspecified' : i.table;
          _(users).map( function (j) {
              var split_value = j.value.split('-');
              var sort_key = split_value[0];
              var name = j.value;
              if (i.type !== 'str') {
                  sort_key = parseInt(sort_key, 10);
                  name = split_value[1] === split_value[0] ?
                      split_value[0] : name;
                  var smart_table = table;
                  if (table === 'unspecified' || table === '') {
                      smart_table = 'actions';
                  }
                  if(split_value[1] === 1 && singulars[smart_table] !== undefined){
                      smart_table = singulars[smart_table];
                  }
                  name = name + ' ' + smart_table;
              }
              if (sort_key === 'other') {
                  sort_key = '|';
              }
              j.name = name;
              j.sort_key = sort_key;
              var item = {};
              item[i.table] = {};
              item[i.table][name] = 1;
              _.merge(uniq_values, item);
              uniq_values[i.table][name] = sort_key;
              return j;
          });
          return i;
      });
      results = _(results)
          .map(function (i) {
              var base_potential_users = i.base_potential_users ? i.base_potential_users : 0;
              var potential_users = i.potential_users ? i.potential_users : 0;
              var table = i.table === null ? 'unspecified' : i.table;
              var full_table = _.contains(special_tables, table);
              var category = i.category === null ? '' : i.category;
              filter_cats.push(category);
              var values = _(i.users);
              if (diff) {
                  values = values.map(function (j){
                      var base_count = typeof j.base_count === 'undefined' ? 0 : j.base_count;
                      var count = typeof j.count === 'undefined' ? 0 : j.count;
                      var base_percent = base_count === 0 ? 0 :
                          base_count / base_potential_users * 100;
                      var percent = count === 0 ? 0 :
                          count / potential_users * 100;
                      return {
                          'name': j.name,
                          'sort_key': j.sort_key,
                          'base_percent': base_percent,
                          'percent': percent,
                          'difference_factor': percent / base_percent * 100,
                          'difference': percent - base_percent,
                          'count': count,
                          'base_count': base_count
                      };
                  });
              } else {
                  values = values.map(function (j){
                      var count = typeof j.count === 'undefined' ? 0 : j.count;
                      var percent = count / potential_users * 100;
                      return {
                          'name': j.name,
                          'sort_key': j.sort_key,
                          'percent': percent,
                          'count': count
                      };
                  });
              }
              values = values.filter(function (d) {
                      return (!(d.sort_key === '|' || (d.name || '').substr(-1) === '+')
                          || d.percent > 0.01);
                  })
                  .value();
              if (full_table) {
                  _.forEach(uniq_values[table], function (v, j) {
                      if (_.contains(_.pluck(values, 'name'), j)) {
                        // Do nothing here.
                      } else if (diff) {
                          values.push({
                              'name': j,
                              'sort_key': v,
                              'base_percent': 0,
                              'percent': 0,
                              'difference_factor': 0,
                              'difference': 0,
                              'count': 0,
                              'base_count': 0
                          });
                      } else {
                          values.push({
                              'name': j,
                              'sort_key': v,
                              'percent': 0,
                              'count': 0
                          });
                      }
                  });
              }
              values = _.sortBy(values, 'sort_key');
              var value_length = values.length;
              _.map(values, function (v) { _.assign(v, {
                  'value_length': value_length,
                  'status': i.measure_status
              });
              });
              var total_diff = 0;
              var oddity = 0;
              if (diff) {
                  total_diff = _.reduce(values, function (a, b) {
                      return a + Math.abs(b.difference);
                  }, 0);
              } else {
                  oddity = 1 - _.max(values, 'percent').percent;
              }
              var measure_name = i.alias ? i.alias : i.measure;
              var summary = [];
              if (diff) {
                  var sum_count = i.active_users;
                  var sum_base_count = i.base_active_users;
                  var sum_difference = 0;
                  var sum_difference_factor = 0;
                  sum_difference = sum_count - sum_base_count;
                  if (sum_base_count !== 0) {
                      sum_difference_factor = sum_count / sum_base_count;
                  }
                  summary.push({
                      'name': 'Active Sessions',
                      'count': sum_count,
                      'base_count': sum_base_count,
                      'difference': sum_difference,
                      'difference_factor': sum_difference_factor,
                      'format': 'sessions'
                  });
                  sum_count = i.potential_users === 0 ? 0 : i.active_users / i.potential_users * 100;
                  sum_base_count = i.base_potential_users === 0 ?
                          0 : i.base_active_users / i.base_potential_users * 100;
                  sum_difference = 0;
                  sum_difference_factor = 0;
                  sum_difference = sum_count - sum_base_count;
                  if (sum_base_count !== 0) {
                      sum_difference_factor = sum_count / sum_base_count;
                  }
                  summary.push({
                      'name': 'Percentage of sessions',
                      'count': sum_count,
                      'base_count': sum_base_count,
                      'difference': sum_difference,
                      'difference_factor': sum_difference_factor,
                      'format': 'percent'
                  });
                  if (i.type === 'bucket') {
                      sum_count = i.average;
                      sum_base_count = i.base_average;
                      sum_difference = sum_count - sum_base_count;
                      sum_difference = sum_count - sum_base_count;
                      if (sum_base_count !== 0) {
                          sum_difference_factor = sum_count / sum_base_count;
                      }
                      summary.push({
                          'name': 'per overall session',
                          'count': sum_count,
                          'base_count': sum_base_count,
                          'difference': sum_difference,
                          'difference_factor': sum_difference_factor,
                          'format': 'actions'
                      });
                      sum_count = i.nonzero_average;
                      sum_base_count = i.base_nonzero_average;
                      sum_difference = sum_count - sum_base_count;
                      if (sum_base_count !== 0) {
                          sum_difference_factor = sum_count / sum_base_count;
                      }
                      summary.push({
                          'name': 'per active session',
                          'count': i.nonzero_average,
                          'base_count': i.base_nonzero_average,
                          'difference': sum_difference,
                          'difference_factor': sum_difference_factor,
                          'format': 'actions'
                      });
                  }
              } else {
                  summary.push({
                      'name': 'Active sessions',
                      'count': i.active_users,
                      'format': 'sessions'
                  });
                  summary.push({
                      'name': 'Percentage of sessions',
                      'count': i.potential_users === 0 ?
                          0 : i.active_users / i.potential_users * 100,
                      'format': 'percent'
                  });
                  if (i.type === 'bucket') {
                      summary.push({
                          'name': 'per overall session',
                          'count': i.average,
                          'format': 'actions'
                      });
                      summary.push({
                          'name': 'per active session',
                          'count': i.nonzero_average,
                          'format': 'actions'
                      });
                  }
              }
              var summary_length = summary.length;
              _.map(summary, function (v) { _.assign(v, {
                  'summary_length': summary_length,
                  'table': table.trim() === '' ? 'actions' : table.trim()
              });
              });
              return {
                  'measure': measure_name,
                  'measure_lc': measure_name.toLocaleLowerCase(),
                  'full-name': i.measure,
                  'table': table.trim() === '' ? 'unspecified' : table.trim(),
                  'category': category.trim() === '' ? null : category.trim(),
                  'given_sort': i.sort,
                  'values': values,
                  'value_length': value_length,
                  'summary': summary,
                  'summary_length': summary_length,
                  'description': i.description ? i.description : '<No Description>',
                  'status': i.measure_status,
                  'type': i.type,
                  'total_diff': total_diff,
                  'oddity': oddity,
                  'percent': summary[1].count,
                  'average_sort': (typeof summary[2] !== 'undefined') ? summary[2].count : summary[1].count,
                  'nonzero_average_sort': (typeof summary[3] !== 'undefined') ? summary[3].count : summary[1].count
              };
          })
          .sortBy(function (d) { return d.category + '|' + d.measure_lc; })
          .sortBy('given_sort')
          .forEach(function (v, i) {
              v.sort = i;
          })
          .groupBy('table')
          .map(function (v, k) {
              return {
                  'name': k,
                  'measures': v
              };
          })
          .sortBy('name')
          .value();
      filter_tables = _(results).map('name').value();
      filter_cats = _(filter_cats).sort().uniq().compact().value();
      filter_cats.push('unspecified');
      createFilters();
      updateChange(true);
  });

}

function updateForm() {
    var type;
    var timeframe;
    if (parameters.version && !parameters.base_version) {
        type = 'version';
        timeframe = 'version';
    } else if (parameters.date && !parameters.base_date) {
        type = 'cs-week';
        timeframe = 'week';
    } else if (parameters.version && parameters.base_version) {
        type = 'version-diff';
        timeframe = 'version';
    } else if (parameters.date && parameters.base_date) {
        type = 'week-diff';
        timeframe = 'week';
    } else {
        type = 'cs-week';
        timeframe = 'week';
    }

    $('input[type=\'radio\']#type-' + type).click();
    $('input[type=\'radio\']#timeframe-' + timeframe).click();
    var os = parameters.os ? parameters.os : 'default';
    $('input[type=\'radio\']#os-' + os).click();
    var channel = parameters.channel ? parameters.channel : 'release';
    $('input[type=\'radio\']#channel-' + channel).click();
    var params = ['date', 'base_date', 'version', 'base_version'];
    _(params).forEach(function (param){
        if (parameters[param] && parameters[param] !== 'default') {
            $('select#' + param + ' [value="' + parameters[param] + '"]')
                .prop('selected', true);
        } else if (parameters[param] !== 'default') {
            $('select#' + param + ' [value="latest"]')
                .prop('selected', true);
        }
    });
}


function showHideForm() {
    var selected_type = $('input[type=\'radio\'][name=\'type\']:checked').val();
    var params = ['date', 'base_date', 'version', 'base_version'];
    _(params).forEach(function (param){
        $('select#' + param).hide();
        $('#form-label-' + param).hide();
    });
    if (selected_type === 'cs-version') {
        $('select#version').show();
        $('#form-label-version').show();
        $('#timeframe-week').parent('label').removeClass('active');
        $('#timeframe-version').parent('label').addClass('active');
    } else if (selected_type === 'cs-week') {
        $('select#date').show();
        $('#form-label-date').show();
        $('#timeframe-week').parent('label').addClass('active');
        $('#timeframe-version').parent('label').removeClass('active');
    } else if (selected_type === 'version-diff') {
        $('select#version').show();
        $('select#base_version').show();
        $('#form-label-version').show();
        $('#form-label-base_version').show();
        $('#timeframe-week').parent('label').removeClass('active');
        $('#timeframe-version').parent('label').addClass('active');
    } else if (selected_type === 'week-diff') {
        $('select#date').show();
        $('select#base_date').show();
        $('#form-label-date').show();
        $('#form-label-base_date').show();
        $('#timeframe-week').parent('label').addClass('active');
        $('#timeframe-version').parent('label').removeClass('active');
    }
}

function showHideVersionWeek() {
    var selected_timeframe = $('input[type=\'radio\'][name=\'timeframe\']:checked').val();
    var selected_type = $('input[type=\'radio\'][name=\'type\']:checked').val();
    var params = ['date', 'base_date', 'version', 'base_version'];
    _(params).forEach(function (param){
        $('select#' + param).hide();
        $('#form-label-' + param).hide();
    });
    if (selected_timeframe === 'week') {
        $('.show-week').show();
        $('.show-version').hide();
        if (selected_type === 'cs-week') {
            $('select#date').show();
            $('#form-label-date').show();
        } else if (selected_type === 'week-diff') {
            $('select#date').show();
            $('select#base_date').show();
            $('#form-label-date').show();
            $('#form-label-base_date').show();
        }
    } else if (selected_timeframe === 'version') {
        $('.show-week').hide();
        $('.show-version').show();
        if (selected_type === 'cs-version') {
            $('select#version').show();
            $('#form-label-version').show();
        } else if (selected_type === 'version-diff') {
            $('select#version').show();
            $('select#base_version').show();
            $('#form-label-version').show();
            $('#form-label-base_version').show();
        }
    } else {
        $('.show-week').hide();
        $('.show-version').hide();
    }
}

function getAvailDates() {
    d3.json('/data/api/v1/telemetry/params', function (error, json) {
        if (error || json.error) {
            console.log(error || json.error); // eslint-disable-line no-console
            return;
        }
        var valid_weeks = json.weeks.reverse();
        var valid_versions = json.versions.reverse();
        $('#date').empty();
        $('#base_date').empty();
        ['#date', '#base_date'].forEach( function (selector) {
            var selection = d3.select(selector);
            selection.selectAll('option').data(valid_weeks).enter()
                .append('option').attr('value', function (d) {
                    return d;
                }).text(function (d) { return d; });
        });
        d3.select('#date').insert('option', ':first-child').attr('value', 'latest')
            .text('Latest (' + json.latest_week + ')');
        d3.select('#base_date').insert('option', ':first-child').attr('value', 'previous')
            .text('Previous (' + json.prev_week + ')');

        $('#version').empty();
        $('#base_version').empty();
        ['#version', '#base_version'].forEach( function (selector) {
            var selection = d3.select(selector);
            selection.selectAll('option').data(valid_versions).enter()
                .append('option').attr('value', function (d) {
                    return d;
                }).text(function (d) { return d; });
        });
        d3.select('#version').insert('option', ':first-child').attr('value', 'latest')
            .text('Rolling (' + json.latest_version + ')');
        d3.select('#base_version').insert('option', ':first-child').attr('value', 'previous')
            .text('Rolling (' + json.prev_version + ')');

        updateForm();
        showHideForm();
        showHideVersionWeek();
    });
}


function startup() {
    parameters = $.deparam(document.location.search.substring(1));
    if (parameters.date === undefined &&
        parameters.base_date === undefined &&
        parameters.version === undefined &&
        parameters.base_version === undefined) {
        parameters.date = 'latest';
    } else if (parameters.date === undefined && parameters.base_date !== undefined) {
        parameters.date = parameters.base_date;
        delete parameters.base_date;
    } else if (parameters.version === undefined && parameters.base_version !== undefined) {
        parameters.version = parameters.base_version;
        delete parameters.base_version;
    }
    filter_hash = location.hash.substring(1);
    setGlobals();
    run();
    getAvailDates();
}


function sortResults() {
    results = _.forEach(results, function (v) {
        var measures = v.measures;
        if (sort_order === 'total_diff') {
            v.measures = _(measures).sortBy('total_diff').reverse().value();
        } else if (sort_order === 'oddity') {
            v.measures = _(measures).sortBy('oddity').reverse().value();
        } else if (sort_order === 'alpha') {
            v.measures = _(measures).sortBy('measure_lc').value();
        } else if (sort_order === 'percent') {
            v.measures = _(measures).sortBy('percent').reverse().value();
        } else if (sort_order === 'nonzero') {
            v.measures = _(measures).sortBy('nonzero_average_sort').reverse().value();
        } else if (sort_order === 'average') {
            v.measures = _(measures).sortBy('average_sort').reverse().value();
        } else {
            v.measures = _.sortBy(measures, 'sort');
        }
    });
}

function generateDetailUrl(type, value) {
    var url = 'trend.html?';
    var out_params = {};
    out_params.os = _.isUndefined(parameters.os) ? '' : parameters.os;
    out_params.channel = _.isUndefined(parameters.channel) ?
        'release' : parameters.channel;
    out_params.timestep = _.isUndefined(parameters.version) ? 'week' : 'version';
    out_params[type] = value;
    url += $.param(out_params);
    return url;
}

function drawTables() {
    var selection = d3.select('#full-list');
    $(selection[0]).empty();
    var rows = selection.selectAll('.telemetry-table').data(results).enter();
    var table_group = rows.append('div').classed('telemetry-table', true);
    table_group.append('h3')
        .text(function(d) { return d.name + ':'; });
    var item_table = table_group.selectAll('.telemetry-row')
        .data(function (d) { return d.measures; }).enter()
            .append('table')
            .style('width', '100%')
            .classed('telemetry-row', true);
    var table_row = item_table.append('tr');
    var measure_name = table_row.append('td').style('width', '33%');
    measure_name.append('p').classed('category-name', true)
        .text(function(d) { return d.category === 'null' ? null : d.category; });
    measure_name.append('p').classed('measure-name', true).append('a')
        .attr('href', function(d) { return generateDetailUrl('elements', d.measure_lc); })
        .text(function(d) {
            if (d.status === 'old') {
                return d.measure + ' (deprecated)';
            } else if (d.status === 'new') {
                return diff ? d.measure + ' (new)' : d.measure;
            } else {
                return d.measure;
            }
        });
    measure_name.append('p').classed('measure-description', true)
        .text(function(d) { return d.description; });
    var cells;

    if (show_value === 'summary_count' || show_value === 'summary_percent' || show_value === 'summary' || show_value === 'default') {
        cells = table_row.selectAll('.telemetry-cell')
            .data(function (d) { return d.summary; }).enter()
            .append('td').classed('telemetry-cell', true);
        cells.style('width', function (d) { return (66 / d.summary_length) + '%'; });
        cells.append('p').text(function (d) { return d.name + ': '; })
            .classed('value-name', true);
        cells.append('p').text(function (d) {
            var format = d.format === 'actions' ? d.table : d.format;
            if (diff) {
                if ((d.count === undefined || _.isNaN(d.count))
                    && (d.base_count === undefined || _.isNaN(d.base_count))){
                    return '☠';
                } else if (d.count === undefined || _.isNaN(d.count)) {
                    return 'Deprecated';
                } else if (d.base_count === undefined || _.isNaN(d.base_count)) {
                    return 'New measure';
                }
            }
            if (diff && show_value === 'summary_count') {
                if (d.difference < 0) {
                    return '↓' + smartFormat(-d.difference, format);
                } else if (d.difference > 0) {
                    return '↑' + smartFormat(d.difference, format);
                } else {
                    return 'No change.';
                }
            } else if (diff && (show_value === 'summary_percent' ||
                                show_value === 'default')) {
                var change = d.difference_factor * 100 - 100;
                if (change < 0) {
                    return '↓' + percentFormat(-change);
                } else if (change > 0) {
                    return '↑' + percentFormat(change);
                } else {
                    return 'No change.';
                }
            } else {
                return smartFormat(d.count, format);
             }
        }).classed('value-number', true);
        cells.attr('title', function (d) {
            var format = d.format === 'actions' ? d.table : d.format;
            if (diff) {
                return 'Before: ' + smartFormat(d.base_count, format) +
                    ' After: ' + smartFormat(d.count, format);
            } else {
                return '';
            }
        });

       if (diff && (show_value === 'summary_count' || show_value === 'default')) {
            cells.style('background-color', function(d) {
                if (d.format === 'percent') {
                    return bilateralColor(d.difference);
                } else if (d.format === 'sessions') {
                    return bilateralColor(d.difference / 100000);
                } else if (d.name === 'per active user'){
                    return bilateralColor(d.difference);
                } else if (d.name === 'per overall user') {
                    return bilateralColor(d.difference * 30);
                }
            });

            measure_name.style('background-color', function() {
                return 'white';
            });
        } else if (diff && (show_value === 'summary_percent')) {
            cells.style('background-color', function(d) {
                return bilateralColor(d.difference);
            });

            measure_name.style('background-color', function() {
                return 'white';
            });
        }else{
            cells.style('background-color', function(d) {
                if (d.format === 'percent') {
                    return singleNew(d.count);
                } else if (d.format === 'sessions') {
                    return singleNew(d.count / 100000);
                } else if (d.name === 'per active session'){
                    return singleNew(d.count * 10 - 10);
                } else if (d.name === 'per overall session') {
                    return singleNew(d.count * 300);
                }

            });

            measure_name.style('background-color', function() {
                return 'white';
            });

        }
    } else {
        cells = table_row.selectAll('.telemetry-cell')
        .data(function (d) { return d.values; }).enter()
            .append('td').classed('telemetry-cell', true);
        cells.style('width', function (d) { return (66 / d.value_length) + '%'; });
        cells.append('p').text(function (d) { return d.name + ': '; })
            .classed('value-name', true);
        cells.append('p').text(function (d) {
            if (show_value === 'diff') {
                if (d.difference < 0) {
                    return '↓' + percentFormat(-d.difference);
                } else if (d.difference > 0) {
                    return '↑' + percentFormat(d.difference);
                } else {
                    return 'No change.';
                }
            } else if (show_value === 'percent') {
                return percentFormat(d.percent);
            } else if (show_value === 'count') {
                return sessionsFormat(d.count);
            } else if (show_value === 'base_percent') {
                return percentFormat(d.base_percent);
            } else if (show_value === 'base_count') {
                return sessionsFormat(d.base_count);
            } else {
                return '☠';
            }
        }).classed('value-number', true);
        cells.attr('title', function (d) {
            if (diff) {
                return 'Before: ' + percentFormat(d.base_percent) +
                    ' After: ' + percentFormat(d.percent);
            } else {
                return 'Total users: ' + d.count;
            }
        });

        if (diff) {
            cells.style('background-color', function(d) {
                if (d.status === 'old') {
                    return singleOld(d.percent_base);
                } else if (d.status === 'new') {
                    return singleNew(d.percent);
                } else {
                    return bilateralColor(d.difference);
                }
            });

            measure_name.style('background-color', function(d) {
                if (d.status === 'both') {
                    return singleDiff(d.total_diff);
                } else {
                    return 'white';
                }
            });

        }else{
            cells.style('background-color', function(d) { return singleNew(d.percent); });
        }
    }

// POLISH
    measure_name.style('color', function() {
        var bg = $(this).css('background-color');
        return (d3.hsl(bg).l < 0.6) ? 'white' : null;
    });
    cells.style('color', function() {
        var bg = $(this).css('background-color');
        return (d3.hsl(bg).l < 0.6) ? 'white' : null;
    });

    cells.style('padding', function() {
        var width = $(this).width();
        if (width > max_width ) {
            var padding = Math.max((width - max_width) / 3, 5);
            return '0px ' + padding + 'px';
        }
        return null;
    });

}

// Utilities

function smartFormat(value, format) {
    if (format === 'percent') {
        return percentFormat(value);
    } else if (format === 'sessions') {
        return sessionsFormat(value);
    } else {
        return actionsFormat(value, format);
    }
}

function percentFormat(value) {
    var formatter = d3.format('2.2%');
    if (value === 0){
        return '--';
    } else if (value < 0.01) {
        return '<0.01%';
    } else {
        return formatter(value / 100);
    }
}

function sessionsFormat(count){
    var formatter = d3.format(',d');
    if (count === 0){
        return 'No sessions';
    } else if (count === 1) {
        return '1 session';
    } else {
        return formatter(count) + ' sessions';
    }
}

function actionsFormat(count, action){
    var word = action;
    if(count === 1 && singulars[action] !== undefined){
        word = singulars[action];
    }
    var formatter = d3.format(',.3f');
    if (count === 0){
        return 'No ' + word;
    } else if (count === 1) {
        return '1 ' + word;
    } else {
        return formatter(count) + ' ' + word;
    }
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
$('#form-type').change(showHideForm);
$('#form-timeframe').change(showHideVersionWeek);

window.showHideForm = showHideForm;

window.toggleForm = function () {
    $('#data-form').toggle();
};

window.toggleDisplay = function () {
    $('#display-settings').toggle();
};

window.submitForm = function () {
    var new_params = {};
    var selected_type = $('input[type=\'radio\'][name=\'type\']:checked');
    if (selected_type.length > 0) {
        new_params.type = selected_type.val();
    }
    var selected_os = $('input[type=\'radio\'][name=\'OS\']:checked');
    if (selected_os.length > 0) {
        new_params.os = selected_os.val();
    }
    var selected_channel = $('input[type=\'radio\'][name=\'channel\']:checked');
    if (selected_os.length > 0) {
        new_params.channel = selected_channel.val();
    }
    if (new_params.type === 'cs-version') {
        new_params.version = $('select#version').val();
        delete new_params.type;
    } else {
        new_params.version = null;
    }
    if (new_params.type === 'cs-week') {
        new_params.date = $('select#date').val();
        delete new_params.type;
    } else {
        new_params.date = null;
    }
    if (new_params.type === 'week-diff') {
        new_params.date = $('select#date').val();
        new_params.base_date = $('select#base_date').val();
        delete new_params.type;
    } else {
        new_params.base_date = null;
    }
    if (new_params.type === 'version-diff') {
        new_params.version = $('select#version').val();
        new_params.base_version = $('select#base_version').val();
        delete new_params.type;
    } else {
        new_params.base_version = null;
    }
    parameters = _.assign(parameters, new_params);
    parameters = removeDefaultParams(parameters);
    setGlobals();
    var url = document.location.pathname;
    url = url + '?' + $.param(removeDefaultParams(parameters));
    history.pushState(parameters, 'Telemetry UI dashboard', url);
    run();
};

function showErrorMessage (state, text) {
    if (state && (text === undefined || text === '' || text === null)) {
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
    var index = string.search('\\w');
    if (index < 0) { return string; }
    return string.substr(0, index) + string.substr(index, 1).toUpperCase() + string.substr(index + 1);
}


}(jQuery, d3, window, _));
