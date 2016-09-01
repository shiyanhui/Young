;(function($) {
    "use strict";

    $(document).ready(function(){

        $("input").iCheck({
            checkboxClass: 'icheckbox_minimal-red',
            radioClass: 'iradio_minimal',
        });

        $(".wysiwyg-editor").wysiwyg({
            hotKeys: {}
        });

        $('select[name="category"]').select2({
            width: 415,
            placeholder: '请选择类别'
        });
    });

}(jQuery));
