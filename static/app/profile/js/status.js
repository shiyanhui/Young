;(function($) {
    "use strict";

    var Controller = {
        loadMoreStatus: function() {
            var _this = $(this);
            var page = _this.data("page");

            $.ajax({
                type: "post",
                url: "/profile/status/more",
                data: {
                    page: page,
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
                        $("#status-list").append(data.html);
                        _this.data('page', data.page);
                    }
                    else{
                        _this.hide();
                    }
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
        recommendFriend: function() {
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
        saveLeagueBulletin: function(){
            var league_bulletin = $('textarea[name="league-bulletin"]').val();
            $.ajax({
                type: "post",
                url: "/profile/league/bulletin/save",
                data: {
                    league_bulletin : league_bulletin,
                    _xsrf: getCookie( "_xsrf" )
                },
                dataType: "json",
                success: function(data ,textStatus , jqXHR){
                    Messenger().post({
                        id: 0,
                        message: "保存成功!",
                        showCloseButton: true,
                        type: "success"
                    })
                    $("#league-bulletin-content").removeClass(
                        "no-league-bulletin"
                    );
                    $("#league-bulletin-content").addClass(
                        "flat-block-content"
                    );
                    $("#league-bulletin-content").html(league_bulletin);
                    $.fancybox.close();
                },
                error: function(jqXHR, textStatus, errorThrown){
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
        $("#change-league-bulletin-link").fancybox({
            padding: 0,
            topRatio: 0.3,
            closeClick: false
        });

        $("#load-more-status-button").live("click", Controller.loadMoreStatus);
        $("#friend-recommend-link").live("click", Controller.recommendFriend);
        $("#save-league-bulletin-button").click(Controller.saveLeagueBulletin);
    });
}(jQuery));
