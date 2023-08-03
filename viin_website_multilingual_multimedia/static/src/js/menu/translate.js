odoo.define('viin_website_multilingual_multimedia.translateMenu', function (require) {
'use strict';

var core = require('web.core');
var translateMenu = require('website.translateMenu');
var weWidgets = require('wysiwyg.widgets');

var AttributeTranslateDialog = translateMenu.AttributeTranslateDialog;

var _t = core._t;


AttributeTranslateDialog.include({
    events: _.extend({}, translateMenu.AttributeTranslateDialog.prototype.events, {
        'click #button-image-translate': '_onClickImageTranslate',
    }),
    /**
     * @override
     */
    start: function () {
        var res = this._super.apply(this, arguments);

        var self = this;
        var translation_attr = 'src'
        _.each(this.translation, function (node, attr) {
            if (attr !== translation_attr) {
                return;
            }
            self.$('input').each(function (index) {
                var $node = $(node);
                if ($node.html() !== this.value) {
                    return
                }
                var $group = $('<div class="form-row"></div>')
                var $inputDiv = $('<div class="col-10"></div>')
                var $buttonDiv = $('<div class="col-2"></div>')
                var $input = $('<input id="input-image-translate" class="form-control" />').val($node.html());
                $input.on('change keyup', function () {
                    var value = $input.val();
                    if (!node.hasAttribute('data-oe-readonly')) {
                        node.classList.add('o_dirty');
                    }
                    $node.html(value).trigger('change', node);
                    if ($node.data('attribute')) {
                        $node.data('$node').attr($node.data('attribute'), value).trigger('translate');
                    }
                    $node.trigger('change');
                });
                var $button = $('<button id="button-image-translate" class="form-control btn btn-primary"/>').text(_t("Select a Media"));
                $inputDiv.append($input);
                $buttonDiv.append($button);
                $group.append($inputDiv).append($buttonDiv);
                $group.replaceAll(self.$('input')[index]);
            });
        });
        return res;
    },
    /**
     * Select media.
     *
    */
    _onClickImageTranslate: function (ev) {
        var self = this;
        var mediaDialog = new weWidgets.MediaDialog(this, {
            noImages: false,
            noVideos: true,
            noIcons: true,
            noDocuments: true,
            res_model: 'ir.ui.view',
        }, null);
        mediaDialog.open();
        mediaDialog.on('save', this, function (image) {
            self.$('input#input-image-translate').val(image.getAttribute('src')).trigger('change');
        });
    },
});


translateMenu.TranslatePageMenu.include({
     /**
     * @override
     */
    start: function () {
        var res = this._super.apply(this, arguments);
        if (this._mustEditTranslations) {
            // add class o_editable to create Tranlation Object
            $('a').filter('[' + 'href' + '*="data-oe-translation-id="]').each(function () {
                if (!this.hasAttribute('data-oe-readonly')) {
                    this.classList.add('o_editable');
                }
            });
            $('img, iframe').filter('[' + 'src' + '*="data-oe-translation-id="]').each(function () {
                if (!this.hasAttribute('data-oe-readonly')) {
                    this.classList.add('o_editable');
                }
                // stop iframe loading
                if (this.tagName === 'IFRAME') {
                    var editableNode = $(this.parentNode.children).filter('.css_editable_mode_display')[0];
                    if (editableNode) {
                        editableNode.style.setProperty('display', 'block', 'important');
                    }
                }
            });
            this._startMediaTranslateMode();
        }
        return res;
    },
    /** Start media translate mode with src selector*/
    _startMediaTranslateMode: async function () {
        var self = this;
        // Override to add src selector
        this.translator.savableSelector = this.translator.savableSelector + ', [src*="data-oe-translation-id="], [href*="data-oe-translation-id="]';
        // Override to add src attrs
        var beforeEditorActiveOrigin = self.translator.options.beforeEditorActive;

        self.translator.options.beforeEditorActive = async () => {
            beforeEditorActiveOrigin.apply(beforeEditorActiveOrigin, arguments);
            self._beforeEditorActiveImage();
            self._beforeEditorActiveIframe();
            self._beforeEditorActiveURL();
        }
    },
    _beforeEditorActiveURL: async function () {
        var self = this;
        var translation_attr = 'href';
        const $editable = self._getEditableArea();
        const translationRegex = /<span [^>]*data-oe-translation-id="([0-9]+)"[^>]*>(.*)<\/span>/;
        let $edited = $();
        const attrEdit = $editable.filter('[' + translation_attr + '*="data-oe-translation-id="]').filter('a');
        attrEdit.each(function () {
            var $node = $(this);
            var translation = $node.data('translation') || {};
            var trans = decodeURIComponent($node.attr(translation_attr));
            $node.attr(translation_attr, trans);
            var match = trans.match(translationRegex);
            if(match === null) {
                // In some cases the closing span tag is lost
                match = trans.match( /<span[^>]*data-oe-translation-id="(\d+)"[^>]*>(.*)/);
            }
            var $trans = $(trans).addClass('d-none o_editable o_editable_translatable_attribute').appendTo('body');
            $trans.data('$node', $node).data('attribute', translation_attr);

            translation[translation_attr] = $trans[0];
            $node.attr(translation_attr, match[2]);

            $node.addClass('o_translatable_attribute').data('translation', translation);
        });
        $edited = $edited.add(attrEdit);
        // mark translatable attributes
        $edited.each(function () {
            var $node = $(this);
            var translation = $node.data('translation');
            _.each(translation, function (node, attr) {
                if (attr !== translation_attr) {
                    return;
                }
                var trans = self._getTranlationObject(node);
                trans.value = (trans.value ? trans.value : $node.attr(attr)).replace(/[ \t\n\r]+/, ' ');
                $node.attr('data-oe-translation-state', (trans.state || 'to_translate'));
            });
        });
        $edited.on('dblclick', function (ev) {
            ev.preventDefault();
            ev.stopPropagation();

            var translateDialog = new AttributeTranslateDialog(this, {}, ev.currentTarget);
            translateDialog.open();
            translateDialog.on('save', this, function (a) {
                if (!this.hasAttribute('data-oe-readonly')) {
                    this.classList.add('o_dirty');
                }
            });
            
        });
    },
    _beforeEditorActiveImage: async function () {
        var self = this;
        var translation_attr = 'src';
        const $editable = self._getEditableArea();
        const translationRegex = /<span [^>]*data-oe-translation-id="([0-9]+)"[^>]*>(.*)<\/span>/;
        let $edited = $();
        const attrEdit = $editable.filter('[' + translation_attr + '*="data-oe-translation-id="]').filter('img');
        attrEdit.each(function () {
            var $node = $(this);
            var translation = $node.data('translation') || {};
            var trans = decodeURIComponent($node.attr(translation_attr));
            $node.attr(translation_attr, trans);
            var match = trans.match(translationRegex);
            if(match === null) {
                // In some cases the closing span tag is lost
                match = trans.match( /<span[^>]*data-oe-translation-id="(\d+)"[^>]*>(.*)/);
            }
            var $trans = $(trans).addClass('d-none o_editable o_editable_translatable_attribute').appendTo('body');
            $trans.data('$node', $node).data('attribute', translation_attr);

            translation[translation_attr] = $trans[0];
            $node.attr(translation_attr, match[2]);

            $node.addClass('o_translatable_attribute').data('translation', translation);
        });
        $edited = $edited.add(attrEdit);
        // mark translatable attributes
        $edited.each(function () {
            var $node = $(this);
            var translation = $node.data('translation');
            _.each(translation, function (node, attr) {
                if (attr !== translation_attr) {
                    return;
                }
                var trans = self._getTranlationObject(node);
                trans.value = (trans.value ? trans.value : $node.attr(attr)).replace(/[ \t\n\r]+/, ' ');
                $node.attr('data-oe-translation-state', (trans.state || 'to_translate'));
            });
        });
        self.translations = [];
        self.$translations = self._getEditableArea().filter('.o_translatable_attribute, .o_translatable_text');
        self.$editables = $('.o_editable_translatable_attribute, .o_editable_translatable_text');

        self.$editables.on('change', function () {
            self.trigger_up('rte_change', {target: this});
        });
        self._markTranslatableNodes();
        this.$translations.filter('input[type=hidden].o_translatable_input_hidden').prop('type', 'text');
    },
    _beforeEditorActiveIframe: async function () {
        var self = this;
        var translation_attr = 'src';
        const $editable = self._getEditableArea();
        const translationRegex = /<span [^>]*data-oe-translation-id="([0-9]+)"[^>]*>(.*)<\/span>/;
        let $edited = $();
        const attrEdit = $editable.filter('[' + translation_attr + '*="data-oe-translation-id="]').filter('iframe');
        attrEdit.each(function () {
            var $node = $(this);
            var translation = $node.data('translation') || {};
            var trans = decodeURIComponent($node.attr(translation_attr));
            $node.attr(translation_attr, trans);
            var match = trans.match(translationRegex);
            if(match === null) {
                // In some cases the closing span tag is lost
                match = trans.match( /<span[^>]*data-oe-translation-id="(\d+)"[^>]*>(.*)/);
            }
            var $trans = $(trans).addClass('d-none o_editable o_editable_translatable_attribute').appendTo('body');
            $trans.data('$node', $node).data('attribute', translation_attr);

            translation[translation_attr] = $trans[0];
            $node.attr(translation_attr, match[2]);

            $node.addClass('o_translatable_attribute').data('translation', translation);
        });
        $edited = $edited.add(attrEdit);
        // mark translatable attributes
        $edited.each(function () {
            var $node = $(this);
            var translation = $node.data('translation');
            _.each(translation, function (node, attr) {
                if (attr !== translation_attr) {
                    return;
                }
                var trans = self._getTranlationObject(node);
                trans.value = (trans.value ? trans.value : $node.attr(attr)).replace(/[ \t\n\r]+/, ' ');
                $node.attr('data-oe-translation-state', (trans.state || 'to_translate'));
            });
        });
        if ($edited[0] && $edited[0].parentNode) {
            $($edited[0].parentNode).on('click dblclick', function (e) {
                e.preventDefault();
                e.stopPropagation();

                $(this).attr('data-oe-expression', $edited[0].src);
                var mediaDialog = new weWidgets.MediaDialog(self, {
                    noImages: true,
                    noVideos: false,
                    noIcons: true,
                    noDocuments: true,
                    res_model: 'ir.ui.view',
                }, this);
                mediaDialog.open();
                mediaDialog.on('save', this, function (video) {
                    let new_src = $(video).attr('data-oe-expression');
                    $($edited[0].parentNode).attr('data-oe-expression', new_src);
                    $edited[0].src = new_src;
                    var translation = $edited.data('translation');
                    _.each(translation, function (node, attr) {
                        if (attr !== translation_attr) {
                            return;
                        }
                        if (!node.hasAttribute('data-oe-readonly')) {
                            node.classList.add('o_dirty');
                        }
                        let $node = $(node);
                        $node.html(new_src).trigger('change', node);
                        if ($node.data('attribute')) {
                            $node.data('$node').attr($node.data('attribute'), new_src).trigger('translate');
                        }
                        $node.trigger('change');
                        });
                });
            });
        }
    },
});

});
