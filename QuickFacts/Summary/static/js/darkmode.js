document.addEventListener("DOMContentLoaded", function () {
    const toggleButton = document.getElementById('dark-mode-toggle');
    const body = document.body;

    // Check for saved preference in localStorage
    const darkMode = localStorage.getItem('dark-mode');
    if (darkMode === 'enabled') {
        body.classList.add('dark-mode');
    }

    // Toggle dark mode on button click
    toggleButton.addEventListener('click', function () {
        body.classList.toggle('dark-mode');
        
        // Save preference to localStorage
        if (body.classList.contains('dark-mode')) {
            localStorage.setItem('dark-mode', 'enabled');
        } else {
            localStorage.removeItem('dark-mode');
        }
    });
});