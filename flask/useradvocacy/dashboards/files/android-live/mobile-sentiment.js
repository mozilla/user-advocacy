

var input_by_time_chart = timeScaleLine()
    .y(function(d) {
        return d.value
    })
    .ymax(5)
    .ymin(1)
    .ylabel("Google Play rating")
    .colors(["#B2EAF8", "#00B8E6"])
    .legend(false);

var input_sentiment_chart = sentimentChart()
    .y(function(d) {
        return d.input_volume/d.adis*1000
    })
    .ylabel("Input per thousand ADI")
    .colorfunc(function(d) {
        return d.input_average;
    })
    .colorscale(function(d) {
        return '#bf4040'
    });

var annoter = makeAnnotations();
d3.json("/data/static/json/mobile-annotations.json", function(note_data) {

    notes = annoter(note_data);
    input_by_time_chart.annotations(notes);
    input_sentiment_chart.annotations(notes);

    d3.json("/data/api/v1/stats?measures=play_average&period_delta=90&products=Firefox for Android&channels=all", function(data) {
        final_data = [
            {
                name: "Input rating",
                values: []
            },
            {
                name: "7-day average",
                values: []
            }
        ];
        
        temp_array = [];
        
        for(i = 0; i < data.results.length; i++){
            item = {};
            item.date = data.results[i].date;
            var test_value = data.results[i].play_average;
            if (_.isNumber(test_value) && !_.isNaN(test_value)){
                item.value = test_value;
                final_data[0].values.push(item);
            }
            temp_array.push(item);
            if (temp_array.length >= 7) {
                var sum = _.reduce(temp_array, function (s, n) { 
                    if ('value' in n) {
                        return s + n.value;
                    } else {
                        return s;
                    }
                }, 0);
                var count = _.reduce(temp_array, function (s, n) { 
                    if ('value' in n) {
                        return s + 1;
                    } else {
                        return s;
                    }
                }, 0);
                roll_item = {
                    date: item.date,
                    value: sum/count
                };
                final_data[1].values.push(roll_item);
                temp_array.shift();
            }
        }
        d3.select("#chart1")
            .datum(final_data)
            .call(input_by_time_chart);
    });

    d3.json("/data/api/v1/stats?measures=input_average,input_volume,adis&period_delta=90&products=Firefox for Android&channels=all", function(data) {
        results = data.results;
        d3.select("#chart2")
            .datum(results)
            .call(input_sentiment_chart)
    });

});

var input_by_version_chart = barChart()
    .x(function(d) {
        return d.version;
    })
    .y(function(d) {
        return d.play_average;
    })
    .ymax(5)
    .ymin(1)
    .xtooltip(function(d) {
        return d.version;
    })
    .bartip(function(d) {
        return "Versions: " + d.version + "  Score: " + d.play_average.toFixed(2);
    })
    .xlabel("Version")
    .ylabel("Score")
    .fillcolor("#E68A2E");

d3.json("/data/api/v1/stats?measures=play_average&period=version&period_delta=10&products=Firefox for Android&channels=release", function(data) {
    results = data.results;
    d3.select("#chart3")
        .datum(results)
        .call(input_by_version_chart);
});

var oldFormat = d3.time.format("%Y-%m-%d");
var newFormat = d3.time.format("%-m/%-d");

var sumo_volume_chart = barChart()
    .x(function(d) {
        return newFormat(oldFormat.parse(d.date));
    })
    .y(function(d) {
        return d.sumo_inproduct_visits/1000;
    })
    .xtooltip(function(d) {
        return d.date;
    })
    .bartip(function(d) {
        return "Week of " + d.date + ": " + d.sumo_inproduct_visits + " support visits";
    })
    .ymax(150)
    .xlabel("Week of")
    .ylabel("Support Visits (thousands)")
    .fillcolor("#3366FF")
    .margin({
        top: 20,
        right: 20,
        bottom: 40,
        left: 45
    });

d3.json("/data/api/v1/stats?measures=sumo_inproduct_visits&period=week&products=Firefox for Android&period_delta=12&period=week&channels=all", function(data) {
    results = data.results;
    d3.select("#chart4")
        .datum(results)
        .call(sumo_volume_chart);
});

$(window).resize(_.debounce(function() {
    d3.select("#chart1").call(input_by_time_chart);
    d3.select("#chart2").call(input_sentiment_chart);
    d3.select("#chart3").call(input_by_version_chart);
    d3.select("#chart4").call(sumo_volume_chart);
}, 300));

