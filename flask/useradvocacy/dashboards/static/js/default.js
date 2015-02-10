$('section.expand').not('.content > section.expand').each(function (index, item) {
    var id = "expand-" + index;
    $(item)
    .attr("id", id)
    .before('<div class="expander"><div class="expandtext closed" data-toggleid="'+id+'"></div><div class="expandmarker closed" data-toggleid="'+id+'"></div></div>')
    .slideUp(200);
});

$('.content > section.expand').each(function (index, item) {
    var id = "expand-section-" + index;
    $(item)
    .attr("id", id)
    .before('<div class="section-expander closed" data-toggleid="'+id+'"><div class=" session-expandtext closed" data-toggleid="'+id+'"><div/></div>')
    .slideUp(200);
});

$(".expandmarker,.expandtext,.section-expander").each(function (index, item) {
    $(item).click(function () {
        var id = $(item).attr("data-toggleid");
        var selector = '[data-toggleid="'+id+'"]';
        $(selector).toggleClass('open').toggleClass('closed');
        $( "#"+id ).slideToggle(200, 'swing');
    })
});
