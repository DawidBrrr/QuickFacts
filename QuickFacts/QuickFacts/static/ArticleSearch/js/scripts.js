document.addEventListener('DOMContentLoaded', () => {
    const searchBar = document.getElementById('search-bar');
    const resultsContainer = document.getElementById('search-results');

    // Event listener for the search input
    searchBar.addEventListener('input', () => {
        const query = searchBar.value.trim();  // Get the query from the search bar

        // Only make a request if there is text in the search bar
        if (query.length > 0) {
            // Make the fetch request to the search endpoint with the query
            fetch(`search_articles/?q=${encodeURIComponent(query)}`)
                .then(response => {
                    // Check if the response is successful
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.json();  // Parse the JSON response
                })
                .then(data => {
                    // Clear previous search results
                    resultsContainer.innerHTML = '';
                    
                    // If there are results, display them
                    if (data.length > 0) {
                        data.forEach(item => {
                            const li = document.createElement('li');
                            li.innerHTML = `<a href="${item.link}">${item.title}</a>`;
                            resultsContainer.appendChild(li);
                        });
                    } else {
                        resultsContainer.innerHTML = '<li>No results found</li>';
                    }
                })
                .catch(error => {
                    console.error('There was a problem with the fetch operation:', error);
                    resultsContainer.innerHTML = '<li>Error fetching data</li>';  // Display an error message
                });
        } else {
            // Clear the results container if the search bar is empty
            resultsContainer.innerHTML = '';
        }
    });
});
