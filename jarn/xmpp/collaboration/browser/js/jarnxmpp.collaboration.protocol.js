jarnxmpp.ce = jarnxmpp.ce || {};

jarnxmpp.ce.NS = 'http://jarn.com/ns/collaborative-editing';
jarnxmpp.ce.dmp = new diff_match_patch();
jarnxmpp.ce.dmp.Match_Threshold=0.5;
jarnxmpp.ce.dmp.Patch_DeleteThreshold=0.5;
jarnxmpp.ce.shadow_copies = {};

jarnxmpp.ce.msgReceived = function (msg) {
    $(msg).find('item').each(function () {
        var node = $(this).attr('node');
        var action = $(this).attr('action');
        var user_jid = $(this).attr('user');
        var event;
        if (action === 'focus') {
            event = $.Event('jarnxmpp.ce.nodeFocus');
            event.node = node;
            event.jid = user_jid;
            $(document).trigger(event);
        } else if (action === 'user-joined') {
            event = $.Event('jarnxmpp.ce.userJoined');
            event.jid = user_jid;
            $(document).trigger(event);
        } else if (action === 'user-left') {
            event = $.Event('jarnxmpp.ce.userLeft');
            event.jid = user_jid;
            $(document).trigger(event);
        }
    });
    return true;
};

jarnxmpp.ce.iqReceived = function (iq) {
    var iq_id = $(iq).attr('id');
    $(iq).find('>patch:first').each(function () {
        var node = $(this).attr('node');
        var patch_text = $(this).text();
        var user_jid = $(this).attr('user');
        var patches = jarnxmpp.ce.dmp.patch_fromText(patch_text);
        var shadow = jarnxmpp.ce.shadow_copies[node];
        var patch_applications = jarnxmpp.ce.dmp.patch_apply(patches, shadow);
        shadow = patch_applications[0];
        var results = patch_applications[1];
        $.each(results, function (index, value) {
            if (value!==true) {
                var response = $iq({type: 'error', to: jarnxmpp.ce.component, id: iq_id})
                    .c('error', {xmlns: jarnxmpp.ce.NS});
                jarnxmpp.connection.send(response);
                var event = $.Event('jarnxmpp.ce.error');
                event.text = 'Error applying patch. Resetting text...';
                $(document).trigger(event);
                jarnxmpp.ce.getShadowCopy(node);
                return true;
            }
        });
        // Set shadow
        jarnxmpp.ce.shadow_copies[node] = shadow;
        var event = $.Event('jarnxmpp.ce.applyPatch');
        event.node = node;
        event.shadow = shadow;
        event.patches = patches;
        event.jid = user_jid;
        $(document).trigger(event);
        var response = $iq({type: 'result', to: jarnxmpp.ce.component, id: iq_id})
            .c('success', {xmlns: jarnxmpp.ce.NS});
        jarnxmpp.connection.send(response);
    });
    return true;
};

jarnxmpp.ce.sendPresence = function (node) {
    var presence = $pres({to: jarnxmpp.ce.component})
        .c('query', {xmlns: jarnxmpp.ce.NS, 'node':node});
    jarnxmpp.connection.send(presence);
};

jarnxmpp.ce.getShadowCopy = function(node) {
    var sc_iq = $iq({type: 'get', to: jarnxmpp.ce.component})
        .c('shadowcopy', {xmlns: jarnxmpp.ce.NS, node: node});
    jarnxmpp.connection.sendIQ(sc_iq,
        function(response) {
            var text = $(response).find(">:first-child").text();
            jarnxmpp.ce._setContent(node, text);
            jarnxmpp.ce.shadow_copies[node] = text;
        },
        function(error) {
           console.log(error);
        }
    );
};

jarnxmpp.ce.sendPatch = function (event) {
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

    var iq = $iq({type: 'set', to: jarnxmpp.ce.component})
        .c('patch', {xmlns: jarnxmpp.ce.NS, node: node}, patch_text);
    jarnxmpp.connection.sendIQ(iq,
        function (response) {},
        function(error) {
            var event = $.Event('jarnxmpp.ce.error');
            event.text = 'Error applying patch. Resetting text...';
            $(document).trigger(event);
            jarnxmpp.ce.getShadowCopy(node);
        });
    return false;
};

jarnxmpp.ce.sendNodeFocus = function(node, user) {
    var message = $msg({to: jarnxmpp.ce.component})
        .c('x', {xmlns: jarnxmpp.ce.NS})
        .c('item', {node: node, action: 'focus', user: user});
    jarnxmpp.connection.send(message);
};

$(document).bind('jarnxmpp.connected', function () {
    jarnxmpp.connection.addHandler(jarnxmpp.ce.msgReceived, null, 'message', null, null, jarnxmpp.ce.component);
    jarnxmpp.connection.addHandler(jarnxmpp.ce.iqReceived, jarnxmpp.ce.NS, 'iq', 'set', null, jarnxmpp.ce.component);
});