;(function($) {
    "use strict";

    var Controller = {
        setProfileCover: function() {
            var profile_cover_id = $(this).data("extra-profile-cover-id");

            $.ajax({
                type: "post",
                url: "/setting/profile/cover/set",
                data: {
                    profile_cover_id: profile_cover_id,
                    _xsrf: getCookie("_xsrf")
                },
                dataType: "json",
                success: function() {
                    $(".choosen-as-profile-cover").hide();
                    $("#profile-cover-" + profile_cover_id).show();

                    Messenger().post({
                        id: 0,
                        message: "设置成功!",
                        showCloseButton: true,
                        type: "success"
                    });
                },
                error: function() {
                    Messenger().post({
                        id: 0,
                        message: "设置失败!",
                        showCloseButton: true,
                        type: "error"
                    });
                }
            });
        }
    };

    $(document).ready(function() {
        $(".setting-profile-cover").click(Controller.setProfileCover);

        $("#fileupload").fileupload({
            url: "/setting/profile/cover/custom",
            type: "POST",
            dataType: 'json',
            add: function(e, data) {
                $.each(data.files, function(index, file) {
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

                data.formData = [
                    {
                        name: "_xsrf",
                        value: getCookie("_xsrf")
                    }
                ];

                data.submit().success(function() {
                    $(".choosen-as-profile-cover").hide();
                    Messenger().post({
                        id: 0,
                        message: "设置成功!",
                        showCloseButton: true,
                        type: "success"
                    })
                }).error(function() {
                    Messenger().post({
                        id: 0,
                        message: "设置失败!",
                        showCloseButton: true,
                        type: "error"
                    });
                });
            },
        });
    });
}(jQuery));

