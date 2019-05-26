const pluginSyntaxHighlight = require("@11ty/eleventy-plugin-syntaxhighlight");
const inclusiveLangPlugin = require("@11ty/eleventy-plugin-inclusive-language");

module.exports = function(eleventyConfig) {
    eleventyConfig.addPlugin(pluginSyntaxHighlight);
    eleventyConfig.addPlugin(inclusiveLangPlugin);

    let markdownIt = require("markdown-it");
    let markdownItAnchor = require("markdown-it-anchor");
    let markdownItReplaceLink = require("markdown-it-replace-link");

    let markdownItOptions = {
        html: true,
        breaks: false,
        linkify: true,
        // Replace links to .md files with links to directories. This allows unparsed Markdown links
        // to work on GitHub, while rendered links elsewhere also work.
        replaceLink: function (link, env) {
            return link.replace(/\.md$/, '/');
        }
    };
    let markdownItAnchorOptions = {
        permalink: true,
        permalinkClass: "direct-link"
    };

    eleventyConfig.setLibrary(
        "md",
        markdownIt(markdownItOptions)
            .use(markdownItAnchor, markdownItAnchorOptions)
            .use(markdownItReplaceLink)
    );

    return {
        templateFormats: [
          "md",
          "txt"
        ]
    }
};

