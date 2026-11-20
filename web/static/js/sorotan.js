/* ==================================================
   TILIEK
   HALAMAN SOROTAN
================================================== */


/* ==================================================
   1. CAROUSEL OTOMATIS
================================================== */

(function () {
    "use strict";

    // Ubah angka ini untuk mengatur lama tiap slide (milidetik)
    var DURASI_SLIDE = 3000;

    var carousel = document.querySelector("[data-carousel]");
    if (!carousel) return;

    var track = carousel.querySelector("[data-carousel-track]");
    var slides = carousel.querySelectorAll(".highlight-slide");
    var indicators = carousel.querySelectorAll(".indicator");
    var counter = carousel.querySelector("[data-current-slide]");
    var btnPrev = carousel.querySelector("[data-prev-slide]");
    var btnNext = carousel.querySelector("[data-next-slide]");

    var total = slides.length;
    var current = 0;
    var timer = null;
    var dijeda = false;

    var kurangiGerak = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    // Samakan durasi animasi indikator dengan durasi slide
    carousel.style.setProperty("--durasi-slide", DURASI_SLIDE + "ms");


    /* ---------- Tampilkan slide ---------- */

    function tampilkan(index) {
        current = (index + total) % total;

        track.style.transform = "translateX(-" + current * 100 + "%)";

        indicators.forEach(function (el, i) {
            el.classList.remove("active");

            if (i === current) {
                // Paksa reflow supaya animasi isian mulai dari awal
                void el.offsetWidth;
                el.classList.add("active");
            }
        });

        if (counter) {
            counter.textContent = String(current + 1).padStart(2, "0");
        }
    }


    /* ---------- Autoplay ---------- */

    function mulaiAutoplay() {
        if (kurangiGerak) return;

        hentikanAutoplay();
        timer = setInterval(function () {
            tampilkan(current + 1);
        }, DURASI_SLIDE);
    }

    function hentikanAutoplay() {
        if (timer) {
            clearInterval(timer);
            timer = null;
        }
    }

    // Jeda saat pengunjung mengarahkan kursor atau fokus ke carousel.
    // Saat dilanjutkan, hitungan dimulai ulang dari awal.
    function jeda() {
        dijeda = true;
        carousel.classList.add("is-paused");
        hentikanAutoplay();
    }

    function lanjut() {
        dijeda = false;
        carousel.classList.remove("is-paused");

        // Mulai ulang isian indikator agar sinkron dengan timer baru
        tampilkan(current);
        mulaiAutoplay();
    }

    // Setelah klik manual: pindah slide lalu atur ulang timer
    function pindahManual(index) {
        tampilkan(index);

        if (!dijeda) mulaiAutoplay();
    }


    /* ---------- Event ---------- */

    if (btnPrev) {
        btnPrev.addEventListener("click", function () {
            pindahManual(current - 1);
        });
    }

    if (btnNext) {
        btnNext.addEventListener("click", function () {
            pindahManual(current + 1);
        });
    }

    indicators.forEach(function (el) {
        el.addEventListener("click", function () {
            pindahManual(parseInt(el.getAttribute("data-slide-to"), 10));
        });
    });

    carousel.addEventListener("mouseenter", jeda);
    carousel.addEventListener("mouseleave", lanjut);
    carousel.addEventListener("focusin", jeda);
    carousel.addEventListener("focusout", lanjut);

    // Hentikan saat tab tidak aktif, lanjut saat kembali
    document.addEventListener("visibilitychange", function () {
        if (document.hidden) {
            hentikanAutoplay();
        } else if (!dijeda) {
            lanjut();
        }
    });

    // Geser dengan jari (mobile)
    var awalX = null;

    carousel.addEventListener("touchstart", function (e) {
        awalX = e.touches[0].clientX;
    }, { passive: true });

    carousel.addEventListener("touchend", function (e) {
        if (awalX === null) return;

        var selisih = e.changedTouches[0].clientX - awalX;
        awalX = null;

        if (Math.abs(selisih) > 50) {
            pindahManual(selisih < 0 ? current + 1 : current - 1);
        }
    }, { passive: true });


    /* ---------- Mulai ---------- */

    if (kurangiGerak) {
        carousel.classList.add("no-autoplay");
    }

    tampilkan(0);
    mulaiAutoplay();
})();


/* ==================================================
   2. GRAFIK AKTIVITAS BERITA
================================================== */

document.addEventListener("DOMContentLoaded", function () {
    const canvas = document.getElementById("newsActivityChart");

    if (!canvas || typeof Chart === "undefined") return;

    const labels = JSON.parse(canvas.dataset.labels);
    const values = JSON.parse(canvas.dataset.values);

    new Chart(canvas, {
        type: "line",

        data: {
            labels: labels,

            datasets: [{
                label: "Jumlah Berita",
                data: values,

                borderColor: "#D7261E",
                backgroundColor: "rgba(215, 38, 30, 0.08)",

                borderWidth: 2,
                pointRadius: 3,
                pointHoverRadius: 5,

                pointBackgroundColor: "#D7261E",
                pointBorderColor: "#FFFFFF",
                pointBorderWidth: 2,

                fill: true,
                tension: 0.35
            }]
        },

        options: {
            responsive: true,
            maintainAspectRatio: false,

            interaction: {
                intersect: false,
                mode: "index"
            },

            plugins: {
                legend: {
                    display: false
                },

                tooltip: {
                    backgroundColor: "#14213D",
                    padding: 12,
                    displayColors: false,

                    callbacks: {
                        label: function (context) {
                            return context.parsed.y + " berita";
                        }
                    }
                }
            },

            scales: {
                x: {
                    grid: {
                        display: false
                    },

                    ticks: {
                        color: "#747B88",
                        maxTicksLimit: 10
                    },

                    border: {
                        display: false
                    }
                },

                y: {
                    beginAtZero: true,

                    ticks: {
                        precision: 0,
                        color: "#747B88"
                    },

                    grid: {
                        color: "#E8E8E8"
                    },

                    border: {
                        display: false
                    }
                }
            }
        }
    });
});


/* ==================================================
   3. GRAFIK ISU YANG MENONJOL (BATANG HORIZONTAL)
================================================== */

document.addEventListener("DOMContentLoaded", function () {
    const canvas = document.getElementById("issueChart");

    if (!canvas || typeof Chart === "undefined") return;

    const labels = JSON.parse(canvas.dataset.labels);
    const values = JSON.parse(canvas.dataset.values);

    // Tambah nomor urut, sekaligus membedakan topik yang namanya sama
    const labelBernomor = labels.map(function (nama, i) {
        return String(i + 1).padStart(2, "0") + "  " + nama;
    });

    const fontJudul =
        getComputedStyle(document.documentElement)
            .getPropertyValue("--font-heading").trim() || "serif";

    // Menampilkan angka jumlah berita di ujung tiap batang
    const labelNilai = {
        id: "labelNilai",

        afterDatasetsDraw: function (chart) {
            const ctx = chart.ctx;

            ctx.save();
            ctx.font = "600 12px sans-serif";
            ctx.fillStyle = "#14213D";
            ctx.textBaseline = "middle";

            chart.getDatasetMeta(0).data.forEach(function (bar, i) {
                ctx.fillText(chart.data.datasets[0].data[i], bar.x + 8, bar.y);
            });

            ctx.restore();
        }
    };

    new Chart(canvas, {
        type: "bar",

        data: {
            labels: labelBernomor,

            datasets: [{
                label: "Jumlah Berita",
                data: values,

                backgroundColor: "#D7261E",
                hoverBackgroundColor: "#14213D",

                borderWidth: 0,
                borderRadius: 0,
                barPercentage: 0.62,
                categoryPercentage: 0.9
            }]
        },

        options: {
            indexAxis: "y",
            responsive: true,
            maintainAspectRatio: false,

            plugins: {
                legend: {
                    display: false
                },

                tooltip: {
                    backgroundColor: "#14213D",
                    padding: 12,
                    displayColors: false,

                    callbacks: {
                        label: function (context) {
                            return context.parsed.x + " berita";
                        }
                    }
                }
            },

            scales: {
                x: {
                    beginAtZero: true,
                    grace: "8%",

                    ticks: {
                        precision: 0,
                        color: "#747B88"
                    },

                    grid: {
                        color: "#E8E8E8"
                    },

                    border: {
                        display: false
                    }
                },

                y: {
                    grid: {
                        display: false
                    },

                    ticks: {
                        color: "#14213D",
                        font: {
                            family: fontJudul,
                            size: 14,
                            weight: "700"
                        }
                    },

                    border: {
                        display: false
                    }
                }
            }
        },

        plugins: [labelNilai]
    });
});