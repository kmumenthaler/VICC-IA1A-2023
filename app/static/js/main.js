window.addEventListener('load', function() {
    document.body.classList.add('loaded');
});

document.addEventListener("DOMContentLoaded", function() {
    let navbarLinks = document.querySelectorAll(".nav-link");
    let currentPath = window.location.pathname;

    navbarLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.parentElement.classList.add("active-link");
        } else {
            link.parentElement.classList.remove("active-link");
        }
    });
});

function editReview(button) {
    var id = button.getAttribute("data-id");
    // Weiterleitung zur Bearbeitungsseite mit der ID der Rezension
    window.location.href = "/edit-review/" + id;
}

function deleteReview(button) {
    var id = button.getAttribute("data-id");
    var r = confirm("Möchten Sie diese Rezension wirklich löschen?");
    if (r == true) {
        // Sie können hier einen AJAX-Aufruf machen oder den Benutzer zu einer anderen Route weiterleiten,
        // um den Löschvorgang durchzuführen
        window.location.href = "/delete-review/" + id;
    }
}

