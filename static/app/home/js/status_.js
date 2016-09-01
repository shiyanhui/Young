;(function($) {
    "use strict";

    var replyeder_id = null;

    var Controller = {
        likeStatus: function() {
            var _this = $(this);
            var status_id = _this.data("status-id");

            $.ajax({
                type: "post",
                url: "/home/status/like",
                data: {
                    status_id: status_id,
                    _xsrf: getCookie("_xsrf")
                },
                dataType: "json",
                beforeSend: function(){
                    $(".status-likers").tooltip("destroy");
                },
                success: function(data, textStatus, jqXHR) {
                    var html = '\
                        <span class="status-likers red-color" \
                            data-toggle="tooltip" title="%s">\
                            <i class="fa fa-thumbs-o-up"></i> 赞%s\
                        </span>';
                    var like_times = '';

                    if(data.like_times > 0){
                        like_times = data.like_times;
                    }
                    _this.replaceWith(sprintf(html, data.likers, like_times));
                    $(".status-likers").tooltip();
                },
                error: function(jqXHR, textStatus, errorThrown) {
                    Messenger().post({
                        id: 0,
                        message: "点赞失败!",
                        showCloseButton: true,
                        type: "error"
                    });
                }
            });
        },
        commentStatus: function() {
            var _this = $(this);
            var status_id = _this.data("status-id");
            var toggle_status = _this.data("toggle-status");

            if(toggle_status == "closed"){
                $.ajax({
                    type: "post",
                    url: "/home/status/comments",
                    data: {
                        status_id: status_id,
                        _xsrf: getCookie("_xsrf")
                    },
                    dataType: "json",
                    success: function(data, textStatus, jqXHR) {
                        $(sprintf(
                            "#status-comments-wrap-%s", status_id
                        )).html(data.html);

                        _this.data("toggle-status", "open");

                        $(".status-comment-item").hover(function() {
                            $(sprintf(
                                "#status-comment-reply-%s",
                                $(this).data("status-comment-id")
                            )).show();
                        }, function() {
                            $(sprintf(
                                "#status-comment-reply-%s",
                                $(this).data("status-comment-id")
                            )).hide();
                        });
                    },
                    error: function(jqXHR, textStatus, errorThrown){
                        Messenger().post({
                            id: 0,
                            message: "请求失败!",
                            showCloseButton: true,
                            type: "error"
                        })
                    }
                });
            }
            else{
                $(sprintf("#status-comments-wrap-%s", status_id)).html("");
                _this.data("toggle-status", "closed")
            }
        },
        addReplyeder: function() {
            var _this = $(this);
            var user_id = _this.data("author-id");
            var name = _this.data("author-name");
            var status_id = _this.data("status-id");

            var template = '\
                <table> \
                    <tbody> \
                        <tr> \
                            <td width="480px">回复<a href="/profile/%s" \
                                data-userid="%s">%s</a>:\
                            </td> \
                            <td width="100px" align="right"> \
                                <a href="javascript:void(0)" \
                                    data-status-id="%s"\
                                    class="black-color \
                                    clear-reply-status-comment-link"> \
                                    <i class="fa fa-times"></i> \
                                </a> \
                            </td> \
                        </tr> \
                    </tbody> \
                </table>';
            $(sprintf("#show-replyer-label-%s", status_id)).html(sprintf(
                template, user_id, user_id, name, status_id
            ));
            replyeder_id = user_id;
        },
        removeReplyeder: function() {
            var status_id = $(this).data("status-id");
            $(sprintf("#show-replyer-label-%s", status_id)).html("");
            replyeder_id = null;
        },
        submitComment: function() {
            var status_id = $(this).data("status-id");
            var content = $(sprintf(
                "#status-comment-textarea-%s", status_id
            )).val();

            if(is_null(content)){
                Messenger().post({
                    id: 0,
                    message: "评论内容不能为空!",
                    showCloseButton: true,
                    type: "error"
                });
                return;
            }

            if(content.length > 200){
                Messenger().post({
                    id: 0,
                    message: "评论内容不能操作200字!!",
                    showCloseButton: true,
                    type: "error"
                });
                return;
            }

            $.ajax({
                type: "post",
                url: "/home/status/comment/new",
                data: {
                    status_id: status_id,
                    content: content,
                    replyeder_id: replyeder_id,
                    _xsrf: getCookie("_xsrf")
                },
                dataType: "json",
                success: function(data, textStatus, jqXHR) {
                    if(data.error){
                        Messenger().post({
                            id: 0,
                            message: data.error,
                            type: "error",
                            showCloseButton: true
                        });
                    }
                    else{
                        $(sprintf(
                            "#status-comment-table-%s",
                            status_id
                        )).append(data.html)

                        $(sprintf(
                            "#status-comment-textarea-%s",
                            status_id
                        )).val("")

                        $(".status-comment-item").hover(function() {
                            $(sprintf(
                                "#status-comment-reply-%s",
                                $(this).data("status-comment-id")
                            )).show();
                        }, function() {
                            $(sprintf(
                                "#status-comment-reply-%s",
                                $(this).data("status-comment-id")
                            )).hide();
                        });
                    }
                },
                error: function(jqXHR, textStatus, errorThrown){
                    Messenger().post({
                        id: 0,
                        message: "评论失败!",
                        type: "error",
                        showCloseButton: true
                    });
                }
            });
        }
    };

    $(document).ready(function(){
        // $(".status-content img").wrap(function() {
        //     var template = '<a class="fancybox fancybox.image" href="%s"></a>'
        //     return sprintf(template, $(this).attr("src"));
        // });

        $(".fancybox").fancybox({
            padding: 5,
            maxWidth: 800,
        });
        $(".status-likers").tooltip();
        $(".status-like-link").live("click", Controller.likeStatus);
        $(".status-comment-link").live("click", Controller.commentStatus);
        $(".reply-status-comment-link").live("click", Controller.addReplyeder);
        $(".clear-reply-status-comment-link").live(
            "click", Controller.removeReplyeder
        );
        $(".status-comment-submit-button").live(
            "click", Controller.submitComment
        );
    });
}(jQuery));
