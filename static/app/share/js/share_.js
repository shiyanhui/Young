;(function($) {
    "use strict";

    var Controller = {
        likeShare: function() {
            var _this = $(this);
            var share_id = _this.data("share-id");

            $.ajax({
                url: '/share/like',
                type: 'POST',
                dataType: 'json',
                data: {
                    share_id: share_id,
                    _xsrf: getCookie("_xsrf"),
                },
                success: function(data){
                    if(data.error){
                        Messenger().post({
                            id: 0,
                            message: data.error,
                            showCloseButton: true,
                            type: "error"
                        })
                        return;
                    }

                    var html = sprintf(
                        '<span class="red-color"><i class="fa \
                            fa-thumbs-o-up"></i> 赞%s</span>',
                        data.like_times
                    );
                    _this.replaceWith(html);
                },
                error: function() {
                    Messenger().post({
                        id: 0,
                        message: "点赞失败!",
                        showCloseButton: true,
                        type: "error"
                    })
                }
            });
        },
        downloadShare: function() {
            var _this = $(this);
            var cost = parseInt(_this.data("cost"));
            var share_id = _this.data("share-id");

            if(cost && cost > 0){
                alertify.set({labels: {
                    ok: "确定",
                    cancel : "取消"
                }});

                alertify.confirm(sprintf(
                        "下载将会花费你 %s 金币，你确定要下载？", cost
                    ), function (e){

                    if(e) {
                        window.location.href = sprintf(
                            "/share/download/%s", share_id
                        );
                    }
                });
            }
            else {
                window.location.href=sprintf("/share/download/%s", share_id);
            }
        }
    };

    $(document).ready(function(){
        $(".share-like-link").live("click", Controller.likeShare);
        $(".share-download-button").click(Controller.downloadShare);
    });

}(jQuery));
