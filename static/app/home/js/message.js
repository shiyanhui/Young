;(function($) {
    "use strict";

    var Controller = {
        loadMoreMessage: function() {
            var _this = $(this);
            var page = _this.data("page");
            var category = _this.data("category");

            $.ajax({
                type: "post",
                url: "/home/message/more",
                data: {
                    page: page,
                    category: category,
                    _xsrf: getCookie("_xsrf")
                },
                dataType: "json",
                beforeSend: function(jqXHR){
                    _this.html("正在加载中...");
                },
                complete: function(jqXHR, textStatus){
                    _this.html("加载更多");
                },
                success: function(data, textStatus, jqXHR) {
                    if(!is_null(data.html)){
                        $("#message-list").append(data.html);
                        _this.data('page', data.page);
                    }
                    else{
                        _this.hide();
                    }
                },
                error: function(jqXHR, textStatus, errorThrown) {
                    Messenger().post({
                        id: 0,
                        message: "加载失败",
                        showCloseButton: true,
                        type: "error"
                    })
                }
            });
        },
        aggreeFriendRequest: function() {
            var user_id = $(this).data("user-id");

            $.ajax({
                type: "post",
                url: "/profile/friend/request/agree",
                data: {
                    user_id: user_id,
                    _xsrf: getCookie("_xsrf")
                },
                dataType: "json",
                success: function(data, textStatus, jqXHR) {
                    $(sprintf(".message-list-item-%s", user_id)).hide();
                    Messenger().post({
                        id: 0,
                        message: "添加成功!",
                        showCloseButton: true,
                        type: "success"
                    });
                },
                error: function(jqXHR, textStatus, errorThrown) {
                    Messenger().post({
                        id: 0,
                        message: "添加失败!",
                        showCloseButton: true,
                        type: "error"
                    });
                }
            });
        },
        refuseFriendRequest: function() {
            var user_id = $(this).data("user-id");

            $.ajax({
                type: "post",
                url: "/profile/friend/request/refuse",
                data: {
                    user_id: user_id,
                    _xsrf: getCookie("_xsrf")
                },
                dataType: "json",
                success: function(data, textStatus, jqXHR) {
                    $(sprintf(".message-list-item-%s", user_id)).hide();
                },
                error: function(jqXHR, textStatus, errorThrown) {
                    Messenger().post({
                        id: 0,
                        message: "拒绝失败!",
                        showCloseButton: true,
                        type: "error"
                    })
                }
            });
        }
    };

    $(document).ready(function(){
        $("#load-more-message-button").live(
            "click", Controller.loadMoreMessage
        );
        $(".friend-request-agree-link").click(
            Controller.aggreeFriendRequest
        );
        $(".friend-request-refuse-link").click(
            Controller.refuseFriendRequest
        );
    });
}(jQuery));
