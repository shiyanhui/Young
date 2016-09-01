;(function($) {
    "use strict";

    var replyeder_id = null;

    var Controller = {
        addReplyeder: function() {
            $.scrollTo("100%", 200);

            var _this = $(this);
            var user_id = _this.data("author-id");
            var name = _this.data("author-name");

            var template = '\
                <div class="pull-left"> \
                    回复<a href="/profile/%s" data-userid="%s">%s</a>: \
                </div> \
                <div class="pull-right"> \
                    <a id="clear-reply-leavemessage-link" \
                        href="javascript:void(0)" class="black-color"> \
                        <i class="fa fa-times"></i> \
                    </a> \
                </div> \
                <div class="clearfix">\
                </div>';

            $("#show-replyer-label").html(
                sprintf(template, user_id, user_id, name)
            );
            replyeder_id = user_id;
        },
        removeReplyeder: function() {
            $("#show-replyer-label").html("");
            replyeder_id = null;
        },
        leaveMessage: function() {
            var _this = $(this);
            var user_id = _this.data("user-id");
            var private_ = $("#private-leavemessage-checkbox").get(0).checked;
            var content = $("#leavemessage-editor").getHtml();

            if(is_null(cleanHTML(content))){
                Messenger().post({
                    id: 0,
                    message: "请输入留言内容!",
                    showCloseButton: true,
                    type: "error"
                });
                return;
            }

            if(content.length > 5000){
                Messenger().post({
                    id: 0,
                    message: "留言太长了!",
                    showCloseButton: true,
                    type: "error"
                });
                return;
            }

            $.ajax({
                type: "post",
                url: "/profile/leavemessage/new",
                data: {
                    user_id: user_id,
                    private: private_,
                    content: content,
                    replyeder_id: replyeder_id,
                    _xsrf: getCookie("_xsrf")
                },
                dataType: "json",
                success: function(data, textStatus, jqXHR) {
                    $("#leavemessage-list").append(data.html);
                    $(".leavemessage-list-part").show();
                    $("#leavemessage-editor").html("");
                    $("#show-replyer-label").html("");
                    replyeder_id = null;
                },
                error: function(jqXHR, textStatus, errorThrown) {
                    Messenger().post({
                        id: 0,
                        message: "留言失败!",
                        showCloseButton: true,
                        type: "error"
                    })
                }
            });
        },
        loadMoreLeaveMessage: function() {
            var _this = $(this);
            var page = _this.data("page");
            var user_id = _this.data("user-id");

            $.ajax({
                type: "post",
                url: "/profile/leavemessage/more",
                data: {
                    page: page,
                    user_id: user_id,
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
                        $("#leavemessage-list").append(data.html);
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
                    });
                }
            });
        }
    };

     $(document).ready(function(){
        $(".wysiwyg-editor").wysiwyg({hotKeys: {}});

        $("input").iCheck({
            checkboxClass: 'icheckbox_minimal-red',
            radioClass: 'iradio_minimal',
        });

        $(".leavemessage-list-item").live({
            mouseenter: function() {
                $(sprintf(
                    "#leavemessage-action-%s",
                    $(this).data("leavemessage-id")
                )).show();
            },
            mouseleave: function() {
                $(sprintf(
                    "#leavemessage-action-%s",
                    $(this).data("leavemessage-id")
                )).hide();
            }
        });

        $(".reply-leavemessage-link").live("click", Controller.addReplyeder);
        $("#clear-reply-leavemessage-link").live(
            "click", Controller.removeReplyeder
        );
        $("#submit-leavemessage-button").click(Controller.leaveMessage);
        $("#load-more-leavemessage-button").live(
            "click", Controller.loadMoreLeaveMessage
        );
    });
}(jQuery));
