;(function($) {
    "use strict";

    var Controller = {
        setNotification: function() {
            var email_notify_when_offline = $(
                "#email-notify-when-offline"
            ).get(0).checked;

            $.ajax({
                type: "post",
                url: "/setting/notification/set",
                data: {
                    email_notify_when_offline: email_notify_when_offline,
                    _xsrf: getCookie("_xsrf")
                },
                dataType: "json",
                error: function(jqXHR, textStatus, errorThrown) {
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
            checkbox.onchange = Controller.setNotification;
        };
    });
}(jQuery));
