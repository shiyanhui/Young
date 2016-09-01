;(function($) {
    "use strict";

    var Controller = {
        resetPassword: function() {
            var password = $('input[name="password"]').val();

            if(is_null(password)){
                Messenger().post({
                    id: 0,
                    message: "请输入密码!",
                    showCloseButton: true,
                    type: "error"
                });
                return;
            }

            if(!/[-\da-zA-Z`=\\\[\];',.\/~!@#$%^&*()_+|{}:"<>?]{6,20}/g.test(
                password)) {

                Messenger().post({
                    id: 0,
                    message: "密码格式不正确! 密码必须为长度至少为6的字母、数字或者\
                              非空白字符的组合!",
                    showCloseButton: true,
                    type: "error"
                });
                return;
            }

            $.ajax({
                url: "/password/reset",
                type: "POST",
                dataType: "json",
                data: {
                    password: password,
                    _xsrf: getCookie("_xsrf")
                },
                success: function(data, textStatus, jqXHR){
                    $("#submit-password-button").unbind("click");

                    var message = '\
                        <div style="width: 400px; height: 300px;"> \
                            <div style="text-align: center; padding-top: 50px">\
                                <div>密码重设成功!</div> \
                                <div style="margin-top: 10px">\
                                    <span id="seconds" class="red-color" \
                                        style="font-size: 15px">\
                                    </span> 秒后将会跳转到 \
                                    <a href="/login">登录界面</a>\
                                </div> \
                            </div> \
                        </div>';

                    $.fancybox({
                        padding: 0,
                        modal: true,
                        topRatio: 0.3,
                        scrolling: "no",
                        type: "iframe",
                        content: message,
                        afterShow: function(){
                            var seconds = 10;
                            function count(){
                                if(seconds > 0){
                                    $("#seconds").html(seconds);
                                    seconds = seconds - 1;
                                    setTimeout(count, 1000);
                                }
                                else{
                                    window.location.href="/login"
                                }
                            }
                            count();
                        }
                    })
                },
                error: function(jqXHR , textStatus , errorThrown){
                    Messenger().post({
                        id: 0,
                        message: "密码重设失败!",
                        showCloseButton: true,
                        type: "error"
                    })
                }
            });
        }
    };

    $(document).ready(function() {
        $("#submit-password-button").live('click', Controller.resetPassword);
    });
}(jQuery));
