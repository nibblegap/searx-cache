$(document).ready(function(){
  function configure_image_view(target, view_url) {
    document.getElementById("image_view_image").src = view_url;
    document.getElementById("image_view_file_link").href = target.href;
    document.getElementById("image_view_url_link").href = target.dataset.url;
  }

  $(".result.result-images").click(function (event) {
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
});
