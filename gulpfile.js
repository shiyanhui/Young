const gulp = require("gulp");
const sourcemaps = require("gulp-sourcemaps");
const uglify = require("gulp-uglify");
const concat = require("gulp-concat");
const cleancss = require("gulp-clean-css");
const htmlreplace = require("gulp-html-replace");
const del = require("del");
const rev = require("gulp-rev");
const collector = require("gulp-rev-collector");

gulp.task("clean:dist", function() {
    return del([
        "static/dist"
    ]);
});

gulp.task("clean:templates", function() {
    return del([
        "template"
    ]);
});

gulp.task("copy:css", ["clean:dist"], function() {
    return gulp.src([
        "static/plugin/fancybox/source/*.png",
        "static/plugin/fancybox/source/*.gif",
        "static/plugin/jquery-textext/src/css/close.png",
        "static/plugin/select2/select2x2.png",
    ]).pipe(gulp.dest("static/dist/css"));
});

gulp.task("copy:img", ["clean:dist"], function() {
    return gulp.src([
        "static/plugin/bootstrap-young/img/glyphicons-halflings.png",
    ]).pipe(gulp.dest("static/dist/img"));
});

gulp.task("copy:fonts", ["clean:dist"], function() {
    return gulp.src([
        "static/plugin/font-awesome/fonts/*"
    ])
    .pipe(gulp.dest("static/dist/fonts"));
});

gulp.task("basejs", ["clean:dist"], function() {
    return gulp.src([
        "static/plugin/bootstrap-young/js/bootstrap.js",
        "static/plugin/typeahead.js/dist/typeahead.bundle.min.js",
        "static/plugin/handlebars/handlebars.min.js",
        "static/plugin/messenger/build/js/messenger.min.js",
        "static/plugin/messenger/build/js/messenger-theme-future.js",
        "static/plugin/store-js/store.min.js",
        "static/plugin/store-js/store+json2.min.js",
        "static/plugin/fancybox/source/jquery.fancybox.pack.js",
        "static/plugin/fancybox/source/helpers/jquery.fancybox-buttons.js",
        "static/plugin/fancybox/source/helpers/jquery.fancybox-thumbs.js",
        "static/plugin/fancybox/source/helpers/jquery.fancybox-media.js",
        "static/plugin/sprintf/dist/sprintf.min.js"
    ])
    .pipe(sourcemaps.init())
    .pipe(uglify())
    .pipe(concat("base.min.js"))
    .pipe(sourcemaps.write())
    .pipe(gulp.dest("static/dist/js"));
});

gulp.task("basecss", ["clean:dist"], function() {
    return gulp.src([
        "static/plugin/font-awesome/css/font-awesome.min.css",
        "static/plugin/bootstrap-young/css/bootstrap.css",
        "static/plugin/Buttons/css/buttons.css",
        "static/plugin/messenger/build/css/messenger.css",
        "static/plugin/messenger/build/css/messenger-theme-future.css",
        "static/plugin/fancybox/source/jquery.fancybox.css",
        "static/plugin/fancybox/source/helpers/jquery.fancybox-buttons.css",
        "static/plugin/fancybox/source/helpers/jquery.fancybox-thumbs.css"
    ])
    .pipe(concat("base.min.css"))
    .pipe(cleancss())
    .pipe(gulp.dest("static/dist/css"));
});

gulp.task("appbasejs", ["clean:dist"], function() {
    return gulp.src([
        "static/plugin/jquery-mousewheel/jquery.mousewheel.min.js",
        "static/plugin/node-uuid/uuid.js",
        "static/app/base/js/appbase.js",
        "static/app/message/js/message.js",
        "static/app/search/js/search.js"
    ])
    .pipe(sourcemaps.init())
    .pipe(uglify())
    .pipe(concat("appbase.min.js"))
    .pipe(sourcemaps.write())
    .pipe(gulp.dest("static/dist/js"));
});

gulp.task("bundle:fileupload.js", ["clean:dist"], function() {
    return gulp.src([
        "static/plugin/blueimp-file-upload/js/vendor/jquery.ui.widget.js",
        "static/plugin/blueimp-file-upload/js/jquery.iframe-transport.js",
        "static/plugin/blueimp-file-upload/js/jquery.fileupload.js",
        "static/plugin/blueimp-load-image/js/load-image.all.min.js",
    ])
    .pipe(sourcemaps.init())
    .pipe(uglify())
    .pipe(concat("fileupload.min.js"))
    .pipe(sourcemaps.write())
    .pipe(gulp.dest("static/dist/js"));
});

gulp.task("bundle:jquery-textext.js", ["clean:dist"], function() {
    return gulp.src([
        "static/plugin/jquery-textext/src/js/*.js"
    ])
    .pipe(sourcemaps.init())
    .pipe(uglify())
    .pipe(concat("jquery-textext.min.js"))
    .pipe(sourcemaps.write())
    .pipe(gulp.dest("static/dist/js"));
});

gulp.task("bundle:jquery-textext.css", ["clean:dist"], function() {
    return gulp.src([
        "static/plugin/jquery-textext/src/css/*.css"
    ])
    .pipe(concat("jquery-textext.min.css"))
    .pipe(cleancss())
    .pipe(gulp.dest("static/dist/css"));
});

gulp.task("htmlreplace", ["clean:templates"], function() {
    var tpl = '<script type="text/javascript" src="%s" defer></script>';

    return gulp.src(["app/**/template/*.html", "app/**/template/**/*.html"])
    .pipe(htmlreplace({
        "basecss": "/static/dist/css/base.min.css",
        "basejs": {
            "src": "/static/dist/js/base.min.js",
            "tpl": tpl
        },
        "appbasejs": {
            "src": "/static/dist/js/appbase.min.js",
            "tpl": tpl
        },
        "fileuploadjs": {
            "src": "/static/dist/js/fileupload.min.js",
            "tpl": tpl
        },
        "jquery-textextjs": {
            "src": "/static/dist/js/jquery-textext.min.js",
            "tpl": tpl
        },
        "jquery-textextcss": "/static/dist/css/jquery-textext.min.css",
    }))
    .pipe(gulp.dest("templates"));
});

gulp.task("hash:css", [
        "basecss", "bundle:jquery-textext.css"], function() {

    return gulp.src([
        "static/dist/css/base.min.css",
        "static/dist/css/jquery-textext.min.css",
    ])
    .pipe(rev())
    .pipe(gulp.dest("static/dist/css"))
    .pipe(rev.manifest())
    .pipe(gulp.dest("static/dist/rev/css"));
});

gulp.task("hash:js", [
        "basejs", "appbasejs", "bundle:fileupload.js",
        "bundle:jquery-textext.js"], function() {

    return gulp.src([
        "static/dist/js/base.min.js",
        "static/dist/js/appbase.min.js",
        "static/dist/js/fileupload.min.js",
        "static/dist/js/jquery-textext.min.js",
    ])
    .pipe(rev())
    .pipe(gulp.dest("static/dist/js"))
    .pipe(rev.manifest())
    .pipe(gulp.dest("static/dist/rev/js"));
});

gulp.task("collector:depth1", ["htmlreplace", "hash:css", "hash:js"], function() {
    return gulp.src(["static/dist/rev/**/*.json", "templates/**/template/*.html"])
    .pipe(collector({
        replaceReved: true
    }))
    .pipe(gulp.dest(function(file) {
        return file.base;
    }));
});

gulp.task("collector:depth2", ["htmlreplace", "hash:css", "hash:js"], function() {
    return gulp.src(["static/dist/rev/**/*.json", "templates/**/template/**/*.html"])
    .pipe(collector({
        replaceReved: true
    }))
    .pipe(gulp.dest(function(file) {
        return file.base;
    }));
});

gulp.task("default", [
    "clean:dist", "basejs", "basecss", "appbasejs", "copy:css", "copy:img",
    "copy:fonts", "clean:templates", "htmlreplace", "bundle:fileupload.js",
    "bundle:jquery-textext.js", "bundle:jquery-textext.css",
    "hash:css", "hash:js", "collector:depth1", "collector:depth2"
]);
