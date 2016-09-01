;(function($) {
    'use strict';

    var Controller = {
        getRecommendFriends: function() {
            $.ajax({
                type: "post",
                url: "/profile/friend/recommend",
                data: {
                    _xsrf: getCookie("_xsrf")
                },
                dataType: "json",
                success: function(data, textStatus, jqXHR) {
                    $("#recommend-friend-block").replaceWith(data.html);
                },
                error: function(jqXHR, textStatus, errorThrown) {
                    Messenger().post({
                        id: 0,
                        message: "加载失败!",
                        showCloseButton: true,
                        type: "error"
                    })
                }
            });
        },
        fetchReward: function() {
            $.ajax({
                type: "post",
                url: "/reward/login/fetch",
                data: {
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
                        })
                    }
                    else{
                        $("#fetch-login-reward-label").html(sprintf(
                            '<span class="note-color">连续 %s 天</span>',
                            data.continuous_login_days
                        ));
                        $("#wealth-quantity-label").html(data.wealth);
                    }
                },
                error: function(jqXHR, textStatus, errorThrown) {
                    Messenger().post({
                        id: 0,
                        message: "领取失败！",
                        showCloseButton: true,
                        type: "error"
                    })
                }
            });
        }
    };

    $(document).ready(function() {
        $("#friend-recommend-link").live(
            "click", Controller.getRecommendFriends
        );
        $("#fetch-login-reward-link").click(Controller.fetchReward);
    });
}(jQuery));
