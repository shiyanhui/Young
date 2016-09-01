;(function($) {
    "use strict";

    var Controller = {
        recommendFriend: function() {
            $.ajax({
                type: "post",
                url: "/home/friend/recommend",
                data: {
                    _xsrf: getCookie("_xsrf")
                },
                dataType: "json",
                success: function(data, textStatus, jqXHR) {
                    $("#random-recommend-block").replaceWith(data.html);
                },
                error: function(jqXHR, textStatus, errorThrown) {}
            });
        }
    };

    $(document).ready(function() {
        $(".home-navbar-item").live({
            mouseenter: function() {
                $($(this).children()[0]).addClass('red-color-force');
            },
            mouseleave: function() {
                $($(this).children()[0]).removeClass('red-color-force');
            }
        });

        $(".message-collapse li").live({
            mouseenter: function() {
                $($(this).children()[0]).addClass('red-color-force');
            },
            mouseleave: function() {
                $($(this).children()[0]).removeClass('red-color-force');
            }
        });

        $(".home-navbar-item").click(function() {
            window.location.href=$(this).children()[0].href;
        });

        $(".message-collapse li").click(function(e){
            window.location.href=$(this).children()[0].href;
            return false;
        });
        $("#friend-recommend-link").live("click", Controller.recommendFriend);
    });

}(jQuery));
