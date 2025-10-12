---
title: Search documentation
eleventyExcludeFromCollections: true
---
<link href="/borgmatic/pagefind/pagefind-ui.css" rel="stylesheet">
<script src="/borgmatic/pagefind/pagefind-ui.js"></script>
<div id="search"></div>
<script>
    window.addEventListener('DOMContentLoaded', (event) => {
        let search = new PagefindUI({ element: '#search', showSubResults: true, autofocus: true });
        let url_parameters = new URLSearchParams(window.location.search);
        search.triggerSearch(url_parameters.get('query'));
    });
</script>
