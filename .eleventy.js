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
        replaceLink: function (link, env) {
            if (process.env.NODE_ENV == "production") {
                return link;
            }
            return link.replace('https://torsion.org/borgmatic/', 'http://localhost:8080/');
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

