jarnxmpp.ce = {

    NS : 'http://jarn.com/ns/collaborative-editing',
    dmp : new diff_match_patch(),
    shadow_copies: {},

    _setupNode: function (id) {
        var selector = '#' + id;
        var text = $.trim($(selector).text());
        $(selector).text(text);
        jarnxmpp.ce.shadow_copies[id] = text;
        $(selector).attr('contenteditable', true).addClass('jarnxmpp-ceditable');
        var presence = $pres({to: jarnxmpp.ce.component})
            .c('query', {xmlns: jarnxmpp.ce.NS, 'node':id});
        jarnxmpp.connection.send(presence);
    },

    patchReceived: function (msg) {
        $(msg).find('item').each(function () {
            var node = $(this).attr('node');
            var action = $(this).attr('action');
            var selector = '#' + node;
            var patch_text = $(this).text();
            if (action === 'patch') {
                $(selector).queue('ce', function() {
                    var patches = jarnxmpp.ce.dmp.patch_fromText(patch_text);
                    var shadow = jarnxmpp.ce.shadow_copies[node];
                    var results = jarnxmpp.ce.dmp.patch_apply(patches, shadow);
                    var shadow = results[0];
                    jarnxmpp.ce.shadow_copies[node] = shadow;
                    $(selector).text(shadow);
                    $(selector).dequeue('ce');
                });
                $(selector).dequeue('ce');
            }
        });
        return true;
    }
};

$('.jarnxmpp-ceditable').live('focus', function() {
    before = $(this).text();
}).live('blur keyup paste', function() {
    if (before != $(this).text()) {
        $(this).trigger('jarnxmpp.ce.nodeChanged');
    }
});

$('.jarnxmpp-ceditable').live('jarnxmpp.ce.nodeChanged', function (event) {
    var shadow =  jarnxmpp.ce.shadow_copies[this.id];
    var current = $(this).text();
    var diff = jarnxmpp.ce.dmp.diff_main(shadow, current, true);
    if (diff.length<2) return true;
    jarnxmpp.ce.dmp.diff_cleanupSemantic(diff);
    var patch_list = jarnxmpp.ce.dmp.patch_make(shadow, current, diff);
    var patch_text = jarnxmpp.ce.dmp.patch_toText(patch_list);
    jarnxmpp.ce.shadow_copies[this.id] = current;

    var message = $msg({to: jarnxmpp.ce.component})
        .c('x', {xmlns: jarnxmpp.ce.NS})
        .c('item', {node: this.id, action: 'patch'}).t(patch_text);
    jarnxmpp.connection.send(message);
    return true;
});


$(document).bind('jarnxmpp.connected', function () {
    jarnxmpp.ce._setupNode('parent-fieldname-title')
    jarnxmpp.connection.addHandler(jarnxmpp.ce.patchReceived, null, 'message', null, null, jarnxmpp.ce.component);
});

