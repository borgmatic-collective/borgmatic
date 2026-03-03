module.exports = function() {
    return {
        environment: process.env.NODE_ENV || "development",
        port: process.env.PORT || 8080,
        font: process.env.FONT || "custom"
    };
};
