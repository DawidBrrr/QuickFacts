// Darkmode toggle function
document.addEventListener("DOMContentLoaded", function () {
    const toggleButton = document.getElementById('dark-mode-toggle');
    const body = document.body;
    const icon = document.getElementById('mode-icon');
    
    // Define paths for icons
    const sunIconPath = "/static/images/sun-icon.svg";
    const moonIconPath = "/static/images/moon-icon.svg";


    // Check for saved preference in localStorage
    const darkMode = localStorage.getItem('dark-mode');
    if (darkMode === 'enabled') {
        body.classList.add('dark-mode');
        icon.src = moonIconPath; // set icon to moon when dark mode is enabled
    }
    else {
        icon.src = sunIconPath; // set icon to sun when light mode is enabled
    }

    // Toggle dark mode on button click
    toggleButton.addEventListener('click', function () {
        body.classList.toggle('dark-mode');
        
        // Save preference to localStorage
        if (body.classList.contains('dark-mode')) {
            localStorage.setItem('dark-mode', 'enabled');
            icon.src = moonIconPath;
        } else {
            localStorage.removeItem('dark-mode');
            icon.src = sunIconPath;
        }
    });
});