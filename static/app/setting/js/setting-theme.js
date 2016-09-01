;(function($) {
    "use strict";

    var Controller = {
        setTheme: function() {
            var theme = $('select[name="theme"]').val();

            $.ajax({
                type: "post",
                url: "/setting/theme/set",
                data: {
                    theme: theme,
                    _xsrf: getCookie("_xsrf"),
                },
                dataType: "json",
                success: function(data, textStatus, jqXHR) {
                    Messenger().post({
                        id: 0,
                        message: "保存成功!",
                        showCloseButton: true,
                        type: "success"
                    });
                    window.location.reload();
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

    $(document).ready(function(){
        $("#save-theme-button").click(Controller.setTheme);
    });
}(jQuery));
