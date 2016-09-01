function is_null(str) {
    return !str || str.replace(/(^\s*)|(\s*$)/g, "").length == 0;
}

function cleanHTML(html) {
    return html && html.replace(
        /(<br>|\s|<div>|<\/div>|&nbsp;|<pre>|<\/pre>|<code>|<\/code>|<span>|<\/span>)/g,
        ''
    );
}

function array_unique(arr) {
    var a = [], o = {}, i, v, len = arr.length;

    if (len < 2) {
        return arr;
    }

    for (i = len - 1; i >= 0; i--) {
        v = arr[i];
        if (o[v] !== 1) {
            a.unshift(v);
            o[v] = 1;
        }
    }
    return a;
}

function array_remove_all(arr, value) {
    var a = [];
    for (var i = 0; i < arr.length; i++) {
        if (arr[i] != value) {
            a.push(arr[i]);
        }
    }
    return a;
}

function validateEmail(email) {
    var re = /^(([^<>()[\]\\.,;:\s@\"]+(\.[^<>()[\]\\.,;:\s@\"]+)*)|(\".+\"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
    return re.test(email);
}


function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

function unicode_to_utf8(str) {
    return unescape(str.replace(/\\u/gi, '%u'));
};

function font_number(str) {
    var regex = /\w+/g;
    if (!!str) {
        var words = str.match(regex);
        for(var w in words) {
            if (w.length > 50) {
                return str.length;
            }
        }

        str = str.replace(regex, "");

        var _words_cnt = 0;
        if(words){
            _words_cnt = words.length;
        }
        return _words_cnt + str.length;
    }
    return 0;
}

// http://blog.csdn.net/coder_andy/article/details/6202231.
jQuery.fn.extend({
    getCurPos: function() {
        var e = $(this).get(0);
        e.focus();
        if (e.selectionStart) {
            //FF
            return e.selectionStart;
        }

        if (document.selection) {
            //IE
            var r = document.selection.createRange();
            if (r == null) {
                return e.value.length;
            }

            var re = e.createTextRange();
            var rc = re.duplicate();

            re.moveToBookmark(r.getBookmark());
            rc.setEndPoint('EndToStart', re);
            return rc.text.length;
        }
        return e.value.length;
    },
    setCurPos: function(pos) {
        var e = $(this).get(0);
        e.focus();

        if (e.setSelectionRange) {
            e.setSelectionRange(pos, pos);
        } else if (e.createTextRange) {
            var range = e.createTextRange();

            range.collapse(true);
            range.moveEnd('character', pos);
            range.moveStart('character', pos);
            range.select();
        }
    }
});
