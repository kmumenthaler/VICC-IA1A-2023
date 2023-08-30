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


