function barChart() {
    var margin = {
            top: 20,
            right: 20,
            bottom: 40,
            left: 30
        },
        givenWidth = null, // default width
        givenHeight = null,
        width = null,
        height = null,
        aspectRatio = 1.3, // not even setable, I'm lazy yo #TODO
        fillColor = "#c13832",
        y_minValue = 0,
        y_maxValue = 100, // default height
        xScale = d3.scale.ordinal(),
        yScale = d3.scale.linear(),
        xAxis = d3.svg.axis().scale(xScale).orient("bottom").tickSize(6, 0),
        yAxis = d3.svg.axis().scale(yScale).orient("left").ticks(10),
        xValue = function(d, i) {
            return i;
        },
        yValue = function(d) {
            return d;
        },
        yLabel = "Percentage",
        xLabel = "Response",
        xTooltip = function(d) {
            return null;
        },
        barTooltip = function(d) {
            return null;
        };

    function chart(selection) {
        $selection = $(selection[0]);
        $selection.empty();
        selection.each(function(data) {
            data = data.map(function(d, i) {
                return {
                    label: xValue.call(data, d, i),
                    value: yValue.call(data, d, i),
                    x_tooltip: xTooltip.call(data, d, i),
                    bar_tooltip: barTooltip.call(data, d, i),
                    original_datum: d
                }
            });

            if (givenWidth === null) {
                width = $selection.width();
            } else {
                width = givenWidth;
            }

            if (givenHeight === null) {
                height = width / aspectRatio;
            } else {
                height = givenHeight;
            }

            xScale.domain(data.map(function(d) {
                    return d.label;
                }))
                .rangeRoundBands([margin.left, width - margin.right], .1, .3);

            yScale.domain([y_minValue, y_maxValue])
                .range([height - margin.bottom, margin.top]);

            var svg = d3.select(this).append('svg');
            var g = svg.append('g');
            g.append("g").attr("class", "x axis");
            g.append("g").attr("class", "y axis");
            g.append("g").attr("class", "bars");

            svg.attr("width", width)
                .attr("height", height);

            g.select(".x.axis")
                .attr("transform", "translate(0," + (height - margin.bottom) + ")")
                .call(xAxis)
                .append("text")
                .style("text-anchor", "middle")
                .text(xLabel)
                .classed("axis-label", true)
                .attr("y", 5)
                .attr("transform", "translate(" + ((margin.left + width - margin.right) / 2) + "," + 30 + ")")

            g.select(".y.axis")
                .attr("transform", "translate(" + margin.left + ",0)")
                .call(yAxis)
                .append("text")
                .classed("axis-label", true)
                .attr("transform", "rotate(-90) translate(" + -margin.top + ",0)")
                .attr("y", 6)
                .attr("dy", ".71em")
                .style("text-anchor", "end")
                .text(yLabel);

            g.select(".bars")
                .selectAll(".bar")
                .data(data)
                .enter().append("rect")
                .attr("class", "bar")
                .attr("x", function(d) {
                    return X(d.label);
                })
                .attr("width", xScale.rangeBand())
                .attr("y", function(d) {
                    return Y(d.value);
                })
                .attr("height", function(d) {
                    return height - margin.bottom - Y(d.value);
                })
                .style("stroke", "#333")
                .style("stroke-width", "1px")
                .style("fill", fillColor)
                .style("fill-opacity", .6)
                .on("mouseenter", hoverBar)
                .on("mouseleave", resetBar)
                .append("svg:title")
                .text(function(d) {
                    return d.bar_tooltip;
                });

            g.selectAll(".axis path")
                .style("fill", "none")
                .style("stroke", "#000");

            g.selectAll(".y.axis line")
                .style("fill", "none")
                .style("stroke", "#000");

            g.selectAll(".x.axis g")
                .data(data)
                .append("svg:title")
                .text(function(d) {
                    return d.x_tooltip;
                });

        });
    }

    function hoverBar(d) {
        d3.select(this)
            .transition()
            .style("fill-opacity", 1)
            .duration(200);
    }

    function resetBar(d) {
        d3.select(this)
            .transition()
            .style("fill-opacity", 0.6)
            .duration(200)
            .delay(50);
    }

    function X(d) {
        return xScale(d);
    }

    function Y(d) {
        return yScale(d);
    }

    chart.margin = function(_) {
        if (!arguments.length) return margin;
        margin = _;
        return chart;
    };

    chart.width = function(_) {
        if (!arguments.length) return width;
        givenWidth = _;
        return chart;
    };

    chart.height = function(_) {
        if (!arguments.length) return height;
        givenHeight = _;
        return chart;
    };

    chart.x = function(_) {
        if (!arguments.length) return xValue;
        xValue = _;
        return chart;
    };

    chart.y = function(_) {
        if (!arguments.length) return yValue;
        yValue = _;
        return chart;
    };

    chart.ymin = function(_) {
        if (!arguments.length) return y_minValue;
        y_minValue = _;
        return chart;
    };

    chart.ymax = function(_) {
        if (!arguments.length) return y_maxValue;
        y_maxValue = _;
        return chart;
    };

    chart.ylabel = function(_) {
        if (!arguments.length) return yLabel;
        yLabel = _;
        return chart;
    };

    chart.xlabel = function(_) {
        if (!arguments.length) return xLabel;
        xLabel = _;
        return chart;
    };

    chart.yaxis = function(_) {
        if (!arguments.length) return yAxis;
        yAxis = _;
        return chart;
    };

    chart.xaxis = function(_) {
        if (!arguments.length) return xAxis;
        xAxis = _;
        return chart;
    };

    chart.fillcolor = function(_) {
        if (!arguments.length) return fillColor;
        fillColor = _;
        return chart;
    };

    chart.xtooltip = function(_) {
        if (!arguments.length) return xTooltip;
        xTooltip = _;
        return chart;
    };


    chart.bartip = function(_) {
        if (!arguments.length) return barTooltip;
        barTooltip = _;
        return chart;
    };

    return chart;
}

function lineChart() {
    var margin = {
            top: 20,
            right: 20,
            bottom: 40,
            left: 30
        },
        givenWidth = null, // default width
        givenHeight = null,
        width = null,
        height = null,
        aspectRatio = 1.3, // not even setable, I'm lazy yo #TODO
        fillColor = "#c13832",
        y_minValue = 0,
        y_maxValue = 100, // default height
        xScale = d3.scale.ordinal(),
        yScale = d3.scale.linear(),
        xAxis = d3.svg.axis().scale(xScale).orient("bottom").tickSize(6, 0),
        yAxis = d3.svg.axis().scale(yScale).orient("left").ticks(10),
        xValue = function(d, i) {
            return i;
        },
        yValue = function(d) {
            return d;
        },
        yLabel = "Percentage",
        xLabel = "Response",
        xTooltip = function(d) {
            return null;
        },
        barTooltip = function(d) {
            return null;
        };

    function chart(selection) {
        $selection = $(selection[0]);
        $selection.empty();
        selection.each(function(data) {
            data = data.map(function(d, i) {
                var output = {
                    x_value: xValue.call(data, d, i),
                    value: yValue.call(data, d, i),
                    x_tooltip: xTooltip.call(data, d, i),
                    bar_tooltip: barTooltip.call(data, d, i),
                    original_datum: d
                };
                output.display = !(isNaN(output.x_value) || isNaN(output.value));
                return output;
            });
            
            // Convert isolated points to points
            
            var points = data.map(function (d, i, arr) {
                if (!d.display) {
                    return undefined;
                }
                if ((i == 0 || !arr[i-1].display) && !arr[i+1].display) {
                    return d;
                } else {
                    return undefined;
                }
            }).filter(function(d) {return d !== undefined });

            if (givenWidth === null) {
                width = $selection.width();
            } else {
                width = givenWidth;
            }

            if (givenHeight === null) {
                height = width / aspectRatio;
            } else {
                height = givenHeight;
            }
            
            if (y_minValue === null) {
                y_minValue === d3.min(data, function (d) { return d.value })
            }
            if (y_maxValue === null) {
                y_maxValue === d3.max(data, function (d) { return d.value })
            }
            
            xScale.domain(data.map(function(d) {
                    return d.x_value;
                }))
                .rangePoints([margin.left, width - margin.right]);

            yScale.domain([y_minValue, y_maxValue])
                .range([height - margin.bottom, margin.top]);

            var svg = d3.select(this).append('svg');
            var g = svg.append('g');
            g.append("g").attr("class", "x axis");
            g.append("g").attr("class", "y axis");
            

            svg.attr("width", width)
                .attr("height", height);

            g.select(".x.axis")
                .attr("transform", "translate(0," + (height - margin.bottom) + ")")
                .call(xAxis)
                .append("text")
                .style("text-anchor", "middle")
                .text(xLabel)
                .classed("axis-label", true)
                .attr("y", 5)
                .attr("transform", "translate(" + ((margin.left + width - margin.right) / 2) + "," + 30 + ")")

            g.select(".y.axis")
                .attr("transform", "translate(" + margin.left + ",0)")
                .call(yAxis)
                .append("text")
                .classed("axis-label", true)
                .attr("transform", "rotate(-90) translate(" + -margin.top + ",0)")
                .attr("y", 6)
                .attr("dy", ".71em")
                .style("text-anchor", "end")
                .text(yLabel);

            var line = d3.svg.line()
                .x(function(d) {
                    return X(d.x_value);
                })
                .y(function(d) {
                    return Y(d.value);
                })
            g.append("path").classed({"line": true, "line-line": true})
                .datum(data)
                .attr("d", function(d) { return line(d); })
                .style("stroke", fillColor)
                .style("stroke-width", 2)
                .style("fill-opacity", 0);
            
            var line_points = g.append("g");
            line_points.selectAll(".line-points")
                .data(points)
                .enter().append("circle")
                .classed({"line": true, "line-points": true})
                .attr("cx", function(d) {
                    return X(d.x_value);
                })
                .attr("cy", function(d) {
                    return Y(d.value);
                })
                .attr("r", 1)
                .style("stroke-width", 2)                
                .style("stroke", function(d) {
                    return fillColor
                })
                .style("fill", function(d) {
                    return fillColor
                })
                .style("fill-opacity", 1)

                
            g.selectAll(".axis path")
                .style("fill", "none")
                .style("stroke", "#000");

            g.selectAll(".y.axis line")
                .style("fill", "none")
                .style("stroke", "#000");

            g.selectAll(".x.axis g")
                .data(data)
                .append("svg:title")
                .text(function(d) {
                    return d.x_tooltip;
                });

        });
    }

    // TODO: Insert items for hover interactions.

    function X(d) {
        return xScale(d);
    }

    function Y(d) {
        return yScale(d);
    }

    chart.margin = function(_) {
        if (!arguments.length) return margin;
        margin = _;
        return chart;
    };

    chart.width = function(_) {
        if (!arguments.length) return width;
        givenWidth = _;
        return chart;
    };

    chart.height = function(_) {
        if (!arguments.length) return height;
        givenHeight = _;
        return chart;
    };

    chart.x = function(_) {
        if (!arguments.length) return xValue;
        xValue = _;
        return chart;
    };

    chart.y = function(_) {
        if (!arguments.length) return yValue;
        yValue = _;
        return chart;
    };

    chart.ymin = function(_) {
        if (!arguments.length) return y_minValue;
        y_minValue = _;
        return chart;
    };

    chart.ymax = function(_) {
        if (!arguments.length) return y_maxValue;
        y_maxValue = _;
        return chart;
    };

    chart.ylabel = function(_) {
        if (!arguments.length) return yLabel;
        yLabel = _;
        return chart;
    };

    chart.xlabel = function(_) {
        if (!arguments.length) return xLabel;
        xLabel = _;
        return chart;
    };

    chart.yaxis = function(_) {
        if (!arguments.length) return yAxis;
        yAxis = _;
        return chart;
    };

    chart.xaxis = function(_) {
        if (!arguments.length) return xAxis;
        xAxis = _;
        return chart;
    };

    chart.fillcolor = function(_) {
        if (!arguments.length) return fillColor;
        fillColor = _;
        return chart;
    };

    chart.xtooltip = function(_) {
        if (!arguments.length) return xTooltip;
        xTooltip = _;
        return chart;
    };

    chart.bartip = function(_) {
        if (!arguments.length) return barTooltip;
        barTooltip = _;
        return chart;
    };

    return chart;
}


function timeScaleLine() {

    var margin = {
            top: 20,
            right: 60,
            bottom: 40,
            left: 30
        },
        marginUserSet = false,
        dateFormat = "%Y-%m-%d",
        givenWidth = null, // null is RESPONSIVE
        givenHeight = null,
        width = null,
        height = null,
        aspectRatio = 1.3,
        y_minValue = 0,
        y_maxValue = null,
        x_minValue = null,
        x_maxValue = null,
        xScale = d3.time.scale(),
        yScale = d3.scale.linear(),
        xAxis = d3.svg.axis()
        .scale(xScale)
        .orient("bottom")
        .tickSize(6, 6),
        yAxis = d3.svg.axis()
        .scale(yScale)
        .orient("left")
        .ticks(10),
        xValue = function(d) {
            return d.date;
        },
        yValue = function(d) {
            return d.value;
        },
        nameLabel = function(d) {
            return d.name;
        },
        valuesAccessor = function(d) {
            return d.values;
        },
        yLabel = "Value",
        xLabel = "Date",
        colorArray = [
            'rgb(27,158,119)',
            'rgb(217,95,2)',
            'rgb(117,112,179)',
            'rgb(231,41,138)',
            'rgb(102,166,30)',
            'rgb(230,171,2)',
            'rgb(166,118,29)',
            'rgb(102,102,102)'
        ],
        legendValue = true,
        annoteMargin = 20,
        annoteDates = null,
        redraw = false;

    var parseDate = d3.time.format(dateFormat).parse;

    function chart(selection) {
        $selection = $(selection[0]);
        $selection.empty();
        selection.each(function(data) {
            if (redraw) {} else {
                var countSeries = 0;
                for (var i = 0; i < data.length; i++) {
                    countSeries++;
                    var series = data[i];
                    if (nameLabel(series) === null) {
                        series.realname = "Series_" + countSeries;
                    } else {
                        series.realname = nameLabel(series);
                    }
                    series.values.forEach(function(d) {
                        d.date = parseDate(xValue(d));
                    });
                    series.points = series.values.map(function(d) {
                            if (d === undefined) {
                                return null;
                            } else if (isNaN(yValue(d))) {
                                return null;
                            } else {
                                return d;
                            }
                        }).map(function (d,i,arr) { 
                        if ((i == 0 || arr[i-1] === null) 
                            && arr[i+1] === null && d !== null) {
                            d.realname = series.realname;
                            return d;
                        } else {
                            return undefined;
                        }
                    }).filter(function(d) {return !(d == undefined || d == null) })
                }
                console.log("points", series.points);

                console.log("data:",data);

                if (legendValue && countSeries > 1) {
                    legendValue = true;
                } else {
                    legendValue = false;
                    if (!marginUserSet) {
                        margin.right = 20;
                    }
                }
                
                if (x_minValue === null) {
                    x_minValue = d3.min(data, function(c) {
                        return d3.min(valuesAccessor(c), function(v) {
                            return v.date;
                        });
                    });
                } else {
                    x_minValue = parseDate(x_minValue);
                }

                if (x_maxValue === null) {
                    x_maxValue = d3.max(data, function(c) {
                        return d3.max(valuesAccessor(c), function(v) {
                            return v.date;
                        });
                    });
                } else {
                    x_maxValue = parseDate(x_maxValue);
                }
                
                if (annoteDates !== null){
                    annoteDates = _.filter(annoteDates, function (i) { 
                        return (i.date <= x_maxValue && i.date >= x_minValue) ;
                    });
                }
                
                if (annoteDates !== null && !marginUserSet && annoteDates.length > 0) {
                    margin.top = margin.top + annoteMargin;
                }

                if (y_minValue === null) {
                    y_minValue = d3.min(data, function(c) {
                        return d3.min(valuesAccessor(c), function(v) {
                            return yValue(v);
                        });
                    });
                }

                if (y_maxValue === null) {
                    y_maxValue = d3.max(data, function(c) {
                        return d3.max(valuesAccessor(c), function(v) {
                            return yValue(v);
                        });
                    });
                    yScale.nice(10);
                }

                xScale.domain([x_minValue, x_maxValue]);

                yScale.domain([y_minValue, y_maxValue]);
                redraw = true;
            }
            if (givenWidth === null) {
                width = $selection.width();
            } else {
                width = givenWidth;
            }

            if (givenHeight === null) {
                height = width / aspectRatio;
            } else {
                height = givenHeight;
            }

            var line = d3.svg.line()
                .x(function(d) {
                    return xScale(d.date);
                })
                .y(function(d) {
                    return yScale(yValue(d));
                })
                .defined(function(d) { return !isNaN(yValue(d)); });

            xAxis.ticks(d3.time.week, 2);
            xAxis.tickFormat(d3.time.format("%-m/%-d"));

            var color = d3.scale.ordinal().range(colorArray)
                .domain(data.map(function(d) {
                    return d.realname;
                }));

            var svg = d3.select(this).append('svg');
            var g = svg.append('g');
            svg.attr("width", width)
                .attr("height", height);

            yScale.range([height - margin.bottom, margin.top]);
            xScale.range([margin.left, width - margin.right]);


            var lines = g.append("g").attr("class", "lines");
            var series = lines.selectAll(".series")
                .data(data)
                .enter().append("g")
                .attr("class", "series");

            series.append("path")
                .classed({"line": true, "line-line": true})
                .attr("d", function(d) {
                    return line(valuesAccessor(d));
                })
                .style("stroke", function(d) {
                    return color(d.realname)
                })
                .style("stroke-width", 2)
                .style("fill", "none")
                .on("mouseenter", boldLine)
                .on("mouseleave", thinLine);

            var line_points = series.append("g");
            line_points.selectAll(".line-points")
                .data(function(d) {
                    return d.points;
                })
                .enter().append("circle")
                .classed({"line": true, "line-points": true})
                .attr("cx", function(d) {
                    return xScale(d.date);
                })
                .attr("cy", function(d) {
                    return yScale(yValue(d));
                })
                .attr("r", 1)
                .style("stroke-width", 2)                
                .style("stroke", function(d) {
                    return color(d.realname)
                })
                .style("fill", function(d) {
                    return color(d.realname)
                })
                .style("fill-opacity", 1)
                .on("mouseenter", boldLine)
                .on("mouseleave", thinLine);

            g.append("g").attr("class", "x axis");
            g.append("g").attr("class", "y axis");

            g.select(".x.axis")
                .attr("transform", "translate(0," + (height - margin.bottom) + ")")
                .call(xAxis)
                .append("text")
                .style("text-anchor", "middle")
                .text(xLabel)
                .classed("axis-label", true)
                .attr("y", 5)
                .attr("transform", "translate(" +
                    ((margin.left + width - margin.right) / 2) + "," + 30 + ")");

            g.select(".y.axis")
                .attr("transform", "translate(" + margin.left + ",0)")
                .call(yAxis)
                .append("text")
                .classed("axis-label", true)
                .attr("transform", "rotate(-90) translate(" + -margin.top + ",0)")
                .attr("y", 6)
                .attr("dy", ".71em")
                .style("text-anchor", "end")
                .text(yLabel);

            g.selectAll(".axis path")
                .style("fill", "none")
                .style("stroke", "#000");

            g.selectAll(".axis line")
                .style("fill", "none")
                .style("stroke", "#000");

            if (annoteDates !== null || annoteDates.length == 0) {
                var eventLines = g.append('g').classed('annotations', true)
                    .selectAll('g')
                    .data(annoteDates)
                    .enter()
                    .append('g');
                
                eventLines.append('line')
                    .attr({
                        x1: function(d) {
                            return xScale(d.date);
                        },
                        y1: 1,
                        x2: function(d) {
                            return xScale(d.date);
                        },
                        y2: height - margin.bottom,
                    })
                    .attr("stroke-dasharray", "10,5,10,5,5,5");
                eventLines.append('text')
                    .text(function(d) {
                        return d.title;
                    })
                    .attr('x', function(d) {
                        return xScale(d.date);
                    })
                    .attr('y', 1)
                    .style("transform-origin", function(d) {
                        return (xScale(d.date)) + "px 4px";
                    })
                    .style("transform", "rotate(-90deg)")
                    .style("z-index", 2)
                    .attr("title", function(d) {
                        return d.tooltip
                    });
            }

            if (legendValue) {
                var legend = svg.append("g")
                    .attr("class", "legend")
                    .attr("transform", "translate(" + (width - margin.right + 5) + ", " + (margin.top + 10) + ")");

                var item = legend.selectAll(".legend-item")
                    .data(data)
                    .enter()
                    .append("g")
                    .attr("class", "legend-item");
                item.append("text")
                    .text(function(d) {
                        return d.realname
                    })
                    .attr("dy", function(d, i) {
                        return i * 2 + "em";
                    })
                    .attr("dx", "1em");

                item.append("circle")
                    .attr("cy", function(d, i) {
                        return (i * 2 - .4) + "em"
                    })
                    .attr("cx", 0)
                    .attr("r", "0.4em")
                    .style("fill", function(d) {
                        return color(d.realname)
                    });

                item.on("mouseenter", boldLine).on("mouseleave", thinLine);
            }

        });
    }

    function boldLine(d) {
        d3.selectAll(".lines .line")
            .each(function(c, i) {
                if (d.realname == c.realname) {
                    d3.select(this)
                        .transition()
                        .style("stroke-width", 4)
                        .duration(200)
                } else {
                    d3.select(this)
                        .transition()
                        .style("stroke-width", 2)
                        .duration(200)
                }
            });
    }

    function thinLine(d) {
        d3.selectAll(".lines .line")
            .transition()
            .style("stroke-width", 2)
            .duration(200);
    }

    function X(d) {
        return xScale(d);
    }

    function Y(d) {
        return yScale(d);
    }

    chart.margin = function(_) {
        if (!arguments.length) return margin;
        margin = _;
        marginUserSet = true;
        return chart;
    };

    chart.width = function(_) {
        if (!arguments.length) return width;
        givenWidth = _;
        return chart;
    };

    chart.height = function(_) {
        if (!arguments.length) return height;
        givenHeight = _;
        return chart;
    };

    chart.x = function(_) {
        if (!arguments.length) return xValue;
        xValue = _;
        return chart;
    };

    chart.y = function(_) {
        if (!arguments.length) return yValue;
        yValue = _;
        return chart;
    };

    chart.ymin = function(_) {
        if (!arguments.length) return y_minValue;
        y_minValue = _;
        return chart;
    };

    chart.ymax = function(_) {
        if (!arguments.length) return y_maxValue;
        y_maxValue = _;
        return chart;
    };

    chart.xmin = function(_) {
        if (!arguments.length) return x_minValue.format(dateFormat);
        x_minValue = _;
        return chart;
    };

    chart.xmax = function(_) {
        if (!arguments.length) return x_maxValue.format(dateFormat);
        x_maxValue = _;
        return chart;
    };

    chart.ylabel = function(_) {
        if (!arguments.length) return yLabel;
        yLabel = _;
        return chart;
    };

    chart.xlabel = function(_) {
        if (!arguments.length) return xLabel;
        xLabel = _;
        return chart;
    };

    chart.yaxis = function(_) {
        if (!arguments.length) return yAxis;
        yAxis = _;
        return chart;
    };

    chart.xaxis = function(_) {
        if (!arguments.length) return xAxis;
        xAxis = _;
        return chart;
    };

    chart.colors = function(_) {
        if (!arguments.length) return colorArray;
        colorArray = _;
        return chart;
    };

    chart.dateformat = function(_) {
        if (!arguments.length) return dateFormat;
        dateFormat = _;
        return chart;
    };

    chart.name = function(_) {
        if (!arguments.length) return nameLabel;
        nameLabel = _;
        return chart;
    };

    chart.values = function(_) {
        if (!arguments.length) return valuesAccessor;
        valuesAccessor = _;
        return chart;
    };

    chart.legend = function(_) {
        if (!arguments.length) return legendValue;
        legendValue = _;
        return chart;
    };

    chart.annotations = function(_) {
        if (!arguments.length) return annoteDates;
        annoteDates = _;
        return chart;
    };
    return chart;
}

function makeAnnotations() {
    var
        dateValue = function(d) {
            return d.date;
        },
        titleValue = function(d) {
            return d.title;
        },
        tooltipValue = function(d) {
            return d.tooltip;
        },
        dateFormat = "%Y-%m-%d";

    var parseDate = d3.time.format(dateFormat).parse;

    function make(data) {
        var output = [];
        for (var i = 0; i < data.length; i++) {
            var item = data[i];
            var newitem = {};
            if (dateValue(item) === null) {
                continue;
            } else {
                newitem.date = parseDate(dateValue(item));
            }
            if (titleValue(item) === null) {
                newitem.title = dateValue(item);
            } else {
                newitem.title = titleValue(item);
            }
            if (tooltipValue(item) === null) {
                newitem.tooltip = "";
            } else {
                newitem.tooltip = tooltipValue(item);
            }
            output.push(newitem);
        }
        return output;
    }

    make.dateformat = function(_) {
        if (!arguments.length) return dateFormat;
        dateFormat = _;
        return make;
    };
    make.date = function(_) {
        if (!arguments.length) return dateValue;
        dateFormat = _;
        return make;
    };
    make.title = function(_) {
        if (!arguments.length) return titleValue;
        dateFormat = _;
        return make;
    };
    make.tooltip = function(_) {
        if (!arguments.length) return tooltipValue;
        dateFormat = _;
        return make;
    };
    return make;
}

function sentimentChart() {
    var margin = {
            top: 20,
            right: 20,
            bottom: 40,
            left: 30
        },
        marginUserSet = false,
        dateFormat = "%Y-%m-%d",
        givenWidth = null, // null is RESPONSIVE
        givenHeight = null,
        width = null,
        height = null,
        aspectRatio = 1.3,
        y_minValue = 0,
        y_maxValue = null,
        x_minValue = null,
        x_maxValue = null,
        xScale = d3.scale.ordinal(),
        xAxisScale = d3.time.scale(),
        yScale = d3.scale.linear(),
        xAxis = d3.svg.axis()
        .scale(xAxisScale)
        .orient("bottom")
        .tickSize(6, 6),
        yAxis = d3.svg.axis()
        .scale(yScale)
        .orient("left")
        .ticks(10),
        xValue = function(d) {
            return d.date;
        },
        yValue = function(d) {
            return d.value;
        },
        colorValue = function(d) {
            return d.color;
        },
        nameLabel = function(d) {
            return d.name;
        },
        valuesAccessor = function(d) {
            return d.values;
        },
        yLabel = "Value",
        xLabel = "Date",
        annoteMargin = 20,
        annoteDates = null,
        redraw = false,
        colorScale = function(d) {
            return d3.interpolateHsl("hsl(0,90%,42%)", "hsl(120,90%,42%)")(d)};

    var parseDate = d3.time.format(dateFormat).parse;

    function chart(selection) {
        $selection = $(selection[0]);
        $selection.empty();
        selection.each(function(data) {
            if (redraw) {} else {
                for (var i = 0; i < data.length; i++) {
                    data[i].date = parseDate(xValue(data[i]));
                }

                if (x_minValue === null) {
                    x_minValue = d3.min(data, function(c) {
                        return c.date;
                    });
                } else {
                    x_minValue = parseDate(x_minValue);
                }

                if (x_maxValue === null) {
                    x_maxValue = d3.max(data, function(c) {
                        return c.date;
                    });
                } else {
                    x_maxValue = parseDate(x_maxValue);
                }
                
                if (annoteDates !== null){
                    annoteDates = _.filter(annoteDates, function (i) { 
                        return (i.date < x_maxValue && i.date > x_minValue) 
                    });
                }

                if (y_minValue === null) {
                    y_minValue = d3.min(data, function(c) {
                        return yValue(c);
                    });
                }

                if (y_maxValue === null) {
                    y_maxValue = d3.max(data, function(c) {
                        return yValue(c);
                    });
                    yScale.nice(10);
                }

                xScale.domain(data.map(function(d) {
                    return d.date;
                }));
                xAxisScale.domain([d3.time.hour.offset(x_minValue, -12), d3.time.hour.offset(x_maxValue, 12)]);
                yScale.domain([y_minValue, y_maxValue]);

                var line = d3.svg.line()
                    .x(function(d) {
                        return xScale(d.date);
                    })
                    .y(function(d) {
                        return yScale(yValue(d));
                    });
                xAxis.ticks(10);
                if (annoteDates !== null && !marginUserSet && annoteDates.length > 0) {
                    margin.top = margin.top + annoteMargin;
                }
                redraw = true;
            }
            if (givenWidth === null) {
                width = $selection.width();
            } else {
                width = givenWidth;
            }

            if (givenHeight === null) {
                height = width / aspectRatio;
            } else {
                height = givenHeight;
            }

            var svg = d3.select(this).append('svg');
            var g = svg.append('g');
            svg.attr("width", width)
                .attr("height", height);

            yScale.range([height - margin.bottom, margin.top]);
            xScale.range([margin.left, width - margin.right]);
            xAxisScale.range([margin.left, width - margin.right]);
            xAxis.ticks(d3.time.week, 2);
            xAxis.tickFormat(d3.time.format("%-m/%-d"));
            xScale.rangeBands([margin.left, width - margin.right], 0, 0);
            
            g.append("g").classed('bars', true).selectAll(".bar")
                .data(data)
                .enter().append("rect")
                .attr("class", "bar")
                .attr("x", function(d) {
                    return xScale(d.date);
                })
                .attr("width", xScale.rangeBand())
                .attr("y", function(d) {
                    return yScale(yValue(d));
                })
                .style("fill", function(d) { return colorScale(colorValue(d))})
                .attr("height", function(d) {
                    return height - yScale(yValue(d)) - margin.bottom;
                });

            g.append("g").attr("class", "x axis");
            g.append("g").attr("class", "y axis");
            
            g.select(".x.axis")
                .attr("transform", "translate(0," + (height - margin.bottom) + ")")
                .call(xAxis)
                .append("text")
                .style("text-anchor", "middle")
                .text(xLabel)
                .classed("axis-label", true)
                .attr("y", 5)
                .attr("transform", "translate(" +
                    ((margin.left + width - margin.right) / 2) + "," + 30 + ")");

            g.select(".y.axis")
                .attr("transform", "translate(" + margin.left + ",0)")
                .call(yAxis)
                .append("text")
                .classed("axis-label", true)
                .attr("transform", "rotate(-90) translate(" + -margin.top + ",0)")
                .attr("y", 6)
                .attr("dy", ".71em")
                .style("text-anchor", "end")
                .text(yLabel);

            g.selectAll(".axis path")
                .style("fill", "none")
                .style("stroke", "#000");

            g.selectAll(".axis line")
                .style("fill", "none")
                .style("stroke", "#000");

            if (annoteDates !== null) {
                var eventLines = g.append('g').classed('annotations', true)
                    .selectAll('g')
                    .data(annoteDates)
                    .enter()
                    .append('g');
                eventLines.append('line')
                    .attr({
                        x1: function(d) {
                            return xScale(d.date);
                        },
                        y1: 1,
                        x2: function(d) {
                            return xScale(d.date);
                        },
                        y2: height - margin.bottom,
                    })
                    .attr("stroke-dasharray", "10,5,10,5,5,5");
                eventLines.append('text')
                    .text(function(d) {
                        return d.title;
                    })
                    .attr('x', function(d) {
                        return xScale(d.date);
                    })
                    .attr('y', 1)
                    .style("transform-origin", function(d) {
                        return (xScale(d.date)) + "px 4px";
                    })
                    .style("transform", "rotate(-90deg)")
                    .style("z-index", 2)
                    .attr("title", function(d) {
                        return d.tooltip
                    });
            }
        });
    }

    function X(d) {
        return xScale(d);
    }

    function Y(d) {
        return yScale(d);
    }

    chart.margin = function(_) {
        if (!arguments.length) return margin;
        margin = _;
        marginUserSet = true;
        return chart;
    };

    chart.width = function(_) {
        if (!arguments.length) return width;
        givenWidth = _;
        return chart;
    };

    chart.height = function(_) {
        if (!arguments.length) return height;
        givenHeight = _;
        return chart;
    };

    chart.x = function(_) {
        if (!arguments.length) return xValue;
        xValue = _;
        return chart;
    };

    chart.y = function(_) {
        if (!arguments.length) return yValue;
        yValue = _;
        return chart;
    };

    chart.ymin = function(_) {
        if (!arguments.length) return y_minValue;
        y_minValue = _;
        return chart;
    };

    chart.ymax = function(_) {
        if (!arguments.length) return y_maxValue;
        y_maxValue = _;
        return chart;
    };

    chart.xmin = function(_) {
        if (!arguments.length) return x_minValue.format(dateFormat);
        x_minValue = _;
        return chart;
    };

    chart.xmax = function(_) {
        if (!arguments.length) return x_maxValue.format(dateFormat);
        x_maxValue = _;
        return chart;
    };

    chart.ylabel = function(_) {
        if (!arguments.length) return yLabel;
        yLabel = _;
        return chart;
    };

    chart.xlabel = function(_) {
        if (!arguments.length) return xLabel;
        xLabel = _;
        return chart;
    };

    chart.yaxis = function(_) {
        if (!arguments.length) return yAxis;
        yAxis = _;
        return chart;
    };

    chart.xaxis = function(_) {
        if (!arguments.length) return xAxis;
        xAxis = _;
        return chart;
    };

    chart.colorfunc = function(_) {
        if (!arguments.length) return colorValue;
        colorValue = _;
        return chart;
    };

    chart.dateformat = function(_) {
        if (!arguments.length) return dateFormat;
        dateFormat = _;
        return chart;
    };

    chart.name = function(_) {
        if (!arguments.length) return nameLabel;
        nameLabel = _;
        return chart;
    };

    chart.values = function(_) {
        if (!arguments.length) return valuesAccessor;
        valuesAccessor = _;
        return chart;
    };
    
    chart.colorscale = function(_) {
        if (!arguments.length) return colorScale;
        colorScale = _;
        return chart;
    };

    chart.legend = function(_) {
        if (!arguments.length) return legendValue;
        legendValue = _;
        return chart;
    };

    chart.annotations = function(_) {
        if (!arguments.length) return annoteDates;
        annoteDates = _;
        return chart;
    };
    return chart;
}
