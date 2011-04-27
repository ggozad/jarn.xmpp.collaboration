jarnxmpp.ce = {

    NS : 'http://jarn.com/ns/collaborative-editing',
    dmp : new diff_match_patch(),
    shadow_copies: {},
    last_update: {},
    tiny_ids: {},

    _setup: function() {
        var context_url = $('base').attr('href');
        $.getJSON(context_url + '/@@collaborate', function(data) {
            if (data===null)
                // Not Ceditable.
                return;
            jarnxmpp.ce.component = data.component;
            jarnxmpp.ce.nodeToId = data.nodeToId;
            jarnxmpp.ce.idToNode = data.idToNode;
            $.each(data.tiny_ids, function (index, value) {
                    jarnxmpp.ce.tiny_ids[value] = '';
            });
            jarnxmpp.ce.dmp.Match_Threshold=0.5;
            jarnxmpp.ce.dmp.Patch_DeleteThreshold=0.5;
            jarnxmpp.connection.addHandler(jarnxmpp.ce.messageReceived, null, 'message', null, null, jarnxmpp.ce.component);

            // Setup up nodes.
            for (var key in jarnxmpp.ce.nodeToId)
                if (jarnxmpp.ce.nodeToId.hasOwnProperty(key))
                    jarnxmpp.ce._setupNode(key);

            $(document).bind('jarnxmpp.ce.nodeChanged', jarnxmpp.ce.sendPatch);
            //jarnxmpp.ce.nodeFocused(jarnxmpp.ce.idToNode[$('*:focus').attr('id')]);
            $('*:focus').each(function () {
                jarnxmpp.ce.nodeFocused(jarnxmpp.ce.idToNode[this.id]);
            });
        });
    },

    _setupNode: function (node) {
        var node_id = jarnxmpp.ce.nodeToId[node];
        var text = jarnxmpp.ce._getContent(node_id);
        jarnxmpp.ce.shadow_copies[node] = text;
        jarnxmpp.ce.last_update[node] = new Date().getTime();
        var presence = $pres({to: jarnxmpp.ce.component})
            .c('query', {xmlns: jarnxmpp.ce.NS, 'node':node});
        jarnxmpp.connection.send(presence);
        if (node_id in jarnxmpp.ce.tiny_ids) {
            var editor = window.tinyMCE.getInstanceById(node_id);
            editor.onKeyUp.add(function (ed, l) {
                jarnxmpp.ce.nodeChanged(editor.id);
            });
            editor.onChange.add(function (ed, l) {
                jarnxmpp.ce.nodeChanged(editor.id);
            });
            editor.onActivate.add(function (ed) {
                jarnxmpp.ce.nodeFocused(jarnxmpp.ce.idToNode[editor.id]);
            });
        }  else {
            $('#' + node_id).bind('blur keyup paste', function () {
                jarnxmpp.ce.nodeChanged(this.id);
            });
            $('#' + node_id).bind('focus', function() {
                jarnxmpp.ce.nodeFocused(jarnxmpp.ce.idToNode[this.id]);
            });
        }
        $('#' + node_id).before($('<div>').attr('id', node_id + '-participants').addClass('node-participants'));
    },

    _getContent: function (node_id) {
        if (node_id in jarnxmpp.ce.tiny_ids) {
            var editor = window.tinyMCE.getInstanceById(node_id);
            if (editor!==undefined)
                return editor.getContent();
        } else {
            return $('#' + node_id).val();
        }
    },

    _setContent: function (node_id, content) {
        if (node_id in jarnxmpp.ce.tiny_ids) {
            var editor = window.tinyMCE.getInstanceById(node_id);
            editor.setContent(content);
        } else {
            $('#' + node_id).val(content);
        }
    },

    _getSelection: function(node_id) {
        if (node_id in jarnxmpp.ce.tiny_ids) {
            var editor = window.tinyMCE.getInstanceById(node_id);
            return editor.selection.getBookmark();
        } else
            return $('#' + node_id).getSelection();
    },

    _setSelection: function(node_id, selection) {
        if (node_id in jarnxmpp.ce.tiny_ids) {
            var editor = window.tinyMCE.getInstanceById(node_id);
            return editor.selection.moveToBookmark(selection);
        } else
            return $('#' + node_id).setSelection(selection.start, selection.end);
    },

    _updateFocus: function(node_id, jid) {
        var participant_id = 'node-participant-' + Strophe.getNodeFromJid(jid) + Strophe.getDomainFromJid(jid) + Strophe.getResourceFromJid(jid);
        $('#' + participant_id).remove();
        var participant_element = $('<span>').attr('id', participant_id).addClass('node-participant').text(jid);
        $('#' + node_id + '-participants').append(participant_element);
        console.log(node_id + ' ' + jid);
    },

    nodeChanged: function (node_id) {
        var now = new Date().getTime();
        var node = jarnxmpp.ce.idToNode[node_id];
        if ((now-jarnxmpp.ce.last_update[node]) < 500.0) {
            $(this).doTimeout('jarnxmpp.ce.delayedNodeChanged', 500, function() {
                now = new Date().getTime();
                jarnxmpp.ce.last_update[node] = now;
                var event = $.Event('jarnxmpp.ce.nodeChanged');
                event.node = node;
                event.text = jarnxmpp.ce._getContent(node_id);
                $(document).trigger(event);
            });
            return true;
        }
        $.doTimeout('jarnxmpp.ce.delayedNodeChanged');
        jarnxmpp.ce.last_update[node] = now;
        var event = $.Event('jarnxmpp.ce.nodeChanged');
        event.node = node;
        event.text = jarnxmpp.ce._getContent(node_id);
        $(document).trigger(event);
        return false;
    },

    nodeFocused: function (node) {
        var message = $msg({to: jarnxmpp.ce.component})
            .c('x', {xmlns: jarnxmpp.ce.NS})
            .c('item', {node: node, action: 'focus'});
        jarnxmpp.connection.send(message);
        jarnxmpp.ce._updateFocus(jarnxmpp.ce.nodeToId[node], jarnxmpp.connection.jid);
    },

    sendPatch: function (event) {
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

    messageReceived: function (msg) {
        $(msg).find('item').each(function () {
            var node = $(this).attr('node');
            var action = $(this).attr('action');
            var node_id = jarnxmpp.ce.nodeToId[node];
            var selector = '#' + node_id;
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
                    $.each(results, function (index, value) {
                        // XXX: Do something about it!
                        if (value!==true)
                            console.log('Failure at applying patch:' + index + 'of '+results.length);
                    });
                    // Set shadow
                    jarnxmpp.ce.shadow_copies[node] = shadow;
                    // Before setting the content predict where the cursor should be
                    //var selection = jarnxmpp.ce._getSelection(node_id);
                    jarnxmpp.ce._setContent(node_id, shadow);
                    //jarnxmpp.ce._setSelection(node_id, selection);
                });
                $(selector).dequeue('ce');
            } else if (action === 'set') {
                jarnxmpp.ce._setContent(node_id, patch_text);
                jarnxmpp.ce.shadow_copies[node] = patch_text;
            } else if (action === 'focus') {
                var user_jid = $(this).attr('user');
                jarnxmpp.ce._updateFocus(node_id, user_jid);
            }
        });
        return true;
    },
};

$(document).bind('jarnxmpp.connected', function () {
    if ($('form[name="edit_form"]').length &&
        $('base').attr('href').indexOf('portal_factory')===-1) {
        jarnxmpp.ce._setup();
    }
});

