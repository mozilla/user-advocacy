(function($, d3, window, _) {


var desktop = issueTrendLine('desktop_conf.json', "#issue-list", "desktop");
var annoter = makeAnnotations();
var noteP = d3.jsonPromise("/data/static/json/desktop-annotations.json")
    .done(function(note_data) {
        notes = annoter(note_data);
        desktop.annotations(notes);
        desktop();
    })

}(jQuery, d3, window, _));
