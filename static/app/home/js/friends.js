;(function($) {
    "use strict";

    var Controller = {
        shield: function(){
            var _this = $(this);
            var friend_id = _this.data("friend-id");

            var shield_friend = function(){
                $.ajax({
                    type: "post",
                    url: "/friend/shield",
                    data: {
                        friend_id: friend_id,
                        _xsrf: getCookie("_xsrf")
                    },
                    dataType: "json",
                    success: function(data, textStatus, jqXHR) {
                        if(data.error){
                            Messenger().post({
                                id: 0,
                                message: data.error,
                                showButtonClose: true,
                                type: "error"
                            })
                        }
                        else{
                            if(data.shielded){
                                Messenger().post({
                                    id: 0,
                                    message: "屏蔽成功!",
                                    showButtonClose: true,
                                    type: "success"
                                })
                                _this.addClass("red-color");
                            }
                            else{
                                _this.removeClass("red-color");
                            }
                        }
                    },
                    error: function(jqXHR, textStatus, errorThrown){
                        Messenger().post({
                            id: 0,
                            message: "屏蔽失败!",
                            showButtonClose: true,
                            type: "error"
                        })
                    }
                });
            }

            if(!_this.hasClass("red-color")){
                alertify.set({labels: {
                    ok: "确定",
                    cancel : "取消"
                }});

                alertify.confirm("屏蔽后, 你将不会收到该好友的状态, \
                                    确定要屏蔽?", function (e) {
                    if(e) {
                        shield_friend();
                    }
                });
            }
            else{
                shield_friend();
            }
        },
        block: function(){
            var _this = $(this);
            var friend_id = _this.data("friend-id");

            var block_friend = function(){
                $.ajax({
                    type: "post",
                    url: "/friend/block",
                    data: {
                        friend_id: friend_id,
                        _xsrf: getCookie("_xsrf")
                    },
                    dataType: "json",
                    success: function(data, textStatus, jqXHR) {
                        if(data.error){
                            Messenger().post({
                                id: 0,
                                message: data.error,
                                showButtonClose: true,
                                type: "error"
                            })
                        }
                        else{
                            if(data.blocked){
                                Messenger().post({
                                    id: 0,
                                    message: "拉黑成功!",
                                    showButtonClose: true,
                                    type: "success"
                                })
                                _this.addClass("red-color");
                            }
                            else{
                                _this.removeClass("red-color");
                            }
                        }
                    },
                    error: function(jqXHR, textStatus, errorThrown){
                        Messenger().post({
                            id: 0,
                            message: "拉黑失败!",
                            showButtonClose: true,
                            type: "error"
                        })
                    }
                });
            }

            if(!_this.hasClass("red-color")){
                alertify.set({labels: {
                    ok: "确定",
                    cancel : "取消"
                }});

                alertify.confirm("拉黑后, 该好友将不会收到你的新状态, \
                                  确定要拉黑?", function (e) {
                    if(e){
                        block_friend();
                    }
                });
            }
            else{
                block_friend();
            }
        },
        delete: function(){
            var _this = $(this);
            var friend_id = _this.data("friend-id");

            var delete_friend = function(){
                $.ajax({
                    type: "post",
                    url: "/friend/delete",
                    data: {
                        friend_id: friend_id,
                        _xsrf: getCookie("_xsrf")
                    },
                    dataType: "json",
                    success: function(data, textStatus, jqXHR) {
                        if(data.error){
                            Messenger().post({
                                id: 0,
                                message: data.error,
                                showButtonClose: true,
                                type: "error"
                            })
                            return;
                        }

                        Messenger().post({
                            id: 0,
                            message: "删除成功!",
                            showButtonClose: true,
                            type: "success"
                        })

                        $(sprintf(
                            '[class*="friends-list-item"][data-friend-id="%s"]',
                            friend_id
                        )).replaceWith("");
                    },
                    error: function(jqXHR, textStatus, errorThrown){
                        Messenger().post({
                            id: 0,
                            message: "删除失败!",
                            showButtonClose: true,
                            type: "error"
                        })
                    }
                });
            }

            alertify.set({labels: {
                ok: "确定",
                cancel : "取消"
            }});

            alertify.confirm("删除对方的同时, 同时也会自动地将你从对方的\
                              好友列表里删除, 确定要删除?", function (e) {
                if(e){
                    delete_friend();
                }
            });
        }
    };

    $(document).ready(function(){
        $(".friends-list-item").live({
            mouseenter: function() {
                $(sprintf("#action-list-%s", $(this).data("friend-id"))).show();
            },
            mouseleave: function() {
                $(sprintf("#action-list-%s", $(this).data("friend-id"))).hide();
            }
        });

        $(".action-shield").live("click", Controller.shield);
        $(".action-block").live("click", Controller.block);
        $(".action-delete").live("click", Controller.delete);
    });
}(jQuery));
