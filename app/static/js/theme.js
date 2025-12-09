document.addEventListener("DOMContentLoaded", () => {

    const toggle = document.getElementById("theme-toggle");
    const themeLabel = document.getElementById("theme-label");
    const html = document.documentElement;
    
    // debug output
    console.log("theme.js loaded", {toggle, themeLabel});

    // check stored theme preference
    const storedTheme = localStorage.getItem("theme");
    if(storedTheme === "dark"){
        html.classList.add("dark");
        if (toggle) toggle.checked = true;
        if (themeLabel) themeLabel.textContent = "Dark Mode";
    } else {
        html.classList.remove("dark");
        if (toggle) toggle.checked = false;
        if (themeLabel) themeLabel.textContent = "Light Mode";
    }


    if (toggle) {
        toggle.addEventListener("change", () => {
            const darkMode = toggle.checked;
            // update dark class on <html>
            html.classList.toggle("dark", darkMode);
            // save the new preference in LocalStorage
            localStorage.setItem("theme", darkMode ? "dark" : "light");
            // update the label text accordingly
            if (themeLabel) themeLabel.textContent = darkMode ? "Dark Mode" : "Light Mode";
            console.log("Theme changed to: ", localStorage.getItem("theme"));
        });
    }

});