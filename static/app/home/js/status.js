;(function($) {
    "use strict";

    function left(content) {
        var number = content.length;
        var regex = new RegExp("@[^@\\d\\(\\)]+\\([0-9a-f]{24}\\)", "gm");
        var result = content.match(regex);
        if(result){
            number -= 26 * result.length;
        }
        return 140 - number;
    }

    function listen_status_input(content){
        var number = 140;
        if (content){
            number = 140 - font_number(content);
        }

        if(number < 0){
            $("#font-left").html(sprintf(
                '已经超了 <span style="font-size:15px;color:#D32">%d</span> 字',
                -number
            ));
        }
        else{
            $("#font-left").html(sprintf(
                '还可以输入 <span style=" font-size: 15px">%d</span> 字',
                number
            ));
        }
    }

    var Controller = {
        publishStatus: function() {
            if($(this).data("file") != "no") {
                return;
            }

            var content = $("#status-textarea").val();
            var number = left(content);

            if(number >= 140){
                Messenger().post({
                    id: 0,
                    message: "请输入文字内容或者照片",
                    type: "error",
                    showCloseButton: true
                });
                return;
            }

            if(number < 0){
                $("#font-left").html(sprintf(
                    '已经超了 <span style="font-size:15px;color:#D32">%d\
                    </span> 字', -number
                ));
                return;
            }

            if(is_null(content)){
                Messenger().post({
                    id: 0,
                    message: "请输入文字内容或者照片",
                    type: "error",
                    showCloseButton: true
                });
                return;
            }

            $.ajax({
                type: "post",
                url: "/home/status/new",
                data: {
                    content: content,
                    _xsrf: getCookie("_xsrf")
                },
                dataType: "json",
                success: function(data, textStatus, jqXHR) {
                    if(data.error){
                        Messenger().post({
                            id: 0,
                            message: data.error,
                            type: "error",
                            showCloseButton: true
                        });
                    }
                    else{
                        Messenger().post({
                            id: 0,
                            message: "发布成功!",
                            type: "success",
                            showCloseButton: true
                        });
                        $("#status-list").prepend(data.html);
                        $("#status-textarea").val("");
                        $(".status-content img").wrap(function() {
                            return (
                                '<a class="fancybox fancybox.image" href="'
                                + $(this).attr("src")
                                + '"></a>'
                            );
                        });
                    }
                    $("#photo-name").html("");
                },
                error: function(jqXHR, textStatus, errorThrown) {
                    Messenger().post({
                        id: 0,
                        message: "发布失败!",
                        type: "error",
                        showCloseButton: true
                    });
                }
            });
        },
        loadMoreStatus: function() {
            var _this = $(this);
            var page = _this.data("page");

            $.ajax({
                type: "post",
                url: "/home/status/more",
                data: {
                    page: page,
                    _xsrf: getCookie("_xsrf")
                },
                dataType: "json",
                beforeSend: function(jqXHR){
                    _this.html("正在加载中...");
                },
                complete: function(jqXHR, textStatus){
                    _this.html("加载更多");
                },
                success: function(data, textStatus, jqXHR) {
                    if(!is_null(data.html)){
                        $("#status-list").append(data.html);
                        _this.data('page', data.page);
                    }
                    else{
                        _this.hide();
                    }
                },
                error: function(jqXHR, textStatus, errorThrown) {
                    Messenger().post({
                        id: 0,
                        message: "加载失败",
                        showCloseButton: true,
                        type: "error"
                    })
                }
            });
        }
    };

    var Uploader = {
        data: null,
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
                        }
                        else {
                            $("#publish-status-button").data("file", "yes");
                            $("#photo-name").html(Uploader.data.files[0].name);
                        }
                    },
                    {
                        boxWidth: 400,
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
            if (!Uploader.data) {
                return;
            }

            Uploader.data.context = $("#publish-status-button").one(
                "click", function(){

                if(Uploader.data.files){
                    var content = $("#status-textarea").val();
                    var number = left(content);

                    if(number < 0){
                        $("#font-left").html(sprintf(
                            '已经超了 <span style="font-size:15px;\
                            color:#D32">%d</span> 字', -number
                        ));
                    }
                    else{
                        if(is_null(content)){
                            content = "";
                        }

                        Uploader.data.context.text("发布中...")
                        Uploader.data.formData = [
                            {
                                name: "content",
                                value: content
                            },
                            {
                                name: "_xsrf",
                                value: getCookie("_xsrf")
                            }
                        ]
                        Uploader.data.submit();
                        Uploader.data.files = null;
                    }
                }
            });
        }
    };

    $(document).ready(function() {
        if($.browser.msie) {
            $("#status-textarea").get(0).attachEvent(
                    "onpropertychange", function() {
                listen_status_input($(this).val());
            });
        }
        else {
            $("#status-textarea").get(0).addEventListener(
                    "input", function() {
                listen_status_input($(this).val());
            }, false);
        }
        $("#publish-status-button").live("click", Controller.publishStatus);
        $("#load-more-status-button").live("click", Controller.loadMoreStatus);
        $('#file-input').fileupload({
            url: "/home/status/new",
            type: "post",
            dataType: "json",
            add: function (e, data) {
                Uploader.data = data;
                Uploader.checkImage();
                Uploader.upload();
            },
            done: function (e, data) {
                if(data.result.error != undefined){
                    Messenger().post({
                        id: 0,
                        message: data.result.error,
                        type: "error",
                        showCloseButton: true
                    })
                }
                else{
                    Messenger().post({
                        id: 0,
                        message: "发布成功!",
                        type: "success",
                        showCloseButton: true
                    })
                    $("#status-list").prepend(data.result.html);
                    $("#status-textarea").val("");
                    $(".status-content img").wrap(function() {
                        return (
                            '<a class="fancybox fancybox.image" href="'
                            + $(this).attr("src")
                            + '"></a>'
                        );
                    });
                }
                data.context.text("发布");
                $("#photo-name").html("");
                $("#publish-status-button").data("file", "no");
            },
            fail: function(e, data){
                Messenger().post({
                    id: 0,
                    message: "发布失败!",
                    type: "error",
                    showCloseButton: true
                })
            }
        });
    });
}(jQuery));
