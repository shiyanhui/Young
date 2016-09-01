;(function($) {
    "use strict";

    var Controller = {
        saveProfile: function() {
            var sex = $.trim($('input[name="sex"]:checked').val());
            var province = $.trim($('select[name="province"]').val());
            var city = $.trim($('select[name="city"]').val());
            var birthday = $.trim($('input[name="birthday"]').val());
            var relationship_status = $.trim($("#relationship-status").val());
            var phone = $.trim($('input[name="phone"]').val());
            var qq = $.trim($('input[name="qq"]').val());
            var signature = $.trim($('textarea[name="signature"]').val());

            if(is_null(signature)){
                signature = ""
            }

            $.ajax({
                type: "post",
                url: "/setting/profile/set",
                data: {
                    'sex': sex,
                    'province': province,
                    'city': city,
                    'birthday': birthday,
                    'relationship_status': relationship_status,
                    'phone': phone,
                    'qq': qq,
                    'signature': signature,
                    _xsrf: getCookie("_xsrf")
                },
                dataType: "json",
                success: function(data, textStatus, jqXHR) {
                    if(data.error){
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
        $("input").iCheck({
            checkboxClass: 'icheckbox_minimal-red',
            radioClass: 'iradio_minimal-red',
        });

        $("#relationship-status").select2({
            width: "324",
            placeholder: "请选择",
        });

        $("#save-profile-button").click(Controller.saveProfile);
    });
}(jQuery));
