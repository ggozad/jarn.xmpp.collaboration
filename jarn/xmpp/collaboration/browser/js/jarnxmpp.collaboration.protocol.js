jarnxmpp.ce = jarnxmpp.ce || {};

jarnxmpp.ce.NS = 'http://jarn.com/ns/collaborative-editing';
jarnxmpp.ce.dmp = new diff_match_patch();
jarnxmpp.ce.dmp.Match_Threshold=0.5;
jarnxmpp.ce.dmp.Patch_DeleteThreshold=0.5;
jarnxmpp.ce.shadow_copies = {};

jarnxmpp.ce.getDigest = function(text) {
    // Convert to utf-8 and return the hexdigest
    return MD5.hexdigest(unescape(encodeURIComponent(text)));
};

jarnxmpp.ce.msgReceived = function (msg) {
    $(msg).find('item').each(function () {
        var node = $(this).attr('node'),
            action = $(this).attr('action'),
            user_jid = $(this).attr('user'),
            ev;
        if (action === 'focus') {
            ev = $.Event('jarnxmpp.ce.nodeFocus');
            ev.node = node;
            ev.jid = user_jid;
            $(document).trigger(ev);
        } else if (action === 'user-joined') {
            ev = $.Event('jarnxmpp.ce.userJoined');
            ev.jid = user_jid;
            $(document).trigger(ev);
        } else if (action === 'user-left') {
            ev = $.Event('jarnxmpp.ce.userLeft');
            ev.jid = user_jid;
            $(document).trigger(ev);
        }
    });
    return true;
};

jarnxmpp.ce.iqReceived = function (iq) {
    var iq_id = $(iq).attr('id');
    $(iq).find('>patch:first').each(function () {
        var node = $(this).attr('node'),
            patch_text = $(this).text(),
            user_jid = $(this).attr('user'),
            patches = jarnxmpp.ce.dmp.patch_fromText(patch_text),
            shadow = jarnxmpp.ce.shadow_copies[node],
            patch_applications = jarnxmpp.ce.dmp.patch_apply(patches, shadow),
            results;

        shadow = patch_applications[0];
        results = patch_applications[1];
        $.each(results, function (index, value) {
            if (value!==true) {
                var response = $iq({type: 'error', to: jarnxmpp.ce.component, id: iq_id})
                    .c('error', {xmlns: jarnxmpp.ce.NS}),
                    ev;
                jarnxmpp.connection.send(response);
                ev = $.Event('jarnxmpp.ce.error');
                ev.text = 'Error applying patch. Resetting text...';
                $(document).trigger(ev);
                jarnxmpp.ce.getShadowCopy(node);
                return true;
            }
        });
        // Set shadow
        jarnxmpp.ce.shadow_copies[node] = shadow;
        var ev = $.Event('jarnxmpp.ce.applyPatch');
        ev.node = node;
        ev.shadow = shadow;
        ev.patches = patches;
        ev.jid = user_jid;
        $(document).trigger(ev);
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
    var node = event.node,
        shadow =  jarnxmpp.ce.shadow_copies[node],
        current = event.text,
        diff = jarnxmpp.ce.dmp.diff_main(shadow, current, true),
        patch_list,
        patch_text,
        digest,
        iq;
    if (diff.length<2)
        return false;
    jarnxmpp.ce.dmp.diff_cleanupEfficiency(diff);
    patch_list = jarnxmpp.ce.dmp.patch_make(shadow, current, diff);
    patch_text = jarnxmpp.ce.dmp.patch_toText(patch_list);
    jarnxmpp.ce.shadow_copies[node] = current;
    digest = jarnxmpp.ce.getDigest(current);
    iq = $iq({type: 'set', to: jarnxmpp.ce.component})
        .c('patch', {xmlns: jarnxmpp.ce.NS, node: node, digest: digest})
        .t(patch_text);
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

jarnxmpp.ce.checkDigest = function (node) {
    var shadow =  jarnxmpp.ce.shadow_copies[node],
        digest = jarnxmpp.ce.getDigest(shadow),
        iq = $iq({type: 'get', to: jarnxmpp.ce.component})
        .c('checksum', {xmlns: jarnxmpp.ce.NS, node: node, digest: digest});
    jarnxmpp.connection.sendIQ(iq,
        function (response) {
            console.log(response);
        },
        function(error) {
            console.log(error);
        });
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