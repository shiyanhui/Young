;(function($) {
    "use strict";

    var Controller = {
        removeMember: function() {
            var user_id = $(this).data("extra-userid");
            $.ajax({
                type: "post",
                url: "/profile/remove-leauge-member",
                data: {
                    user_id: user_id,
                    _xsrf: getCookie("_xsrf")
                },
                dataType: "json",
                success: function(data, textStatus, jqXHR) {
                    $('#member-' + user_id).remove();
                    if (data.member_number == 0) {
                        $("#member-list-table").html(
                            '<div style="padding-top: 100px;color: \
                                #999999;padding-left: 250px;">还没有成员加入\
                            </div>'
                        );
                    }
                }
            });
        }
    };

    $(document).ready(function(){
        $(".remove-member-link").live("click", Controller.removeMember);
    });
}(jQuery));
