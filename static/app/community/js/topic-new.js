;(function($) {
    "use strict";

    var Controller = {
        publishTopick: function() {
            var url = $("#publish-topic-button").data("url");

            var title = $.trim($("#question-title").val());
            if (!title) {
                Messenger().post({
                    id: 0,
                    message: "标题不能为空!",
                    showCloseButton: true,
                    type: "error"
                });
                return;
            }

            if (title.length > 100) {
                Messenger().post({
                    id: 0,
                    message: "标题太长了!",
                    showCloseButton: true,
                    type: "error"
                });
                return
            }

            var content = $("#editor").getHtml();
            if(is_null(cleanHTML(content))){
                content = "";
            }
            else if(content.length > 100000){
                Messenger().post({
                    id: 0,
                    message: "话题内容太长了!",
                    showCloseButton: true,
                    type: "error"
                })
            }

            var nodes = $("input[name='node-list']").val();
            nodes = nodes.slice(1, -1);

            var _nodes = [];
            if(nodes.length){
                _nodes = nodes.split(",");
            }

            if(_nodes.length > 3){
                Messenger().post({
                    id: 0,
                    message: "每个话题所属的节点最多有3个!",
                    showCloseButton: true,
                    type: "error"
                })
                return;
            }

            var result = [];
            for(var i in _nodes){
                var tmp = _nodes[i].slice(1, -1);
                tmp = $.trim(tmp);

                if(!is_null(tmp)){
                    result.push(tmp)
                }
            }
            nodes = result.join(",");

            if(is_null(nodes)){
                Messenger().post({
                    id: 0,
                    message: "节点不能为空!",
                    showCloseButton: true,
                    type: "error"
                })
                return;
            }

            var anonymous = $("#anonymous").attr("checked");

            $.ajax({
                url: url,
                type: 'POST',
                dataType: 'json',
                data: {
                    title: title,
                    content: content,
                    nodes: nodes,
                    anonymous: anonymous,
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
                        window.location.href = "/community";
                    }
                },
                error: function(jqXHR , textStatus , errorThrown){
                    Messenger().post({
                        id: 0,
                        message: "发布失败!",
                        showCloseButton: true,
                        type: "error"
                    })
                }
            });
        }
    };

    $(document).ready(function() {
        $("input[name='node-list']").textext({
            plugins : 'autocomplete tags ajax',
            ajax : {
                url: '/community/node/suggestion',
                dataType : 'json',
                cacheResults : false,
                typeDelay: 0
            }
        });

        $('#editor').wysiwyg({
            activeToolbarClass: 'btn-danger',
            hotKeys: {}
        });

        $("input").iCheck({
            checkboxClass: 'icheckbox_minimal-red',
            radioClass: 'iradio_minimal',
        });

        $("#publish-topic-button").click(Controller.publishTopick);
    });
}(jQuery));
