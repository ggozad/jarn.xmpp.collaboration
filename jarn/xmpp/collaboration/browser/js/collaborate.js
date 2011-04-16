jarnxmpp.ce = {

    NS : 'http://jarn.com/ns/collaborative-editing',
    dmp : new diff_match_patch(),
    shadow_copies: {},
    last_update: {},

    _setup: function() {
        var context_url = $('base').attr('href');
        $.getJSON(context_url + '/@@collaborate', function(data) {
            if (data===null)
                // Not Ceditable.
                return;
            jarnxmpp.ce.component = data.component;
            jarnxmpp.ce.nodeToId = data.nodeToId;
            jarnxmpp.ce.idToNode = data.idToNode;

            jarnxmpp.ce.dmp.Match_Threshold=0.5;
            jarnxmpp.ce.dmp.Patch_DeleteThreshold=0.5;
            jarnxmpp.connection.addHandler(jarnxmpp.ce.patchReceived, null, 'message', null, null, jarnxmpp.ce.component);

            // Setup up nodes.
            for (var key in jarnxmpp.ce.nodeToId)
                if (jarnxmpp.ce.nodeToId.hasOwnProperty(key))
                    jarnxmpp.ce._setupNode(key);

            $(document).bind('jarnxmpp.ce.nodeChanged', jarnxmpp.ce.nodeChanged);

        });
    },

    _setupNode: function (node) {
        var selector = '#' + jarnxmpp.ce.nodeToId[node];
        var text = $(selector).val();
        $(selector).html(text);
        jarnxmpp.ce.shadow_copies[node] = text;
        jarnxmpp.ce.last_update[node] = new Date().getTime();
        var presence = $pres({to: jarnxmpp.ce.component})
            .c('query', {xmlns: jarnxmpp.ce.NS, 'node':node});
        jarnxmpp.connection.send(presence);
        $(selector).addClass('jarnxmpp-ceditable');

    },

    nodeChanged: function (event) {
        var node = event.node;
        var shadow =  jarnxmpp.ce.shadow_copies[node];
        var current = event.text;
        var diff = jarnxmpp.ce.dmp.diff_main(shadow, current, true);
        if (diff.length<2)
            return false;
        jarnxmpp.ce.dmp.diff_cleanupEfficiency(diff);
        var patch_list = jarnxmpp.ce.dmp.patch_make(shadow, current, diff);
        var patch_text = jarnxmpp.ce.dmp.patch_toText(patch_list);
        jarnxmpp.ce.shadow_copies[node] = current;

        var message = $msg({to: jarnxmpp.ce.component})
            .c('x', {xmlns: jarnxmpp.ce.NS})
            .c('item', {node: node, action: 'patch'}).t(patch_text);

        jarnxmpp.connection.send(message);

        return false;
    },

    patchReceived: function (msg) {
        $(msg).find('item').each(function () {
            var node = $(this).attr('node');
            var action = $(this).attr('action');
            var selector = '#' + jarnxmpp.ce.nodeToId[node];
            var patch_text = $(this).text();

            if (action === 'patch') {
                //
                // XXX: This should be queued differently including the above...
                //
                $(selector).queue('ce', function() {
                    var patches = jarnxmpp.ce.dmp.patch_fromText(patch_text);
                    var shadow = jarnxmpp.ce.shadow_copies[node];
                    var patch_applications = jarnxmpp.ce.dmp.patch_apply(patches, shadow);
                    shadow = patch_applications[0];
                    var results = patch_applications[1];
                    for (var i in results) {
                        // XXX: Do something about it!
                        if (results[i]!==true) {
                            console.log('Failure at applying patch:'+i+'of '+results.length);
                        }
                    }
                    jarnxmpp.ce.shadow_copies[node] = shadow;
                    $(selector).val(shadow);
                });
                $(selector).dequeue('ce');
            } else if (action === 'set') {
                $(selector).val(patch_text);
                jarnxmpp.ce.shadow_copies[node] = patch_text;
            }
        });
        return true;
    },
};

$('.jarnxmpp-ceditable').live('blur keyup paste', function() {
    var now = new Date().getTime();
    var node = jarnxmpp.ce.idToNode[this.id];
    if ((now-jarnxmpp.ce.last_update[node]) < 500.0) {
        $(this).doTimeout('jarnxmpp.ce.delayedNodeChanged', 500, function() {
            now = new Date().getTime();
            jarnxmpp.ce.last_update[node] = now;
            var event = $.Event('jarnxmpp.ce.nodeChanged');
            event.node = node;
            event.text = $(this).val();
            $(document).trigger(event);
        });
        return true;
    }
    $.doTimeout('jarnxmpp.ce.delayedNodeChanged');
    jarnxmpp.ce.last_update[node] = now;
    var event = $.Event('jarnxmpp.ce.nodeChanged');
    event.node = node;
    event.text = $(this).val();
    $(document).trigger(event);
    return false;
});

$(document).bind('jarnxmpp.connected', function () {
    if ($('form[name="edit_form"]').length) {
        jarnxmpp.ce._setup();
    }
});

