;(function($) {
    "use strict";

    var Controller = {
        saveAvatar: function() {
            $.ajax({
                type: "post",
                url: "/activity/new",
                data: {
                    x: $('input[name="x"]').val(),
                    y: $('input[name="y"]').val(),
                    w: $('input[name="w"]').val(),
                    h: $('input[name="h"]').val(),
                    target_width: $('input[name="target-width"]').val(),
                    _xsrf: getCookie("_xsrf"),
                },
                dataType: "json",
                success: function(data, textStatus, jqXHR) {
                    Messenger().post({
                        id: 0,
                        message: "保存成功!",
                        showCloseButton: true,
                        type: "success"
                    });
                },
                error: function(jqXHR, textStatus, errorThrown) {
                    Messenger().post({
                        id: 0,
                        message: "保存失败!",
                        showCloseButton: true,
                        type: "error"
                    })
                }
            });
        }
    };

    var Uploader = {
        data: null,
        showPreview: function(coords) {
            if(parseInt(coords.w) > 0){
                $("#x").val(coords.x);
                $("#y").val(coords.y);
                $("#w").val(coords.w);
                $("#h").val(coords.h);

                var rx = 80 / coords.w;
                var ry = 80 / coords.h;

                $("#setting-avatar-preview img").css({
                    width: Math.round(
                        rx * $("#targer-part > img").width()
                    ) + "px",
                    height: Math.round(
                        rx * $("#targer-part > img").height()
                    ) + "px",
                    marginLeft: "-" + Math.round(rx * coords.x) + "px",
                    marginTop: "-" + Math.round(ry * coords.y) + "px"
                });
            }
        },
        checkImage: function() {
            if (!Uploader.data) {
                return;
            }

            $.each(Uploader.data.files, function(index, file) {
                var loadingImage = window.loadImage(
                    file,
                    function(img) {
                        if (img.type === "error") {
                            Messenger().post({
                                id: 0,
                                message: "请上传图片文件!",
                                showCloseButton: true,
                                type: "error"
                            })
                            return;
                        }

                        $("#targer-part").empty();
                        $("#targer-part").append(img.outerHTML);
                        $("#setting-avatar-preview").empty();
                        $("#setting-avatar-preview").append(img.outerHTML);

                        $("#targer-part > img").Jcrop({
                            setSelect: [0, 0, 200, 200],
                            onChange: Uploader.showPreview,
                            onSelect: Uploader.showPreview,
                            aspectRatio: 1
                        });
                    },
                    {
                        boxWidth: 350,
                        noRevoke: true
                    }
                );

                if (!loadingImage) {
                    Messenger().post({
                        id: 0,
                        message: "添加图片失败！",
                        showCloseButton: true,
                        type: "error"
                    });
                }
            });
        },
        upload: function() {
            Uploader.data.formData = [
                {
                    name: "x",
                    value: $('input[name="x"]').val()
                },
                {
                    name: "y",
                    value: $('input[name="y"]').val()
                },
                {
                    name: "w",
                    value: $('input[name="w"]').val()
                },
                {
                    name: "h",
                    value: $('input[name="h"]').val()
                },
                {
                    name: "target_width",
                    value: $('input[name="target-width"]').val()
                },
                {
                    name: "_xsrf",
                    value: getCookie("_xsrf")
                }
            ];
            Uploader.data.submit().success(function() {
                Messenger().post({
                    id: 0,
                    message: "保存成功!",
                    showCloseButton: true,
                    type: "success"
                })
            }).error(function() {
                Messenger().post({
                    id: 0,
                    message: "保存失败!",
                    showCloseButton: true,
                    type: "error"
                });
            });
        }
    };

    $(document).ready(function() {
        $("#fileupload").fileupload({
            url: "/setting/avatar/set",
            type: "POST",
            dataType: 'json',
            maxFileSize: 10000000,
            fail: function(e, data){
                Messenger().post({
                    id: 0,
                    message: "上传失败!",
                    showCloseButton: true,
                    type: "error"
                })
            },
            add: function(e, data) {
                Uploader.data = data;
                Uploader.checkImage();

                $("#save-avatar-button").unbind("click");
                $("#save-avatar-button").one("click", Uploader.upload);
            },
        });
        $("#save-avatar-button").click(Controller.saveAvatar);
    });
}(jQuery));
