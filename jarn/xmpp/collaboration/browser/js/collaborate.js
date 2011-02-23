jarnxmpp.ce = {

    NS : 'http://jarn.com/ns/collaborative-editing',
    dmp : new diff_match_patch(),
    shadow_copies: {},
    last_update: {},

    _setupNode: function (id) {
        var selector = '#' + id;
        var text = $.trim($(selector).text());
        $(selector).text(text);
        jarnxmpp.ce.shadow_copies[id] = text;
        jarnxmpp.ce.last_update[id] = new Date().getTime();
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
                //
                // XXX: This should be queued differently including the above...
                //
                $(selector).queue('ce', function() {
                    var patches = jarnxmpp.ce.dmp.patch_fromText(patch_text);
                    var shadow = jarnxmpp.ce.shadow_copies[node];
                    var patch_applications = jarnxmpp.ce.dmp.patch_apply(patches, shadow);
                    var shadow = patch_applications[0];
                    var results = patch_applications[1];
                    for (var i in results) {
                        // XXX: Do something about it!
                        if (results[i]!=true) {
                            console.log('Failure at applying patch:'+i+'of '+results.length);
                        }
                    }
                    jarnxmpp.ce.shadow_copies[node] = shadow;
                    $(selector).text(shadow);
                });
                $(selector).dequeue('ce');
            }
        });
        return true;
    }
};

$('.jarnxmpp-ceditable').live('blur keyup paste', function() {
    var now = new Date().getTime();
    if ((now-jarnxmpp.ce.last_update[this.id]) < 500.0) {
        $(this).doTimeout('jarnxmpp.ce.delayedNodeChanged', 500, function() {
            var now = new Date().getTime();
            jarnxmpp.ce.last_update[this.id] = now;
            $(this).trigger('jarnxmpp.ce.nodeChanged');
        });
        return true;
    }
    $.doTimeout('jarnxmpp.ce.delayedNodeChanged');
    jarnxmpp.ce.last_update[this.id] = now;
    $(this).trigger('jarnxmpp.ce.nodeChanged');
    return true;
});

$('.jarnxmpp-ceditable').live('jarnxmpp.ce.nodeChanged', function (event) {
    var shadow =  jarnxmpp.ce.shadow_copies[this.id];
    var current = $(this).text();
    var diff = jarnxmpp.ce.dmp.diff_main(shadow, current, true);
    if (diff.length<2) return true;
    jarnxmpp.ce.dmp.diff_cleanupEfficiency(diff);
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
    jarnxmpp.ce.dmp.Match_Threshold=0.5;
    jarnxmpp.ce.dmp.Patch_DeleteThreshold=0.5;
    jarnxmpp.ce._setupNode('parent-fieldname-title')
    jarnxmpp.connection.addHandler(jarnxmpp.ce.patchReceived, null, 'message', null, null, jarnxmpp.ce.component);
});

