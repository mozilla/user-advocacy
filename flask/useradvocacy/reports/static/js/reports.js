function filter_on_hash () {
    var hash = location.hash ? location.hash.substring(1) : "All";
    $("#sidebar-filter .btn").addClass("btn-default").removeClass("btn-primary");
    $("#filter-"+hash).removeClass("btn-default").addClass("btn-primary");
    if (hash !== "All"){
        $(".report-item").fadeOut();
        $(".report-item-"+hash).fadeIn();
        if($(".report-item-"+hash).length == 0) {
            $("#empty-warning").fadeIn();
        } else {
            $("#empty-warning").fadeOut();
        }
    } else {
        $(".report-item").fadeIn();
        $("#empty-warning").fadeOut();
        if($(".report-item").length == 0) {
            $("#empty-warning").fadeIn();
        } else {
            $("#empty-warning").fadeOut();
        }
    }
    $("#filter-menu").text(hash);
    $("#top-filter .dropdown-menu li")
        .addClass("bg-default").removeClass("bg-info");
    $("#fbutton-"+hash).removeClass("bg-default").addClass("bg-info");
    
}

function highlight_filter () {
    unhighlight_filter();
    var hash = $(this).text();
    $(".report-item-"+hash+" .label")
        .removeClass("label-default").addClass("label-primary");
}

function unhighlight_filter () {
    $(".report-item .label").removeClass("label-primary").addClass("label-default");
}

window.onhashchange=filter_on_hash;
$(window).load(filter_on_hash);

$(".side-filter").mouseenter(highlight_filter);
$(".side-filter").mouseout(unhighlight_filter);
