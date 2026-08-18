---
title: Search the documentation
eleventyExcludeFromCollections: true
templateEngineOverride: md
head_additions: >
  <link href="/borgmatic/pagefind/pagefind-component-ui.css" rel="stylesheet">
  <script src="/borgmatic/pagefind/pagefind-component-ui.js" type="module"></script>
  <style>
  @media (prefers-color-scheme: light) {
      :root {
          --pf-summary-font-size: 14px;
          --pf-result-title-font-size: 16px;
          --pf-result-excerpt-font-size: 15px;
      }
  }
  @media (prefers-color-scheme: dark) {
      :root {
          --pf-summary-font-size: 14px;
          --pf-result-title-font-size: 16px;
          --pf-result-excerpt-font-size: 15px;
      }
  }

  .pf-result .pf-result-title, .pf-heading-link {
      font-weight: 600 !important;
  }

  .pf-result .pf-result-excerpt mark, .pf-heading-excerpt mark {
      background-color: yellow !important;
  }
  </style>
---

<pagefind-config bundle-path="/borgmatic/pagefind/" base-url="/borgmatic/"></pagefind-config>

<p><pagefind-input placeholder="Search"></pagefind-input></p>
<p><pagefind-summary></pagefind-summary></p>
<p><pagefind-results></pagefind-results></p>

<script type="module">
    const manager = window.PagefindComponents.getInstanceManager();
    const instance = manager.getInstance('default');

    window.addEventListener('DOMContentLoaded', (event) => {
        let url_parameters = new URLSearchParams(window.location.search);
        instance.triggerSearch(url_parameters.get('query'));
    });
</script>
