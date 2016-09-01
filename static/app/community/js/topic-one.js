;(function($) {
    "use strict";

    var replyeder_id = null;

    var Controller = {
        likeToggle: function(event) {
            var status = $(this).data("status");
            var open = '展开<i class="fa fa-long-arrow-down">';
            var closed = '收起<i class="fa fa-long-arrow-up">'

            if(status == "closed"){
                $(".like-list-item").show();
                $(this).data("status", "open");
                $(this).html(closed);
            }
            else{
                $(".like-list-item").hide();
                $(this).data("status", "closed");
                $(this).html(open);
            }
        },
        loadMoreTopicComment: function() {
            var _this = $(this);
            var page = _this.data("page");
            var topic_id = _this.data("topic-id");

            $.ajax({
                type: "post",
                url: "/community/topic/comment/more",
                data: {
                    topic_id: topic_id,
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
                        $("#topic-comment-list").append(data.html);
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
                    <a id="clear-reply-topic-comment-link" \
                            href="javascript:void(0)" class="black-color"> \
                        <i class="fa fa-times"></i> \
                    </a> \
                </div> \
                <div class="clearfix"></div>';

            $("#show-replyer-label").html(
                sprintf(template, user_id, user_id, name)
            );
            replyeder_id = user_id;
        },
        removeReplyeder: function() {
            $("#show-replyer-label").html("");
            replyeder_id = null;
        },
        submitComment: function() {
            var topic_id = $(this).data("topic-id");
            var content = $.trim($("#editor").getHtml());
            var anonymous = $("#comment-anonymous-checkbox").get(0).checked;

            if(anonymous && replyeder_id){
                Messenger().post({
                    id: 0,
                    message: "匿名时只能评论不能回复",
                    showCloseButton: true,
                    type: "error"
                });
            }
            else if(is_null(cleanHTML(content))){
                Messenger().post({
                    id: 0,
                    message: "评论内容不能为空!",
                    showCloseButton: true,
                    type: "error"
                });
            }
            else if(content.length > 100000){
                Messenger().post({
                    id: 0,
                    message: "评论内容太长了!",
                    showCloseButton: true,
                    type: "error"
                });
            }
            else{
                $.ajax({
                    url: '/community/topic/comment/new',
                    type: 'POST',
                    dataType: 'json',
                    data: {
                        topic_id: topic_id,
                        content: content,
                        anonymous: anonymous,
                        replyeder_id: replyeder_id,
                        _xsrf: getCookie("_xsrf"),
                    },
                    success: function(data, textStatus, jqXHR){
                        if(data.error){
                            Messenger().post({
                                id: 0,
                                message: data.error,
                                showCloseButton: true,
                                type: "error"
                            });
                        }
                        else{
                            $("#editor").html("");
                            $("#topic-comment-list").append(data.item);
                            MathJax.Hub.Queue(["Typeset", MathJax.Hub]);
                            hljs.initHighlightingOnLoad();
                            $("#show-replyer-label").html("");
                            replyeder_id = null;
                        }
                    },
                    error: function(jqXHR , textStatus , errorThrown){
                        Messenger().post({
                            id: 0,
                            message: "评论失败!",
                            showCloseButton: true,
                            type: "error"
                        });
                    }
                });
            }
        }
    };

    $(document).ready(function() {
        hljs.initHighlightingOnLoad();

        $("#editor").wysiwyg({
            activeToolbarClass: 'btn-danger',
            hotKeys: {}
        });

        $(".topic-comment-item").live({
            mouseenter: function() {
                $(sprintf(
                    "#topic-comment-action-%s", $(this).data("comment-id")
                )).css("display", "inline-block");
            },
            mouseleave: function() {
                $(sprintf(
                    "#topic-comment-action-%s", $(this).data("comment-id")
                )).css("display", "none");
            }
        });

        $("#comment-link").click(function() {
            $.scrollTo("100%", 200);
        });

        $("#like-toggle-link").click(Controller.likeToggle);
        $("#load-more-topic-comment-button").click(
            Controller.loadMoreTopicComment
        );
        $(".reply-topic-comment-link").live("click", Controller.addReplyeder);
        $("#clear-reply-topic-comment-link").live(
            "click", Controller.removeReplyeder
        );
        $("#submit-comment-button").click(Controller.submitComment);
    });
}(jQuery));
