;(function($) {
    "use strict";

    var Controller = {
        addFriend: function() {
            var user_id = $(this).data("user-id");

            $.ajax({
                type: "post",
                url: "/profile/friend/request/new",
                data: {
                    user_id: user_id,
                    _xsrf: getCookie("_xsrf")
                },
                dataType: "json",
                success: function(data, textStatus, jqXHR) {
                    if (data.ok) {
                        Messenger().post({
                            message: "好友添加成功!",
                            type: "success",
                            showCloseButton: true,
                            id: 0
                        });
                    } else if (data.error) {
                        Messenger().post({
                            message: data.error,
                            type: "error",
                            showCloseButton: true,
                            id: 0
                        });
                    } else {
                        Messenger().post({
                            message: "好友请求发送成功!",
                            type: "success",
                            showCloseButton: true,
                            id: 0
                        });
                    }
                },
                error: function(jqXHR, textStatus, errorThrown) {
                    Messenger().post({
                        message: "好友请求发送失败!",
                        type: "error",
                        showCloseButton: true,
                        id: 0
                    });
                }
            });
        }
    };

    $(document).ajaxComplete(function(ev, jqXHR, options) {
        if (jqXHR.status == 403 && options.url != "/message/update") {
            window.location.href = "/login";
        }
        return true;
    });

    $(document).ready(function() {
        $(".fancybox-close-button").live("click", function() {
            $.fancybox.close();
        });

        $(".fancybox").fancybox({
            padding: 5,
            maxWidth: 1000,
            prevEffect: 'none',
            nextEffect: 'none',
            helpers: {
                thumbs: {
                    width: 50,
                    height: 50
                }
            }
        });

        Messenger({
            extraClasses: 'messenger-fixed messenger-on-right messenger-on-top',
            messageDefaults: {
                hideAfter: 3
            }
        });

        $(".add-friend-button").live("click", Controller.addFriend);
    });
}(jQuery));
