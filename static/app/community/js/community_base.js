;(function($) {
    'use strict';

    var Controller = {
        like: function(event) {
            var _this = $(this);
            var topic_id = _this.data("topic-id");

            $.ajax({
                url: '/community/topic/like',
                type: 'POST',
                dataType: 'json',
                data: {
                    topic_id: topic_id,
                    _xsrf: getCookie("_xsrf"),
                },
                success: function(data, textStatus, jqXHR){
                    if(data.error){
                        Messenger().post({
                            id: 0,
                            message: data.error,
                            showCloseButton: true,
                            type: "error"
                        })
                    }
                    else{
                        var t = '\
                            <span class="red-color"><i class="fa \
                                fa-thumbs-o-up"></i> 赞%s\
                            </span>';
                        var html = sprintf(t, data.like_times)
                        _this.replaceWith(html);
                    }
                },
                error: function(jqXHR , textStatus , errorThrown){
                    Messenger().post({
                        id: 0,
                        message: "点赞失败!",
                        showCloseButton: true,
                        type: "error"
                    })
                }
            });
        }
    };

    $(document).ready(function(){
        $(".topic-image").fancybox({
            padding: 5,
            maxWidth: 1000,
            prevEffect: 'none',
            nextEffect: 'none',
            helpers: {
                thumbs: {
                    width: 50,
                    height: 50
                }
            }
        });

        $(".topic-like-link").live("click", Controller.like);
    });
}(jQuery));
