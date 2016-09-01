;(function($) {
    "use strict";

    $(document).ready(function(){
        var user = new Bloodhound({
            datumTokenizer: Bloodhound.tokenizers.obj.whitespace('name'),
            queryTokenizer: Bloodhound.tokenizers.whitespace,
            limit: 10,
            rateLimitWait: 0,
            remote: {
                url: "/search?category=user&query=%QUERY"
            }
        });

        var topic = new Bloodhound({
            datumTokenizer: Bloodhound.tokenizers.obj.whitespace('name'),
            queryTokenizer: Bloodhound.tokenizers.whitespace,
            limit: 10,
            rateLimitWait: 0,
            remote: {
                url: "/search?category=topic&query=%QUERY"
            }
        });

        var share = new Bloodhound({
            datumTokenizer: Bloodhound.tokenizers.obj.whitespace('name'),
            queryTokenizer: Bloodhound.tokenizers.whitespace,
            limit: 10,
            rateLimitWait: 0,
            remote: {
                url: "/search?category=share&query=%QUERY"
            }
        });

        user.initialize();
        topic.initialize();
        share.initialize();

        $('.search-query').typeahead(null, {
            name: 'user',
            displayKey: 'user',
            source: user.ttAdapter(),
            templates: {
                header: '<div class="tt-header-first">用户</div>',
                suggestion: Handlebars.compile(
                    '<a href="/profile/{{ _id }}" class="black-color"> \
                        <img src="/avatar/{{ _id }}/thumbnail50x50" \
                            class="avatar avatar-mini"> {{ name }}\
                    </a>'
                )
            }
        }, {
            name: 'topic',
            displayKey: 'topic',
            source: topic.ttAdapter(),
            templates: {
                header: '<div class="tt-header">话题</div>',
                suggestion: Handlebars.compile(
                    '<a href="/community/topic/{{ _id }}" \
                        class="black-color"> {{ title }}\
                    </a>'
                )
            }
        }, {
            name: 'share',
            displayKey: 'share',
            source: share.ttAdapter(),
            templates: {
                header: '<div class="tt-header">分享</div>',
                suggestion: Handlebars.compile(
                    '<a href="/share/{{ _id }}" class="black-color"> \
                        {{ title }}\
                    </a>'
                )
            }
        });

        $(".tt-suggestion").live({
            mouseenter: function() {
                $($(this).children()[0]).addClass('red-color-force');
            },
            mouseleave: function() {
                $($(this).children()[0]).removeClass('red-color-force');
            }
        });

        $(".tt-suggestion").live("click", function() {
            window.location.href=$(this).children()[0].href;
        })
    });
}(jQuery));
