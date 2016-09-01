;(function($) {
    "use strict";

    MathJax.Hub.Config({
        showMathMenu: false,
        showMathMenuMSIE: false,
        messageStyle: "none",
        displayAlign: "left",
        delayStartupUntil: "onload",
        extensions: ["tex2jax.js"],
        jax: ["input/TeX", "output/HTML-CSS"],
        tex2jax: {
            inlineMath: [
                ["$", "$"],
                ["\\(", "\\)"]
            ]
        }
    });

    var Controller = {
        editNodeDescription: function() {
            var node_id = $(this).data("node-id");

            $.ajax({
                type: "post",
                url: "/community/node/description/edit/template",
                data: {
                    node_id: node_id,
                    _xsrf: getCookie("_xsrf"),
                },
                dataType: "html",
                success: function(data, textStatus, jqXHR) {
                    $.fancybox({
                        padding: 0,
                        closeBtn: false,
                        modal: true,
                        scroll: "no",
                        type: "iframe",
                        content: data
                    });
                },
                error: function(jqXHR, textStatus, errorThrown) {
                    Messenger().post({
                        id: 0,
                        message: "加载失败!",
                        showCloseButton: true,
                        type: "error"
                    })
                }
            });
        },
        saveNodeDescription: function() {
            var node_id = $(this).data("node-id");
            var description = $("#node-description-textarea").val();

            if(is_null(description)){
                Messenger().post({
                    id: 0,
                    message: "请输入节点描述!",
                    showCloseButton: true,
                    type: "error"
                })
            }
            else if(description.length > 300){
                Messenger().post({
                    id: 0,
                    message: "节点描述不能超过300字!",
                    showCloseButton: true,
                    type: "error"
                })
            }
            else{
                $.ajax({
                    type: "post",
                    url: "/community/node/description/edit",
                    data: {
                        node_id: node_id,
                        description: description,
                        _xsrf: getCookie("_xsrf"),
                    },
                    dataType: "json",
                    success: function(data, textStatus, jqXHR) {
                        Messenger().post({
                            id: 0,
                            message: "保存成功!",
                            showCloseButton: true,
                            type: "success"
                        })

                        $('#node-description-label').html(data.html);
                        $.fancybox.close();
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
        }
    };

    var Uploader = {
        fileupload_data: null,
        showPreview: function(coords) {
            if(parseInt(coords.w) > 0) {
                $("#x").val(coords.x);
                $("#y").val(coords.y);
                $("#w").val(coords.w);
                $("#h").val(coords.h);
            }
        },
        checkImage: function(files) {
            if (!Uploader.fileupload_data) {
                return;
            }

            $.each(Uploader.fileupload_data.files, function(index, file) {
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
                        }
                        else {
                            $("#node-avatar-preview").append(img.outerHTML);

                            $("#node-avatar-preview > img").Jcrop({
                                setSelect: [0, 0, 200, 200],
                                onChange: Uploader.showPreview,
                                onSelect: Uploader.showPreview,
                                aspectRatio: 1
                            });
                        }
                    },
                    {
                        noRevoke: true
                    }
                );

                if (!loadingImage) {
                    Messenger().post({
                        id: 0,
                        message: "添加图片失败！",
                        showCloseButton: true,
                        type: "error"
                    })
                }
            });
        },
        upload: function() {
            if (!Uploader.fileupload_data) {
                return;
            }

            Uploader.fileupload_data.formData = [
                {
                    name: "node_id",
                    value: $("#topic-sum-label").data("node-id")
                },
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

            Uploader.fileupload_data.submit().success(function() {
                Messenger().post({
                    id: 0,
                    message: "保存成功!",
                    showCloseButton: true,
                    type: "success"
                })
                $.fancybox.close();
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
        $(".node-avatar").hover(function() {
            $(".node-avatar-edit-link").show();
        }, function() {
            $(".node-avatar-edit-link").hide();
        });

        $(".node-description-edit-link").live(
            "click", Controller.editNodeDescription
        );
        $("#save-node-description-button").live(
            "click", Controller.saveNodeDescription
        );

        $("#fileupload").fileupload({
            url: "/community/node/avatar/set",
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
            add: function(e, fileupload_data) {
                $.ajax({
                    type: "post",
                    url: "/community/node/avatar/edit/template",
                    data: {
                        _xsrf: getCookie("_xsrf"),
                    },
                    dataType: "html",
                    success: function(data, textStatus, jqXHR) {
                        $.fancybox({
                            padding: 0,
                            closeBtn: false,
                            modal: true,
                            scroll: "no",
                            type: "iframe",
                            content: data,
                            afterShow: function(){
                                Uploader.fileupload_data = fileupload_data;

                                Uploader.checkImage();
                                $("#save-avatar-button").one(
                                    "click", Uploader.upload
                                );
                            }
                        });
                    },
                    error: function(jqXHR, textStatus, errorThrown) {
                        Messenger().post({
                            id: 0,
                            message: "加载失败!",
                            showCloseButton: true,
                            type: "error"
                        })
                    }
                });
            },
        });
    });
}(jQuery));
