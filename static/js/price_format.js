document.addEventListener("DOMContentLoaded", function () {

    const input = document.getElementById("id_price");

    if (!input) {
        console.log("price field not found");
        return;
    }

    input.setAttribute("type", "text");

    input.addEventListener("input", function () {

        let value = this.value
            .replace(/,/g, "")
            .replace(/\D/g, "");

        this.value = value
            ? Number(value).toLocaleString("en-US")
            : "";

    });


    const form = input.closest("form");

    if (form) {
        form.addEventListener("submit", function () {
            input.value = input.value.replace(/,/g, "");
        });
    }

});