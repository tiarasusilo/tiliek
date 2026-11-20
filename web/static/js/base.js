document.addEventListener("DOMContentLoaded", function () {

    /* ==================================================
       1. DATE INFORMATION
    ================================================== */

    const dateElement = document.getElementById("current-date");

    function updateDate() {
        if (!dateElement) return;

        const now = new Date();

        const formattedDate = new Intl.DateTimeFormat("id-ID", {
            weekday: "long",
            day: "numeric",
            month: "long",
            year: "numeric",
            timeZone: "Asia/Jakarta"
        }).format(now);

        dateElement.textContent = formattedDate;
    }

    updateDate();


    /* ==================================================
       2. THEME SETTINGS
    ================================================== */

    const themeButton = document.querySelector(".theme-button");
    const htmlElement = document.documentElement;

    function applyTheme(theme) {
        htmlElement.setAttribute("data-theme", theme);

        if (!themeButton) return;

        if (theme === "dark") {
            themeButton.textContent = "☀";
            themeButton.setAttribute("aria-label", "Aktifkan mode terang");
            themeButton.setAttribute("title", "Aktifkan mode terang");
        } else {
            themeButton.textContent = "☾";
            themeButton.setAttribute("aria-label", "Aktifkan mode gelap");
            themeButton.setAttribute("title", "Aktifkan mode gelap");
        }
    }

    // Ambil tema yang tersimpan
    const savedTheme = localStorage.getItem("tiliek-theme") || "light";

    applyTheme(savedTheme);

    // Ganti tema ketika tombol diklik
    if (themeButton) {
        themeButton.addEventListener("click", function () {
            const currentTheme = htmlElement.getAttribute("data-theme");

            const newTheme = currentTheme === "dark"
                ? "light"
                : "dark";

            localStorage.setItem("tiliek-theme", newTheme);

            applyTheme(newTheme);
        });
    }

});
