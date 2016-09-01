var chats_manager = {
    chats: {},
    has: function(id) {
        if (chats_manager.chats[id] == undefined) {
            return false;
        }
        return true;
    },
    add: function(id, data) {
        chats_manager.chats[id] = data;
    },
    get: function(id) {
        if (chats_manager.has(id)) {
            return chats_manager.chats[id];
        }
        return null;
    },
    remove: function(id) {
        if (chats_manager.has(id)) {
            delete chats_manager.chats[id];
        }
    },
    new_chat_panel: function(id) {
        $.ajax({
            url: "/chat/with",
            type: "post",
            dataType: "html",
            data: {
                _xsrf: getCookie("_xsrf")
            },
            success: function(data, textStatus, jqXHR) {
                $.fancybox({
                    title: sprintf(
                        "正在和%s聊天...", chats_manager.get(id).name
                    ),
                    padding: 0,
                    type: "iframe",
                    scrolling: 'no',
                    closeBtn: true,
                    content: data,
                    modal: true,
                    beforeShow: function() {
                        var history = chats_manager.get(id).history;
                        for (var i in history) {
                            $("#chat-contents-list").append(history[i]);
                        }
                        var totalheight = (
                            parseFloat($("#chat-contents-list").height()) +
                            parseFloat($("#chat-body").scrollTop())
                        );
                        $("#chat-body").animate({
                            scrollTop: totalheight
                        }, "fast");
                    },
                    afterShow: function() {
                        chat_updater.chat_with = id;
                        chat_updater.poll();
                    },
                    beforeClose: function() {
                        chat_updater.forbidden = true;
                        chat_updater.request.abort();
                    },
                });
            }
        });
    },

    new_message: function(each_people) {
        var id = each_people.sender["id"];
        var name = each_people.sender["name"];
        var history = [];
        var since = (new Date()).getTime();
        var body;

        if (!chats_manager.has(id)) {
            for (var i in each_people.messages) {
                history.push(each_people.messages[i].html);
                body = each_people.messages[i].body;
                if (each_people.messages[i].since < since) {
                    since = each_people.messages[i].since;
                }
            }

            var messenger = Messenger().post({
                message: sprintf('\
                    <img src="/avatar/%s/thumbnail50x50"> %s \
                    <span class="note-color">(提示: 点击该消息框以打开聊天窗口图)\
                    </span>',
                    id, body
                ),
                type: "success",
                showCloseButton: true,
                hideAfter: 0,
                id: id,
                events: {
                    click: function() {
                        $(".minimize-panel").trigger("click");
                        messenger.hide();
                        chats_manager.new_chat_panel(id);
                    },
                    close: function() {
                        chats_manager.remove(id);
                    }
                }
            });

            var data = {
                "name": name,
                "history": history,
                "messenger": messenger,
                "since": since
            }
            chats_manager.add(id, data);
            return;
        }

        for (var i in each_people.messages) {
            chats_manager.get(id).history.push(
                each_people.messages[i].html
            );
            body = each_people.messages[i].body;
            if (each_people.messages[i].since < chats_manager.get(id).since) {
                chats_manager.get(id).since = each_people.messages[i].since;
            }
        }
        chats_manager.chats[id]["messenger"].update({
            "message": sprintf(
                '<img src="/avatar/%s/thumbnail50x50"> %s', id, body
            )
        })
    }
};

var tab_id = uuid.v1();

var message_updater = {
    n: 1,
    id: tab_id,
    errorSleepTime: 500,
    forbidden: false,
    start: function() {
        if (!store.enabled) {
            Messenger().post({
                message: '你的浏览器不支持私聊, 请关闭"Private Mode", 或者使用最新\
                          的Chrome/Firefox/Opera/Safari等非IE内核浏览器',
                type: "error",
                showCloseButton: true,
                hideAfter: 0,
                id: 0
            });
            return;
        }

        var updaters = store.get("u");
        if (!updaters || !updaters.length) {
            store.set("u", [message_updater.id]);
        }
        else {
            updaters.push(message_updater.id);
            store.set("u", updaters);
        }

        message_updater.poll();

        window.onbeforeunload = function(){
            message_updater.close_tab();
        }

        $(window).on('storage', function(e) {
            var data = e.originalEvent;

            if (data.key == "m") {
                var message = store.get("m");
                if (message) {
                    message_updater.newMessage(message);
                }
            }
            else if (data.key == "u") {
                var updaters = store.get("u");

                if (updaters && updaters.length > 0) {
                    var index = -1;
                    for (var i = 0; i < updaters.length; i++) {
                        if (updaters[i] == message_updater.id) {
                            index = i
                        }
                    };

                    if(index != -1){
                        message_updater.forbidden = true;
                        try{message_updater.request.abort();} catch(e){};
                    }
                }
            }
        });
    },
    poll: function() {
        message_updater.request = $.ajax({
            url: "/message/update",
            type: "post",
            dataType: "json",
            data: {
                n: message_updater.n,
                "_xsrf": getCookie("_xsrf")
            },
            timeout: 60000,
            success: message_updater.onSuccess,
            error: message_updater.onError,
            complete: message_updater.onDone
        });
    },
    onSuccess: function(data, textStatus, jqXHR) {
        try {
            if (data.topic == "unread_message_numbers") {
                $("#unread-message-numbers").html(data.html);
            }
            else if (data.topic == "chat_message_new") {
                for (var i in data.each_people) {
                    chats_manager.new_message(data.each_people[i]);
                }
            }
            else {
                message_updater.newMessage(data);
            }
        }
        catch (e) {
            message_updater.onError();
            return;
        }

        if (!message_updater.forbidden) {
            message_updater.errorSleepTime = 500;
            message_updater.poll();
        }
        message_updater.n += 1;
    },
    onError: function(jqXHR, textStatus, errorThrown) {
        if (textStatus == "timeout") {
            message_updater.poll();
        } else if (!message_updater.forbidden) {
            message_updater.errorSleepTime *= 2;
            window.setTimeout(
                message_updater.poll,
                message_updater.errorSleepTime
            );
        }
        message_updater.n += 1;
    },
    newMessage: function(data) {
        Messenger().post({
            message: data.html,
            type: "success",
            showCloseButton: true,
            hideAfter: 0
        });
        message_updater.alert();
    },
    alert: function() {
        document.title = 'Young社区【新消息】';
    },
    close_tab: function() {
        var updaters = store.get("u");

        var index = -1;
        for (var i = 0; i < updaters.length; i++) {
            if (updaters[i] == message_updater.id) {
                index = i;
            }
        };
        if (index != -1) {
            try {updaters[index].request.abort()} catch (e) {};
            updaters.splice(index, 1);
        }

        if (!updaters || !updaters.length) {
            store.clear();
        }
        else {
            store.set("u", updaters);
        }
    }
};

;(function($) {
    "use strict";

    var Controller = {
        openChat: function() {
            var chat_with = $(this).data("chat-with");
            var user_name = $(this).data("user-name");

            if (!chats_manager.has(chat_with)) {
                var messenger = Messenger().post({
                    message: sprintf(
                        '<img src="/avatar/%s/thumbnail50x50">',
                        chat_with
                    ),
                    type: "success",
                    showCloseButton: true,
                    hideAfter: 0,
                    id: chat_with,
                    events: {
                        click: function() {
                            messenger.hide();
                            chats_manager.new_chat_panel(chat_with);
                        },
                        close: function() {
                            chats_manager.remove(chat_with);
                        }
                    }
                });
                messenger.hide();
                var data = {
                    name: user_name,
                    history: [],
                    messenger: messenger,
                    since: (new Date()).getTime()
                }
                chats_manager.add(chat_with, data);
            }
            chats_manager.new_chat_panel(chat_with);
        }
    };

    $(document).ready(function() {
        message_updater.start();
        $(".chat-with").live("click", Controller.openChat);
    });
}(jQuery));
