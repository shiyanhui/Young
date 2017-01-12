;(function($) {
    "use strict";

    var resumable;

    var Controller = {
        file: null,
        upload_token: null,
        cancel_upload: function(){
            if (!Controller.upload_token) {
                return;
            }

            $.ajax({
                type: "post",
                url: "/share/new/cancel",
                data: {
                    upload_token: Controller.upload_token,
                    _xsrf: getCookie("_xsrf")
                },
                dataType: "json",
                success: function() {
                    Messenger().post({
                        id: 0,
                        message: "已取消上传！",
                        showCloseButton: true,
                        type: "success"
                    })
                },
                error: function() {
                    Messenger().post({
                        id: 0,
                        message: "取消上传失败！",
                        showCloseButton: true,
                        type: "error"
                    })
                }
            });
        },
        loadShareTemplate: function() {
            $.fancybox.showLoading();

            $.ajax({
                type: "post",
                url: "/share/new/template",
                data: {
                    _xsrf: getCookie("_xsrf"),
                },
                dataType: "html",
                success: function(data) {
                    $.fancybox({
                        padding: 0,
                        closeBtn: true,
                        scrolling: "no",
                        type: "iframe",
                        content: data,
                        topRatio: 0.3,
                        afterShow: function() {
                            $.fancybox.hideLoading();
                            Controller.fileUpload();
                        },
                        beforeClose: function(){
                            if(resumable && resumable.isUploading()){
                                Messenger().post({
                                    id: 0,
                                    message: '文件正在上传中！请先取消上传, \
                                              然后再关闭该窗口!',
                                    showCloseButton: true,
                                    type: "error"
                                });
                                return false;
                            }
                        }
                    });
                },
                error: function() {
                    Messenger().post({
                        id: 0,
                        message: "保存失败!",
                        showCloseButton: true,
                        type: "error"
                    });
                }
            });
        },
        fileUpload: function() {
            $("#fileupload").fileupload({
                url: "/share/new",
                type: "POST",
                dataType: 'json',
                add: function(e, data) {
                    if (!data.files.length) {
                        return
                    }

                    Controller.file = data['files'][0];

                    if(Controller.file.size > 100 * 1024 * 1024){
                        Messenger().post({
                            id: 0,
                            message: '上传文件大小请不要超过100M！',
                            showCloseButton: true,
                            type: "error"
                        });
                        return;
                    }

                    $("#file-name").html(Controller.file.name);

                    $("#submit-file-button").show();
                    $("#submit-file-button").unbind("click");
                    $("#submit-file-button").live(
                        "click", Controller.startUpload
                    );
                },
            });
        },
        startUpload: function() {
            if (!Controller.file) {
                Messenger().post({
                    id: 0,
                    message: '请选择要上传的文件！',
                    showCloseButton: true,
                    type: "error"
                });
                return;
            }

            var filename = $.trim($("#file-name").html());

            if (!filename) {
                Messenger().post({
                    id: 0,
                    message: '文件名称不能为空！',
                    showCloseButton: true,
                    type: "error"
                });
                return;
            }

            if(filename.length > 500){
                Messenger().post({
                    id: 0,
                    message: '文件名称太长了！',
                    showCloseButton: true,
                    type: "error"
                });
                return;
            }

            var title = $('input[name="title"]').val();

            if(is_null(title)){
                Messenger().post({
                    id: 0,
                    message: '标题不能为空！',
                    showCloseButton: true,
                    type: "error"
                });
                return;
            }

            if(font_number(title) > 100){
                Messenger().post({
                    id: 0,
                    message: '标题请不要超过100字！',
                    showCloseButton: true,
                    type: "error"
                });
                return;
            }

            var category = $('select[name="category"]').val();
            if(is_null(category)){
                Messenger().post({
                    id: 0,
                    message: "请选择分享类别!",
                    showCloseButton: true,
                    type: "error"
                });
                return;
            }

            var cost = $('input[name="cost"]').val();
            if(is_null(cost)){
                Messenger().post({
                    id: 0,
                    message: '请输入价格！',
                    showCloseButton: true,
                    type: "error"
                });
                return;
            }

            if(!/^[0-9]+$/.test(cost)){
                Messenger().post({
                    id: 0,
                    message: '价格请输入非负整数！',
                    showCloseButton: true,
                    type: "error"
                });
                return;
            }

            var description = $.trim($('#editor').getHtml());

            Controller.upload_token = uuid.v1();

            if(!(resumable && resumable.isUploading())){
                resumable = new Resumable({
                    target: '/share/new',
                    chunkSize: 10*1024*1024,
                    simultaneousUploads: 4,
                    testChunks: false,
                    query: {
                        upload_token: Controller.upload_token,
                        title: title,
                        description: description,
                        category: category,
                        cost: cost,
                        _xsrf: getCookie("_xsrf")
                    }
                });

                if(!resumable.support) {
                    Messenger().post({
                        id: 0,
                        message: '你的浏览器不支持大文件上传！\
                                  请使用最新的Chrome、FireFox\
                                  等现代浏览器上传！',
                        showCloseButton: true,
                        type: "error"
                    });
                    return;
                }

                $("#cancel-submit-file-button").live(
                    'click', function() {
                    resumable.cancel();
                    $.fancybox.close();
                });

                resumable.addFile(Controller.file);

                resumable.on(
                    'fileAdded', function(file, event) {
                    resumable.upload();
                });

                resumable.on('uploadStart', function(){
                    $("#submit-file-button").html('上传中...');
                    $("#cancel-submit-file-button").show();
                });

                resumable.on('fileProgress', function(file){
                    var progress = Math.floor(
                        resumable.progress()*100
                    );

                    $('#progress .bar').css(
                        'width',
                        progress + '%'
                    );
                    $('#progress .bar').html(progress + '%');
                });

                resumable.on(
                    'fileSuccess', function(file, message){

                    $("#submit-file-button").html('开始上传');
                    $("#cancel-submit-file-button").hide();
                    $("#submit-file-button").hide();

                    Messenger().post({
                        id: 0,
                        message: '上传成功！',
                        showCloseButton: true,
                        type: "success",
                        hideAfter: 3
                    });

                    $.fancybox.close();
                    Controller.file = null;
                });

                resumable.on(
                    'fileError', function(file, message){

                    Messenger().post({
                        id: 0,
                        message: '上传出错！',
                        showCloseButton: true,
                        type: "error",
                        hideAfter: 3
                    });

                    $("#submit-file-button").html('开始上传');
                });

                resumable.on('cancel', function(){
                    Controller.cancel_upload();
                });
            }
        }
    };

    $(document).ready(function(){
        $(".sidebar-pinned").pin({
            containerSelector: ".container",
            padding: {top: 60}
        })

        $(".share-navbar li").live({
            mouseenter: function() {
                $($(this).children()[0]).addClass('red-color-force');
            },
            mouseleave: function() {
                $($(this).children()[0]).removeClass('red-color-force');
            }
        });

        $(".share-navbar li").click(function() {
            window.location.href=$(this).children()[0].href;
        });

        window.onbeforeunload = function(){
            if(resumable && resumable.isUploading()){
                Controller.cancel_upload();
            }
        };

        $("#share-button").click(Controller.loadShareTemplate);
    });
}(jQuery));
