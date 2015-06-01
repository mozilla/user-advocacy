(function($, d3, window, _) {

var desktop = inputTrendLines('desktop_conf.json')
    .extra_params(['date_delta=180d', 'products=Firefox', 'locales=en-US', 'happy=0']);
var annoter = makeAnnotations();
var noteP = d3.jsonPromise("/data/static/json/desktop-annotations.json")
    .done(function(note_data) {
        notes = annoter(note_data);
        desktop.annotations(notes);
        d3.select('#issue-list').call(desktop);
    })

}(jQuery, d3, window, _));
