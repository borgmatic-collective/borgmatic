const pluginSyntaxHighlight = require("@11ty/eleventy-plugin-syntaxhighlight");
const codeClipboard = require("eleventy-plugin-code-clipboard");
const inclusiveLangPlugin = require("@11ty/eleventy-plugin-inclusive-language");
const navigationPlugin = require("@11ty/eleventy-navigation");

module.exports = function(eleventyConfig) {
    eleventyConfig.addPlugin(pluginSyntaxHighlight);
    eleventyConfig.addPlugin(inclusiveLangPlugin);
    eleventyConfig.addPlugin(navigationPlugin);
    eleventyConfig.addPlugin(codeClipboard);

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
            return link.replace('https://torsion.org/', 'http://localhost:8080/');
        }
    };
    let markdownItAnchorOptions = {
        permalink: markdownItAnchor.permalink.headerLink()
    };

    eleventyConfig.setLibrary(
        "md",
        markdownIt(markdownItOptions)
            .use(markdownItAnchor, markdownItAnchorOptions)
            .use(markdownItReplaceLink)
            .use(codeClipboard.markdownItCopyButton)
    );

    eleventyConfig.addPassthroughCopy({"docs/static": "static"});

    eleventyConfig.setLiquidOptions({dynamicPartials: false});

    return {
        templateFormats: [
          "md",
          "txt"
        ],
    }
};

