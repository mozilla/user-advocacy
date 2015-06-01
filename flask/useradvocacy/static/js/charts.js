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

            if (annoteDates !== null && annoteDates.length > 0) {
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

            if (annoteDates !== null && annoteDates.length > 0) {
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


function inputTrendLines(config_url, selector, id) {

var 
error_selectors = {
    loading_throbber : '#loading-throbber',
    error_message : '#error-message',
    blank_text : '#blank_text',
    error_text : '#error-text'
},
main_selector = selector === undefined ? null : selector,
api_base = 'https://input.mozilla.org/api/v1/feedback/histogram/?',
extra_params = ['date_delta=180d']
link_base = 'https://input.mozilla.org/en-US/?',
url = config_url,
x_max = new Date(2014,0,0),
x_min = new Date(),
height_factor = 50,
annoteDates = null;
x_min.setDate(x_min.getDate() + 7);

if (id == '' || id === undefined || id === null) {
    id = _.sample("abcdefghijklmnopqrstuvwxyz",5).join('');
}

var xScaleGraphedP = $.Deferred();

var xScale = d3.time.scale();

function chart(selection) {
    input_api = api_base + extra_params.join('&') + '&';
    if (main_selector === null) {
        main = selection;
    } else {
        main = d3.select(main_selector);
    }
    d3.jsonPromise(url)
        .done(function (data) {
            showErrorMessage(false);
            divs = main.selectAll('.trends-' + id).data(data.trends)
                .enter().append('div')
                .classed('row trends-' + id, true)
                .style('cursor', 'pointer');
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
        var val_max = _.max(data, function (e) {return e[1]})[1];
        var val_min = _.min(data, function (e) {return e[1]})[1];
        var val_mh = d.baseline;
        if (val_mh === null || val_mh === undefined || val_mh < 1) {
            val_mh = _.sum(data.slice(0,Math.min(Math.floor(data.length/2), 60)), 
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
        height = y_height * height_factor;
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
        svg.attr("height", 2*height_factor); 
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
    d3.select(this).select('.trendgraphs-' + id).selectAll('path')
        .transition()
        .style('stroke-width', 3);
}

function unhoverDiv(d) {
    d3.selectAll('.trendtitles-' + id).selectAll('p.lead')
        .style('font-weight', null);
    d3.selectAll('.trendgraphs-' + id).selectAll('path')
        .transition()
        .style('stroke-width', 2);
}

function sendClick(d) {
    var link_url = d.link || (link_base + d.query);
    window.location.assign(link_url);
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

chart.height_factor = function(_) {
    if (!arguments.length) return height_factor;
    height_factor = _;
    return chart;
};

chart.extra_params = function(_) {
    if (!arguments.length) return extra_params;
    extra_params = _;
    return chart;
};

chart.link_base = function(_) {
    if (!arguments.length) return link_base;
    link_base = _;
    return chart;
};

chart.annotations = function(_) {
    if (!arguments.length) return annoteDates;
    annoteDates = _;
    return chart;
};

return chart;

}
