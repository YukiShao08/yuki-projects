//run in bookmark
Javascript:(function(){
    function extractSearchQuery(url) {
        try {
            const urlObj = new URL(url);
            const query = urlObj.searchParams.get('q');
            return query ? decodeURIComponent(query.replace(/\+/g, ' ')) : null;
        } catch (error) {
            return null;
        }
    }
    var currentQuery = extractSearchQuery(window.location.href);
    if (currentQuery) {
        window.location.href = 'https://search.yahoo.com/search?p=' + encodeURIComponent(currentQuery);
    } else {
        alert('No search query found in this URL.');
    }
})();