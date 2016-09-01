;(function($) {
    "use strict";

    var Controller = {
        setPassword: function() {
            var current_password = $('input[name="current-password"]').val();
            var new_password = $('input[name="new-password"]').val();
            var repeat_password = $('input[name="repeat-password"]').val();

            if (is_null(current_password)) {
                Messenger().post({
                    id: 0,
                    message: "请输入当前密码!",
                    showCloseButton: true,
                    type: "error"
                });
                return;
            }
            if (is_null(new_password)) {
                Messenger().post({
                    id: 0,
                    message: "请输入新密码!",
                    showCloseButton: true,
                    type: "error"
                });
                return;
            }

            if (is_null(repeat_password)) {
                Messenger().post({
                    id: 0,
                    message: "请重复输入新密码!",
                    showCloseButton: true,
                    type: "error"
                });
                return;
            }

            if (new_password.length < 6 || new_password.length > 20){
                Messenger().post({
                    id: 0,
                    message: "新密码的长度必须在6至20之间!",
                    showCloseButton: true,
                    type: "error"
                });
                return;
            }

            if (new_password!= repeat_password){
                Messenger().post({
                    id: 0,
                    message: "新密码和重复输入密码不一致!",
                    showCloseButton: true,
                    type: "error"
                });
                return;
            }

            $.ajax({
                type: "post",
                url: "/setting/password/set",
                data: {
                    'current_password': current_password,
                    'new_password': new_password,
                    'repeat_password': repeat_password,
                    _xsrf: getCookie("_xsrf")
                },
                dataType: "json",
                success: function(data, textStatus, jqXHR) {
                    if(data.error) {
                        Messenger().post({
                            id: 0,
                            message: data.error,
                            showCloseButton: true,
                            type: "error"
                        });
                        return;
                    }

                    Messenger().post({
                        id: 0,
                        message: "保存成功!",
                        showCloseButton: true,
                        type: "success"
                    });

                    $('input[name="current-password"]').val("");
                    $('input[name="new-password"]').val("");
                    $('input[name="repeat-password"]').val("");
                },
                error: function(jqXHR, textStatus, errorThrown) {
                    Messenger().post({
                        id: 0,
                        message: "保存失败!",
                        showCloseButton: true,
                        type: "error"
                    });
                }
            });
        }
    };

    $(document).ready(function() {
        $("#save-password-button").click(Controller.setPassword);
    });
}(jQuery));
