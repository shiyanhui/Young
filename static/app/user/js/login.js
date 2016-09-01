function enterLogin(e) {
    var key = window.event ? e.keyCode : e.which;
    if (key == 13) {
        login();
    }
}

function login() {
    var email = $.trim($('input[name="email"]').val());
    var password = $('input[name="password"]').val();

    if(is_null(email)){
        Messenger().post({
            message: "请输入登录邮箱!",
            showCloseButton: true,
            type: "error",
            id: 0
        });
        return;
    }

    if(is_null(password)){
        Messenger().post({
            message: "请输入密码!",
            showCloseButton: true,
            type: "error",
            id: 0
        });
        return;
    }

    $.ajax({
        url: "/login" + window.location.search,
        type: "POST",
        dataType: "json",
        data: {
            email: email,
            password: password,
            _xsrf: getCookie("_xsrf")
        },
        success: function(data, textStatus, jqXHR){
            if (data.error != undefined) {
                Messenger().post({
                    message: data.error,
                    showCloseButton: true,
                    type: "error",
                    id: 0
                });
            } else {
                window.location.href = data.next;
            }
        },
        error: function(jqXHR , textStatus , errorThrown){
            Messenger().post({
                message: "登录失败!",
                showCloseButton: true,
                type: "error",
                id: 0
            });
        }
    });
}

;(function($) {
    "use strict";

    function detectBrowser() {
        if($.browser.msie){
            Messenger().post({
                message: '<h5>警告:</h5> \
                    <div>当前IE及IE内核浏览器对本站支持不是太好, 为了使你拥有更\
                        好的体验请使用 \
                    <a href="https://www.google.com/intl/zh-CN/chrome/browser/"\
                         target="_blank" class="red-color">Chrome</a>、\
                    <a href="http://www.firefox.com.cn/" target="_blank" \
                        class="red-color">Firefox</a>、\
                    <a href="http://www.opera.com/zh-cn" target="_blank" \
                        class="red-color">Opera</a>、\
                    <a href="http://support.apple.com/zh_CN/downloads/#safari" \
                        target="_blank" class="red-color">Safari</a>\
                    等现代浏览器</div>',
                showCloseButton: true,
                type: "error",
                hideAfter: 0
            });
        }
    }

    var Controller = {
        loadRegisterModal: function() {
            $.ajax({
                url: "/register/template",
                type: "POST",
                dataType: "html",
                data: {
                    _xsrf: getCookie("_xsrf")
                },
                success: function(data, textStatus, jqXHR){
                    $.fancybox({
                        padding: 0,
                        closeBtn: true,
                        topRatio: 0.3,
                        scrolling: "no",
                        type: "iframe",
                        content: data
                    });
                },
                error: function(jqXHR , textStatus , errorThrown){
                    Messenger().post({
                        message: "加载失败!",
                        showCloseButton: true,
                        type: "error"
                    });
                }
            });
        },
        register: function() {
            var name = $.trim($('input[name="register-name"]').val());
            var email = $.trim($('input[name="register-email"]').val());
            var password = $('input[name="register-password"]').val();

            if (is_null(name)) {
                Messenger().post({
                    id: 0,
                    message: "用户名不能为空!",
                    showCloseButton: true,
                    type: "error"
                });
                return;
            }

            if (is_null(email)) {
                Messenger().post({
                    id: 0,
                    message: "请填写你的邮箱!",
                    showCloseButton: true,
                    type: "error"
                });
                return;
            }

            if (!validateEmail(email)) {
                Messenger().post({
                    id: 0,
                    message: "邮箱格式不正确!",
                    showCloseButton: true,
                    type: "error"
                });
                return;
            }

            if (is_null(password)) {
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
                    message: "密码格式不正确! 密码必须为长度至少为6的字母、数字或\
                              者非空白字符的组合!",
                    showCloseButton: true,
                    type: "error"
                })
                return;
            }

            $.ajax({
                url: "/register",
                type: "POST",
                dataType: "json",
                data: {
                    name: name,
                    email: email,
                    password: password,
                    _xsrf: getCookie("_xsrf")
                },
                success: function(data, textStatus, jqXHR){
                    if(data.error != undefined){
                        Messenger().post({
                            id: 0,
                            message: data.error,
                            showCloseButton: true,
                            type: "error"
                        })
                    }
                    else{
                        $.fancybox.close();

                        Messenger().post({
                            id: 0,
                            message: data.success,
                            showCloseButton: true,
                            type: "success"
                        });
                    }
                },
                error: function(jqXHR , textStatus , errorThrown){
                    Messenger().post({
                        id: 0,
                        message: "注册失败!",
                        showCloseButton: true,
                        type: "error"
                    })
                }
            });
        },
        sendResetPasswordMail: function() {
            var email = $.trim($('input[name="validate-email"]').val());

            if (is_null(email)) {
                Messenger().post({
                    id: 0,
                    message: "请填写你的登录邮箱!",
                    showCloseButton: true,
                    type: "error"
                });
                return;
            }

            if (!validateEmail(email)) {
                Messenger().post({
                    id: 0,
                    message: "登录邮箱格式错误!",
                    showCloseButton: true,
                    type: "error"
                });
                return;
            }

            $.ajax({
                url: "/password/reset/sendmail",
                type: "POST",
                dataType: "json",
                data: {
                    email: email,
                    _xsrf: getCookie("_xsrf")
                },
                success: function(data, textStatus, jqXHR){
                    if(data.error != undefined){
                        Messenger().post({
                            id: 0,
                            message: data.error,
                            showCloseButton: true,
                            type: "error"
                        });
                    }
                    else{
                        $.fancybox.close();
                        $('input[name="validate-email"]').val("");

                        Messenger().post({
                            id: 0,
                            message: "验证邮件发送成功! 请前往你的邮箱查看! 如果没有，请检查垃圾邮件！",
                            showCloseButton: true,
                            type: "success"
                        });
                    }
                },
                error: function(jqXHR , textStatus , errorThrown){
                    Messenger().post({
                        id: 0,
                        message: "发送失败!",
                        showCloseButton: true,
                        type: "error"
                    });
                }
            });
        },
        sendActiveAccountMail: function() {
            var email = $.trim($('input[name="activation-email"]').val());

            if (is_null(email)) {
                Messenger().post({
                    id: 0,
                    message: "请填写你的登录邮箱!",
                    showCloseButton: true,
                    type: "error"
                })
                return;
            }

            if (!validateEmail(email)) {
                Messenger().post({
                    id: 0,
                    message: "登录邮箱格式错误!",
                    showCloseButton: true,
                    type: "error"
                });
                return;
            }

            $.ajax({
                url: "/account/active/sendmail",
                type: "POST",
                dataType: "json",
                data: {
                    email: email,
                    _xsrf: getCookie("_xsrf")
                },
                success: function(data, textStatus, jqXHR){
                    if(data.error != undefined){
                        Messenger().post({
                            id: 0,
                            message: data.error,
                            showCloseButton: true,
                            type: "error"
                        });
                    }
                    else{
                        $.fancybox.close();
                        $('input[name="activation-email"]').val("");

                        Messenger().post({
                            id: 0,
                            message: "激活邮件发送成功! 请前往你的邮箱查看！如果没有，请检查垃圾邮件！",
                            showCloseButton: true,
                            type: "success"
                        });
                    }
                },
                error: function(jqXHR , textStatus , errorThrown){
                    Messenger().post({
                        id: 0,
                        message: "发送失败!",
                        showCloseButton: true,
                        type: "error"
                    });
                }
            });
        }
    };

    $(document).ready(function(){
        store.clear()
        detectBrowser();

        var fancyboxConfig = {
            padding: 0,
            closeBtn: true,
            topRatio: 0.3,
            scrolling: "no",
        };

        $("#forget-password-link").fancybox(fancyboxConfig);
        $("#resend-activation-email-link").fancybox(fancyboxConfig)
        $("#login-button").click(login);

        $("#register-link").click(Controller.loadRegisterModal);
        $("#submit-register-button").live('click', Controller.register);
        $("#submit-validate-button").click(Controller.sendResetPasswordMail);
        $("#submit-activation-email-modal-button").click(
            Controller.sendActiveAccountMail);
    });
}(jQuery));
