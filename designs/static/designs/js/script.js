var userMarker = null;
var currentRatio = null;
var originalSize = [];
var img = null;
var offset_top = null;
var total_offset_left = null;
var contaier_offset_left = null;
let comment_box = $("textarea#text");


var onImgLoad = function(selector, callback){
    $(selector).each(function(){
        if (this.complete || /*for IE 10-*/ $(this).height() > 0) {
            callback.apply(this);
        }
        else {
            $(this).on('load', function(){
                callback.apply(this);
            });
        }
    });
};

function showToast(text, color) {
    if (color === "red") {
        color = "#dc3545"; 
    } else if (color === "green") {
        color = "#28a745";
    }
    // Get the snackbar DIV
    var x = document.getElementById("snackbar");
    // Add the "show" class to DIV
    x.style.backgroundColor = color; 
    x.innerText = text;
    x.className = "show";
    // After 3 seconds, remove the show class from DIV
    setTimeout(function(){ x.className = x.className.replace("show", ""); }, 3000);
}

function copyLink() {
    var dummy = document.createElement('input'),
    text = window.location.href;
    document.body.appendChild(dummy);
    dummy.value = text;
    dummy.select();
    document.execCommand('copy');
    document.body.removeChild(dummy);
    showToast("Link copied to clipboard!", "green")
}


Dropzone.options.myAwesomeDropzone = {
    // Prevents Dropzone from uploading dropped files immediately
    autoProcessQueue : false,
    addRemoveLinks: true,
    uploadMultiple: true,
    maxFiles: 10,
    parallelUploads: 10,
    acceptedFiles: "image/*",
    paramName: "asset",
    init : function() {
        var submitButton = document.querySelector("#submit")
        let myDropzone = this;

        submitButton.addEventListener("click", function() {

            myDropzone.processQueue();
            // Tell Dropzone to process all queued files.
        });

        // You might want to show the submit button only when
        // files are dropped here:
        this.on("addedfile", function(file) {
            // Show submit button here and/or inform user to click it.
            // if (currentFile) {
            //     this.removeFile(currentFile);
            // }
            // currentFile = file;
            $("#submit").prop('disabled', false);
        });
        this.on("error", function(file) {
            if (!file.accepted) {
                this.removeFile(file);
                showToast("Invalid file selected. Please select a valid file", "red")
            }
        });
        this.on("sending", function(file, xhr, formData) {
            if ($("input#design_id").val()) {
                formData.append("design", $("input#design_id").val());
            } else if ($("input#project_id").val()) {
                formData.append("project", $("input#project_id").val());
            }
        });
        this.on("success", function(file, response, action) {
            showToast("Uploaded design successfully. Redirecting...", "green")
            response = JSON.parse(response);
            window.setTimeout(function(){ window.location = "/designs/" + response.id; },3000);
        });
    },
    removedfile: function (file) {
        file.previewElement.remove();
        if (!this.files.length) {
            $("#submit").prop('disabled', true);
        }
    }
};

function translateToAbsolute(rx, ry) {
    return [((rx / currentRatio) - total_offset_left + container_offset_left).toFixed(), (ry / currentRatio).toFixed()];
}

function translateToRelative(x, y) {
    return [((x * currentRatio) + total_offset_left - container_offset_left).toFixed(), (y * currentRatio).toFixed()];
}

function newBullseye(rx, ry) {
    let $selector = $(".design-asset");
    let $img = $(".design-asset img");
    console.log("relative: " + rx + " " + ry);
    let abs_x, abs_y;
    [abs_x, abs_y] = translateToAbsolute(rx, ry);
    console.log("absolute: " + abs_x + " " + abs_y);
    console.log($selector.find("#bullseye_new"));
    if (!$selector.find("#bullseye_new").length) {
        console.log("Add new")
        $selector.bullseye({
            id: "_new",
            left: rx-10, // Determines bullseye position from left.
            top: ry-10, // Determines bullseye position from top.
            type: "new",
            orientation: "left", // <a href="https://www.jqueryscript.net/tooltip/">Tooltip</a> orientation
            color: "#00ff00", // Dot and dot animation color. 
            onHoverMarkAsRead: true
        });
        $selector.find("#bullseye_new").on('click', function() {
            comment_box.focus();
        })
    } else {
        comments.splice(0, 1);
    }
    comments.splice(0, 0, {id: "_new", type: "new", coords: [abs_x, abs_y]});
    $selector.find("#bullseye_new").css(
        {
            left: (rx-10)+"px",
            top: (ry-10)+"px",
            position: "absolute"
        }
    );
    $("#formMarkerFalse").hide();
    $("#formMarkerTrue").show();
    comment_box.focus();
}

function removeMarker() {
    let $selector = $(".design-asset");
    if ($selector.find("#bullseye_new").length) {
        $("#bullseye_new").remove();
    }
    if (comments[0].id === "_new") {
        comments.splice(0, 1);
    }
    userMarker = null;
    $("#formMarkerFalse").show();
    $("#formMarkerTrue").hide();
}

onImgLoad("div.design-asset img", function() {
    img = $('div.design-asset img');
    originalSize = [img.prop('naturalWidth'), img.prop('naturalHeight')];
    console.log(originalSize)
    console.log(img.width())
    let ratio = img.width() / originalSize[0];
    currentRatio = ratio.toFixed(2);
    offset_top = img.offset().top
    container_offset_left = $("div.design-asset").offset().left;
    total_offset_left = $("div.design-asset img").offset().left;
    console.log("Set currentRation to " + currentRatio)
    
    img.click(function(e) {
        offset_top = $(this).offset().top;
        offset_left = $("div.design-asset").offset().left;
        rel_x = e.pageX - offset_left;
        rel_y = e.pageY - offset_top;
        console.log("rel_x, rel_y: " + rel_x + " " + rel_y)
        userMarker = translateToAbsolute(rel_x, rel_y);
        newBullseye(rel_x, rel_y);
    });
})

$(document).ready(function() {
    
    $(".djdatetime").each((idx, el) => {
        let $el = $(el);
        let timestamp = $el.text() + "000";
        let date = new Date(Number(timestamp))
        $el.text(date.toLocaleString())
    })

    $("#formMarkerFalse").show();
    $("#formMarkerTrue").hide();

    $("#comment-form").submit(function(event) {
        var input = $("<input>")
               .attr("type", "hidden")
               .attr("name", "x").val(userMarker[0]);
        $('#comment-form').append(input);
        input = $("<input>")
               .attr("type", "hidden")
               .attr("name", "y").val(userMarker[1]);
        $('#comment-form').append(input);
        return true;
    });

    
    onImgLoad(".design-asset img", function() {
        comments.forEach((i) => {
            console.log(i);
            image = image.bullseye({
                id: i.id,
                left: i.coords[0], // Determines bullseye position from left.
                top: i.coords[1], // Determines bullseye position from top.
                heading: i.name, // Heading content
                content: i.text, // Paragraph content
                orientation: "left", // <a href="https://www.jqueryscript.net/tooltip/">Tooltip</a> orientation
                color: "#fzff", // Dot and dot animation color. 
                onHoverMarkAsRead: true
            });
        });
    });
  });

  $(window).resize(function(){
    let ratio = img.width() / originalSize[0];
    currentRatio = ratio.toFixed(2);
    offset_top = img.offset().top
    container_offset_left = $("div.design-asset").offset().left;
    total_offset_left = $("div.design-asset img").offset().left;
    // console.log("resizing")
    // Reposition bullseye
    
    let rel_left, rel_top;
    comments.forEach(comment => {
        console.log(comment)
        let rel = translateToRelative(comment.coords[0], comment.coords[1]);
        console.log(rel);
        rel_left = rel[0];
        rel_top = rel[1];
        console.log(rel_left +" " + rel_top)
        $(".jqBullseye#bullseye"+comment.id).css(
            {
                left: (rel_left-10)+"px",
                top: (rel_top-10)+"px",
                position: "absolute"
            }
        )
    });
});
