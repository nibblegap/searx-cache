/*jshint multistr: true */

function build_video(videos) {
  var i;
  var res = "";

  for (i = 0; i < videos.length; i++) {
    res += "\
      <div class='result result-videos'>\
        <div class='result-content'>\
          <a class='thumbnail' href='" + videos[i].url + "' rel='noreferrer'>\
            <img src='" + videos[i].thumbnail + "' alt=\"" + videos[i].title + "\">\
          </a>\
          <div>\
            <h4 class='result_header'>\
              <a href='" + videos[i].url +"' rel='noreferrer'>" + videos[i].title + "</a>\
            </h4>\
          </div>\
        </div>\
      </div>";
  }

  return res;
}

function build_image(images) {
  var i;
  var res = "";

  for (i = 0; i < images.length; i++) {
    if (images[i].thumbnail_src === undefined) {
        continue;
    }
    res += "\
      <div class='result result-images'>\
        <a href=" + images[i].img_src + "' data-url='" + images[i].url + "' class='img-thumb-link'>\
          <img src='" + images[i].thumbnail_src + "' alt=\"" + images[i].title + "\" title=\"" + images[i].title + "\" class='img-thumbnail'>\
        </a>\
      </div>";
  }

  return res;
}

$(document).ready(function(){
  function configure_image_view(target, view_url) {
    document.getElementById("image_view_image").src = view_url;
    document.getElementById("image_view_file_link").href = target.href;
    document.getElementById("image_view_url_link").href = target.dataset.url;
  }

  $("#results").on("click", ".result.result-images", function (event) {
    event.preventDefault();
    var target = event.target;
    var view_url = target.src;
    if (target.tagName == "IMG") {
        target = target.parentElement;
    }

    var modal = document.getElementById("image_view_modal");
    modal.classList.remove("hidden");
    modal.style.top = window.scrollY + "px";
    configure_image_view(target, view_url);
    document.body.classList.add("lock");
  });

  $("#close_image_view_modal").click(function () {
    document.getElementById("image_view_modal").classList.add("hidden");
    document.getElementById("image_view_image").src = "";
    document.getElementById("image_view_file_link").href = "#";
    document.getElementById("image_view_url_link").href = "#";
    document.body.classList.remove("lock");
  });

  if ($("#results").has(".first-page-media-results").length) {
    var headers = {"headers": { "Content-Type": "application/json"}};
    var query_params = $.param({
      "format": "json",
      "q": $("#q").attr("value"),
      "language": $("select[name='language']").find('option:selected').attr("value"),
      "time_range": $("select[name='time_range']").find('option:selected').attr("value")
    });

    fetch(window.location.origin + "/search?categories=images&" + query_params, {"headers": headers})
      .then(function(r) { return r.json(); })
      .then(function(data) {
        if (data.results) {
          $("#default_images_container").append(build_image(data.results.slice(0, 5)));
        }
      });

    fetch(window.location.origin + "/search?categories=videos&" + query_params, {"headers": headers})
      .then(function(r) { return r.json(); })
      .then(function(data) {
        if (data.results) {
          $(".videos-gallery").append(build_video(data.results.slice(0, 2)));
        }
      });
  }
});
