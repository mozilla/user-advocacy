function issueTrendLine(config_url, selector, id) {

var 
error_selectors = {
    loading_throbber : '#loading-throbber',
    error_message : '#error-message',
    blank_text : '#blank_text',
    error_text : '#error-text'
},
main_selector = selector,
input_api = 'https://input.mozilla.org/api/v1/feedback/histogram/?date_delta=180d&',
input_link = 'https://input.mozilla.org/en-US/?',
url = config_url,
x_max = new Date(2014,0,0),
x_min = new Date(),
annoteDates = null;
x_min.setDate(x_min.getDate() + 7);

if (id == '' || id === undefined || id === null) {
    id = _.sample("abcdefghijklmnopqrstuvwxyz",5).join('');
}

var xScaleGraphedP = $.Deferred();

var xScale = d3.time.scale();
window.xScale = xScale;

function chart() {
    d3.jsonPromise(url)
        .done(function (data) {
            showErrorMessage(false);
            main = d3.select(main_selector);
            divs = main.selectAll('.trends-' + id).data(data.trends)
                .enter().append('div')
                .classed('row trends-' + id, true);
            title = divs.append('div')
                .classed('col-md-2 trendtitles-' + id, true);
            title.append('div').classed('spacer hidden-sm hidden-xs', true)
                .attr('height', '10%')
            title.append('p').text(function(d) { return d.name})
                .classed('lead', true)
                .style('color', function(d) {return color(d.shortname)})
                .style('margin', '10px 10px 5px 10px');
            title.append('p').text(function(d) { return d.description})
                .classed('trend-description small', true)
                .style('margin', '5px 10px 0 10px');
            chart = divs.append('div').classed('col-md-10 trendgraphs-' + id, true);
            chart.each(render);
            annote = main.insert('div', ":first-child")
                .classed('row annotations-' + id, true);
            annote.append('div')
                .classed('col-md-2', true);
            var annoteChart = annote.append('div')
                .classed('col-md-10 annote-chart-' + id, true);
                
            var annoteChartSvg = annoteChart.append('svg');
            annoteChartSvg.attr('width', $(annoteChart.node()).width());
            annoteChartSvg.attr('height', 130);
            $.when(xScaleGraphedP).done(renderAnnotationsScale);
            divs.on('mouseenter', hoverDiv);
            divs.on('mouseleave', unhoverDiv);
            divs.on('click', sendClick);
            divs.attr('title', function (d) { 
                return "Click to search Input for " + d.name 
            });
        })
        .fail(function(error) {
            var errorText = error.statusText ? error.statusText : "No Response";
            showErrorMessage(true, "No trends to chart. Go about your day. " + errorText);
        });
}

function renderAnnotationsScale() {
    var annoteChart = d3.select('.annote-chart-'+ id +' svg');
    if (x_min > x_max) {
        var x_min_place = x_min;
        x_min = x_max;
        x_max = x_min_place;
        xScale.domain([x_min, x_max]);
    }
    if (annoteDates !== null || annoteDates.length == 0) {
        var eventLines = annoteChart.append('g').classed('annotations', true)
            .selectAll('g')
            .data(annoteDates)
            .enter()
            .append('g');
        eventLines.append('line')
            .attr({
                x1: function(a) {
                    return xScale(a.date);
                },
                y1: 30,
                x2: function(a) {
                    return xScale(a.date);
                },
                y2: 130,
            })
            .attr("stroke-dasharray", "10,5,10,5,5,5");
        eventLines.append('text')
            .text(function(a) {
                return a.title;
            })
            .attr('x', function(a) {
                return xScale(a.date);
            })
            .attr('y', 30)
            .style("transform-origin", function(a) {
                return (xScale(a.date)) + "px 34px";
            })
            .style("transform", "rotate(-90deg)")
            .style("z-index", 2)
            .attr("title", function(a) {
                return a.tooltip
            });
    }
    var xAxis = d3.svg.axis()
        .scale(xScale)
        .orient("top")
        .tickSize(6, 6);
    annoteChart.append("g").attr("class", "x axis");
    x_axis = annoteChart.select(".x.axis")
        .attr("transform", "translate(0," + 30 + ")")
        .call(xAxis)
        .append("text")
        .style("text-anchor", "middle");
    annoteChart.selectAll(".axis path")
        .style("fill", "none")
        .style("stroke", "#000");

    annoteChart.selectAll(".axis line")
        .style("fill", "none")
        .style("stroke", "#000");

}

function render (d, i) {
    var selection = this;
    var lineColor = color(d.shortname);
    d3.jsonPromise(input_api + d.query).done(function (data) {
        data = data.results;
        var X = function(e) { return new Date(e[0])};
        var local_max = X(_.max(data, X));
        var local_min = X(_.min(data, X));
        x_max = (x_max > local_max)?x_max:local_max;
        x_min = (x_min < local_min)?x_min:local_min;
        console.log(x_max, x_min);
        var val_max = _.max(data, function (e) {return e[1]})[1];
        var val_min = _.min(data, function (e) {return e[1]})[1];
        var val_mh = d.baseline;
        if (val_mh === null || val_mh === undefined || val_mh < 1) {
            val_mh = _.sum(data.slice(0,Math.floor(data.length/2)), 
                function (e) {return e[1]});
            val_mh = val_mh/(Math.floor(data.length/2) + 1);
            val_mh = Math.max(val_mh, 1);
        }
        var y_val = function (y) { return (y - val_mh)/val_mh };
        var Y = function (e) { return y_val(e[1]) };
        var y_min = Math.min(Math.floor(y_val(val_min)), -1);
        var y_max = Math.ceil(y_val(val_max));
        var y_height = ( y_max - y_min );
        svg = d3.select(selection).append('svg');
        height = y_height * 50; // Change this to make graphs bigger
        svg.attr("height", height); 
        width = $(selection).width();
        xScale.domain([x_min, x_max]).range([0, width]);
        svg.attr("width", width);
        var yScale = d3.scale.linear();
        yScale.domain([y_min, y_max]).range([height, 0]);
        xScaleGraphedP.resolve();
        var line = d3.svg.line()
            .x(function(e) {
                return xScale(X(e));
            })
            .y(function(e) {
                return yScale(Y(e));
            });
        svg.append("path")
            .classed({"line": true})
            .attr("d", line(data))
            .style("stroke", lineColor)
            .style("stroke-width", 2)
            .style("fill", "none");
        
        svg.insert("line", ":first-child")
            .classed("axis", true)
            .attr({
                x1: 0,
                y1: yScale(-1),
                x2: width,
                y2: yScale(-1),
            }).attr("stroke", "rgb(200,200,200)").attr("stroke-width", 2);
            
        if (annoteDates !== null || annoteDates.length == 0) {
            var eventLines = svg.append('g').classed('annotations', true)
                .selectAll('g')
                .data(annoteDates)
                .enter()
                .append('g');
            eventLines.append('line')
                .attr({
                    x1: function(a) {
                        return xScale(a.date);
                    },
                    y1: 0,
                    x2: function(a) {
                        return xScale(a.date);
                    },
                    y2: height,
                })
                .attr("stroke-dasharray", "10,5,10,5,5,5");
        }

    })
    .fail(function (error) {
        errorText = error.statusText ? error.statusText : "No Response";
        svg = d3.select(selection).append('svg');
        svg.attr("height", 100); 
        width = $(selection).width();
        xScale.domain([x_min, x_max]).range([0, width]);
        svg.attr("width", width);
        svg.append('text').text("No data from server: " +  errorText).attr({
            'x': 30,
            'y': 55
        });
        xScaleGraphedP.resolve();
    })
}

color = d3.scale.ordinal().range([
    'rgb(228,26,28)',
    'rgb(55,126,184)',
    'rgb(77,175,74)',
    'rgb(152,78,163)',
    'rgb(255,127,0)',
    'rgb(255,255,51)',
    'rgb(166,86,40)',
    'rgb(247,129,191)',
    'rgb(153,153,153)'
]);

function showErrorMessage (state, text) {
    if (state && (text === undefined || text == '' || text === null)) {
        console.log("showing error message (blank)");
        $(error_selectors.loading_throbber).hide();
        $(main_selector).hide();
        $(error_selectors.error_message).show();
        $(error_selectors.blank_text).show();
    } else if (state) {
        console.log("showing error message " + text);
        $(error_selectors.loading_throbber).hide();
        $(main_selector).hide();
        $(error_selectors.error_message).show();
        $(error_selectors.blank_text).hide();
        $(error_selectors.error_text).empty().text(text);
    } else {
        $(error_selectors.loading_throbber).hide();
        $(error_selectors.error_message).hide();
        $(main_selector).show();
    }
}

function hoverDiv(d) {
    d3.select(this).select('.trendtitles-' + id).select('p.lead')
    .style('font-weight', 600);
}

function unhoverDiv(d) {
    d3.selectAll('.trendtitles-' + id).selectAll('p.lead')
        .style('font-weight', null)
}

function sendClick(d) {
    window.location.assign(input_link + d.query);
}

chart.loading_throbber = function (_) {
    if (!arguments.length) return error_selectors.loading_throbber;
    error_selectors.loading_throbber = _;
    return chart;
}
chart.error_message = function (_) {
    if (!arguments.length) return error_selectors.error_message;
    error_selectors.error_message = _;
    return chart;
}
chart.blank_text = function (_) {
    if (!arguments.length) return error_selectors.blank_text;
    error_selectors.blank_text = _;
    return chart;
}
chart.error_text = function (_) {
    if (!arguments.length) return error_selectors.error_text;
    error_selectors.error_text = _;
    return chart;
}

chart.annotations = function(_) {
    if (!arguments.length) return annoteDates;
    annoteDates = _;
    return chart;
};

return chart;

}
