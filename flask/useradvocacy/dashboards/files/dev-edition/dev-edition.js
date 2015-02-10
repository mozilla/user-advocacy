(function($, d3, window) {
    var timeformat = d3.time.format("%Y-%0m-%0dT%H:%M:%S");
    var displayformat = d3.time.format("%H:%M %-m/%-d/%Y");
    var url = "https://input.mozilla.org/api/v1/feedback/?products=Firefox%20dev";
    function get_display_data() {
        var nocache = (new Date()).getTime()
        d3.json(url + "&nocache=" + nocache,function (error, json) {
            var responses = json.results;
            // console.log("responses", responses);
            drawTable(responses);
           });
        }

    function drawTable(responses) {
        var selection = d3.select("#feedback");
            $selection = $(selection[0]);
            var selected_data = selection.selectAll(".feedback-item")
                .data(responses, function(d) {return d.id});
            // console.log("selecteddata", selected_data);
            var new_items = selected_data.enter()
                .insert("li", ":first-child")
                .classed("feedback-item", true)
                .classed("feedback-happy",function(d) {return d.happy})
                .classed("feedback-sad",function(d) {return !d.happy})
                .style("opacity", 0);
            // console.log("new items", new_items);
            new_items.append("p")
                .html(function(d){
                    return _.escape(d.description)
                        .replace(new RegExp('\r?\n','g'), '<br />')
                });
            meta = new_items.append("ul")
                .attr("class", "feedback-meta");
            meta.append("li")
                .text(function(d){return d.happy?"Happy":"Sad"});
            meta.append("li")
                .text(function(d){return (d.platform == "")?"Unknown":d.platform});
            meta.append("li")
                .text(function(d){return d.locale});
            meta.append("li")
                .text(function(d){return d.version});
            meta.append("li")
                .text(function(d){return displayformat(timeformat.parse(d.created))});
            meta.append("li")
                .append("a")
                .text("Link to Input")
                .attr("href", function(d) { return "https://input.mozilla.org/dashboard/response/" + d.id});
            new_items.transition().style("opacity", 1);
            var gone_items = selected_data.exit();
            gone_items
                .transition()
                .style("opacity",0)
                .remove();
            selected_data.order();
    }
    
    // code stolen from willkg
    
    var timeoutId = null;
    // Set up to refresh only when the tab is active
    function runIntervals() {
        if (window.blurred) {
            return;
        }
        get_display_data();
        // Once every 5 minutes--run them again.
        timeoutId = setTimeout(runIntervals, 300000);
    }
    
    window.onblur = function() {
        if (timeoutId !== null) {
            clearInterval(timeoutId);
        }
    };
    window.onfocus = function() { runIntervals(); };
    get_display_data();
}(jQuery, d3, window));
