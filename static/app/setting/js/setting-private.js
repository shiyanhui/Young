;(function($) {
    "use strict";

    var Controller = {
        setPrivate: function() {
            var require_verify_when_add_friend = $(
                "#require-verify-when-add-friend").get(0).checked;
            var allow_stranger_visiting_profile = $(
                "#allow-stranger-visiting-profile").get(0).checked;
            var allow_stranger_chat_with_me = $(
                "#allow-stranger-chat-with-me").get(0).checked;
            var enable_leaving_message = $(
                "#enable-leaving-message").get(0).checked;

            $.ajax({
                type: "post",
                url: "/setting/private/set",
                data: {
                    require_verify_when_add_friend: require_verify_when_add_friend,
                    allow_stranger_visiting_profile: allow_stranger_visiting_profile,
                    allow_stranger_chat_with_me: allow_stranger_chat_with_me,
                    enable_leaving_message: enable_leaving_message,
                    _xsrf: getCookie("_xsrf")
                },
                dataType: "json",
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
        var elem = $(".switchery");

        for (var i = 0; i < elem.size(); i++) {
            var checkbox = elem.get(i);
            var init = new Switchery(checkbox);
            checkbox.onchange = Controller.setPrivate;
        };
    });
}(jQuery));
