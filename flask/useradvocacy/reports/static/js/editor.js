function submit_preview() {
    var markdown = $('#markdown_field').val();
    var template = $('#template_field').val();
    $('#markdown_preview_field').val(markdown);
    $('#template_preview_field').val(template);
    if($("#preview-box").is(":visible")) {
        var previewscrolloffset = $("#preview-area").contents().scrollTop();
        $('#preview').attr('target', 'preview-frame');
        $("#preview-area").load(function () {
            $("#preview-area").contents().scrollTop(previewscrolloffset);
            $("#preview-area").fadeIn(50);
        });
        $('#preview').submit();
        $("#preview-area").fadeOut(50);
    } else {
        $('#preview').attr('target', '_blank');
        $('#preview').submit();
    }
    
}

function hide_preview() {
    $('#preview-box').hide();
    $('#edit-box').removeClass('col-lg-6');
    $('#edit-box').addClass('col-lg-12');
    $('.preview-show').show();
    $('.preview-noshow').hide();
}

function show_preview() {
    $('#preview-box').show();
    $('#edit-box').removeClass('col-lg-12');
    $('#edit-box').addClass('col-lg-6');
    $('.preview-show').hide();
    $('.preview-noshow').show();
    submit_preview();
}

$('#markdown_field').keypress(function(event) {
    if (!((event.ctrlKey || event.metaKey) && (event.which == 115 || event.which == 83))) {
        return true;
    }
    $("#save_button").click();
    event.preventDefault();
    return false;
});

function getFileList() {
    var file_req = new XMLHttpRequest();
    var path = window.location.pathname;
    path = path.substr(0, path.lastIndexOf('edit'));
    path = path + "listfiles";
    file_req.open("GET", path, true);
    file_req.onload = createDropzoneItems;
    file_req.send();
}

function createDropzoneItems() {
    var filelist = JSON.parse(this.responseText);
    console.log("got filelist", filelist);
    for (var i = 0; i < filelist.length; i++) {
        uploader.emit("addedfile", filelist[i]);
    }
}

function deleteFile(file) { 
    var req = new XMLHttpRequest();
    var path = window.location.pathname;
    path = path.substr(0, path.lastIndexOf('edit'));
    path = path + file.name + "/delete";
    console.log("deleting", path);
    req.open("DELETE", path, true);
    req.send();
}

Dropzone.autoDiscover = false;

var uploader = new Dropzone('div#uploader', { 
    url: "upload",
    paramName: "file",
    maxFilesize: 5,
    uploadMultiple: false,
    addRemoveLinks: true,
    acceptedFiles: ".jpg, .gif, .png, .js, .css, .jpeg, .json, .csv, .tsv, .xml, .pdf, .key",
    createImageThumbnails: false,
    thumbnailHeight: 0,
    init: function() {
        getFileList();
        this.on("removedfile",deleteFile);
    }
});


function check_submit_preview() {
    if($("#preview-box").is(":visible")) {
        submit_preview();
    }
}

function highlight_publish_button() {
    if ($("#publish-button").prop("checked")) {
        $("#publish-button").parent("label").removeClass("btn-default")
            .addClass("btn-primary");
        $("#listed-button").prop("disabled", false);
        $("#listed-button").parent("label").removeClass("disabled");
    } else {
        $("#publish-button").parent("label").removeClass("btn-primary")
            .addClass("btn-default");
        $("#listed-button").prop("disabled", true);
        $("#listed-button").parent("label").addClass("disabled");
    }
}

function highlight_listed_button() {
    if ($("#listed-button").prop("checked")) {
        $("#listed-button").parent("label").removeClass("btn-default")
            .addClass("btn-primary");
    } else {
        $("#listed-button").parent("label").removeClass("btn-primary")
            .addClass("btn-default");
    }
}

debounce_md_update = _.debounce(check_submit_preview, 2000, { 'leading': false, 'trailing': true });

$(window).load(check_submit_preview);
$(window).load(highlight_publish_button);
$(window).load(highlight_listed_button);
$("#publish-button").click(highlight_publish_button);
$("#listed-button").click(highlight_listed_button);

$(".main_md").on("input", debounce_md_update);
