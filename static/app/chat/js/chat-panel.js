var chat_updater = {
    chat_with: null,
    errorSleepTime: 500,
    forbidden: false,
    poll: function() {
        chat_updater.request = $.ajax({
            url: "/chat/message/update",
            type: "post",
            dataType: "html",
            data: {
                "chat_with": chat_updater.chat_with,
                "_xsrf": getCookie("_xsrf")
            },
            success: chat_updater.onSuccess,
            error: chat_updater.onError
        });
    },
    onSuccess: function(data , textStatus , jqXHR){
        try {
            chat_updater.showMessage(data);
        }
        catch (e) {
            chat_updater.onError();
            return;
        }
        chat_updater.errorSleepTime = 500;
        if (!chat_updater.forbidden) {
            chat_updater.poll();
        }
    },
    onError: function(jqXHR , textStatus , errorThrown) {
        chat_updater.errorSleepTime *= 2;
        if (!chat_updater.forbidden){
            window.setTimeout(
                chat_updater.poll, chat_updater.errorSleepTime
            );
        }
    },
    showMessage: function(message) {
        chats_manager.get(chat_updater.chat_with).history.push(message);
        $("#chat-contents-list").append(message);

        var totalheight = (
            parseFloat($("#chat-body").height()) +
            parseFloat($("#chat-body").scrollTop())
        );
        $("#chat-body").animate({scrollTop: totalheight});
    }
};

;(function($) {
    "use strict";

    var distance = 0;
    var fetching = false;

    var Controller = {
        onKeyDown: function(event) {
            if (event.keyCode == 13) {
                var content = $.trim($(this).val());

                if(!is_null(content)){
                    $.ajax({
                        url: "/chat/message/new",
                        type: "post",
                        dataType: "html",
                        data: {
                            "body": content,
                            "chat_with": chat_updater.chat_with,
                            "_xsrf": getCookie("_xsrf")
                        },
                        success: chat_updater.showMessage
                    });
                }
                $(this).val("");
            }
        },
        onKeyUp: function(event) {
            if (event.keyCode == 13) {
                $(this).val("");
            }
        },
        closePanel: function() {
            chats_manager.get(chat_updater.chat_with).messenger.hide();
            chats_manager.remove(chat_updater.chat_with);
            $.fancybox.close();
        },
        minimizePanel: function() {
            var messenger = chats_manager.get(chat_updater.chat_with).messenger;
            messenger.update({
                "message": sprintf(
                    '<img src="/avatar/%s/thumbnail50x50">',
                    chat_updater.chat_with
                )
            });
            messenger.show();
            $.fancybox.close();
        },
        onMousewheel: function() {
            if($("#chat-body").scrollTop() == 0){
                distance += event.deltaY;

                if(event.deltaY >= 0){
                    distance = 0;
                }

                if(distance < -50 && !fetching){
                    distance = 0;
                    Controller.fetchHistory();
                }
            }
        },
        fetchHistory: function() {
            $.ajax({
                url: "/chat/message/history",
                type: "post",
                dataType: "json",
                data: {
                    "chat_with": chat_updater.chat_with,
                    "since": chats_manager.get(chat_updater.chat_with).since,
                    "_xsrf": getCookie("_xsrf")
                },
                beforeSend: function(){
                    fetching = true;
                    $("#chat-label").prepend('\
                        <div id="chat-spinner">\
                            <img src="/static/app/chat/img/spinner.gif" \
                                style="width: 20px">\
                        </div>'
                    );
                },
                success: function(data ){
                    if(!data.has){
                        $("#pull-chat-history").html("已无更旧消息");
                        $("#chat-body").unmousewheel();
                        return;
                    }

                    $("#chat-contents-list").prepend(data.html);

                    var chat = chats_manager.get(chat_updater.chat_with);
                    if (chat.since > data.since) {
                        chat.since = data.since;
                    }
                    chat.history.splice(0, 0, data.html);
                },
                error: function(){
                    $("#pull-chat-history").html("获取失败");
                    $("#chat-body").unmousewheel();
                },
                complete: function(){
                    $("#chat-label").css({"marginTop": 0});
                    $("#chat-spinner").remove();
                    fetching = false;
                }
            });
        }
    };

    $(document).ready(function() {
        $("#chat-input-field").focus();
        $("#chat-input-field").keydown(Controller.onKeyDown);
        $("#chat-input-field").keyup(Controller.onKeyUp);
        $("#chat-body").mousewheel(Controller.onMousewheel);
        $(".close-panel").click(Controller.closePanel);
        $(".minimize-panel").click(Controller.minimizePanel);
    });
}(jQuery));
