
function configure_image_view(target) {
  document.getElementById("image_view_image").src = target.href;
  document.getElementById("image_view_file_link").href = target.href;
  document.getElementById("image_view_url_link").href = target.dataset.url;
}

function show_image_view_modal(event) {
  event.preventDefault();
  var target = event.target;
  if (target.tagName == "IMG") {
      target = target.parentElement;
  }

  var modal = document.getElementById("image_view_modal");
  modal.classList.remove("hidden");
  modal.style.top = window.scrollY + "px";
  configure_image_view(target);
  document.body.classList.add("lock");
}

function close_image_view_modal() {
  document.getElementById("image_view_modal").classList.add("hidden");
  document.getElementById("image_view_image").src = "";
  document.getElementById("image_view_file_link").href = "#";
  document.getElementById("image_view_url_link").href = "#";
  document.body.classList.remove("lock");
}