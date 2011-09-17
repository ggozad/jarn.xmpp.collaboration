jarnxmpp.ce = {

    NS : 'http://jarn.com/ns/collaborative-editing',
    dmp : new diff_match_patch(),
    shadow_copies: {},
    last_update: {},
    tiny_ids: {},
    paused_nodes: {},
    participants: {},
    focused_node: null,

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
            jarnxmpp.connection.addHandler(jarnxmpp.ce.messageReceived, null, 'message', null, null, jarnxmpp.ce.component);
            jarnxmpp.connection.addHandler(jarnxmpp.ce.onPatchIQ, jarnxmpp.ce.NS, 'iq', 'set', null, jarnxmpp.ce.component);

            // Setup up nodes.
            for (var key in jarnxmpp.ce.nodeToId)
                if (jarnxmpp.ce.nodeToId.hasOwnProperty(key))
                    jarnxmpp.ce._setupNode(key);

            $(document).bind('jarnxmpp.ce.nodeChanged', jarnxmpp.ce.sendPatch);
        });
    },

    _setupNode: function (node) {
        var node_id = jarnxmpp.ce.nodeToId[node];
        var jqid = jarnxmpp.ce._jqID(node_id);
        var text = jarnxmpp.ce._getContent(node_id);
        jarnxmpp.ce.shadow_copies[node] = text;
        jarnxmpp.ce.last_update[node] = new Date().getTime();
        var presence = $pres({to: jarnxmpp.ce.component})
            .c('query', {xmlns: jarnxmpp.ce.NS, 'node':node});
        jarnxmpp.connection.send(presence);
        var editor = window.tinyMCE.getInstanceById(node_id);

        if (editor!==undefined) {
            jarnxmpp.ce.tiny_ids[node_id] = '';
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
            $(jqid).bind('blur keyup paste', function () {
                jarnxmpp.ce.nodeChanged(this.id);
            });
            $(jqid).bind('focus', function() {
                jarnxmpp.ce.nodeFocused(jarnxmpp.ce.idToNode[this.id]);
            });
        }
        $(jqid).before($('<div>').attr('id', node_id + '-participants').addClass('node-participants'));
        jarnxmpp.ce._getShadowCopy(node);
    },

    _getShadowCopy: function(node) {
        var sc_iq = $iq({type: 'get', to: jarnxmpp.ce.component})
            .c('shadowcopy', {xmlns: jarnxmpp.ce.NS, node: node});
        jarnxmpp.connection.sendIQ(sc_iq,
            function(response) {
                var node_id = jarnxmpp.ce.nodeToId[node];
                var selector = jarnxmpp.ce._jqID(node_id);
                var text = $(response).find(">:first-child").text();
                jarnxmpp.ce._setContent(node_id, text);
                jarnxmpp.ce.shadow_copies[node] = text;
            },
            function(error) {
               console.log(error);
            });
    },

    _getContent: function (node_id) {
        if (node_id in jarnxmpp.ce.tiny_ids) {
            var editor = window.tinyMCE.getInstanceById(node_id);
            if (editor!==undefined)
                return editor.getContent();
        } else {
            return $(jarnxmpp.ce._jqID(node_id)).val();
        }
    },

    _setContent: function (node_id, content) {
        if (node_id in jarnxmpp.ce.tiny_ids) {
            var editor = window.tinyMCE.getInstanceById(node_id);
            editor.setContent(content);
        } else
            $(jarnxmpp.ce._jqID(node_id)).val(content);
    },

    _applyPatches: function (node_id, content, patches, user_jid) {
        var node = jarnxmpp.ce.idToNode[node_id];
        var jqid = jarnxmpp.ce._jqID(node_id);
        if (jarnxmpp.ce.focused_node === node) {
            var caret_id = 'caret-' + Math.floor(Math.random()*100000);
            var selection, bookmark_content;
            if (node_id in jarnxmpp.ce.tiny_ids) {
                var editor = window.tinyMCE.getInstanceById(node_id);
                // If we are inside the node as well we need some special care.
                // First we set a bookmark element. Then apply the patches, then remove the bookmark.
                jarnxmpp.ce.paused_nodes[node_id] = '';
                var caret_element = editor.dom.createHTML('a', {'id': caret_id, 'class': 'mceNoEditor'}, ' ');
                selection = editor.selection;
                editor.selection.setContent(caret_element);
                // Maybe this will do for IE instead of the above? Need to test
                //editor.execCommand('mceInsertContent', false, caret_element);
                bookmark_content = editor.getContent();
                content = jarnxmpp.ce.dmp.patch_apply(patches, bookmark_content)[0];
                editor.setContent(content);

                var doc = editor.getDoc();
                var range = doc.createRange();
                caret_element = doc.getElementById(caret_id);
                range.selectNode(caret_element);
                editor.selection.setRng(range);
                editor.selection.collapse(0);
                delete jarnxmpp.ce.paused_nodes[node_id];
                var bm = editor.selection.getBookmark(0, true);
                editor.dom.remove(caret_element);
                editor.selection.moveToBookmark(bm);
                editor.focus();
            } else {
                selection = $(jqid).getSelection();
                selection.end = selection.start;
                bookmark_content = $(jqid).val();
                bookmark_content = bookmark_content.substr(0,selection.start) +
                    caret_id + bookmark_content.substr(selection.start);
                content = jarnxmpp.ce.dmp.patch_apply(patches, bookmark_content)[0];
                var new_start = content.search(caret_id);
                content = content.replace(caret_id, '');
                jarnxmpp.ce._setContent(node_id, content);
                $(jqid).setSelection(new_start, new_start + selection.length);
            }
        } else {
            // The field has no focus, just set the content
            jarnxmpp.ce._setContent(node_id, content);
        }
        var participant_id = 'node-participant-' + jarnxmpp.ce._idFromJID(user_jid);
        participant_id = jarnxmpp.ce._jqID(participant_id);
        $(participant_id).fadeTo('fast', 0.1);
        $(participant_id).fadeTo('fast', 1.0);
    },

    _updateFocus: function(node_id, jid) {
        var participant_id = 'node-participant-' + jarnxmpp.ce._idFromJID(jid);
        $('#' + participant_id).remove();

        var user_id = Strophe.getNodeFromJid(jid);
        if (node_id !=='') {
            jarnxmpp.Presence.getUserInfo(user_id, function(data) {
                var participant_element = $('<img/>')
                    .attr('id', participant_id)
                    .attr('title', data.fullname)
                    .attr('src', data.portrait_url)
                    .addClass('node-participant');
                $(jarnxmpp.ce._jqID(node_id + '-participants')).append(participant_element);
            });
        }
    },

    _jqID: function (id) {
       return '#' + id.replace(/(:|\.)/g,'\\$1');
     },

    _idFromJID: function(jid) {
        return Strophe.getNodeFromJid(jid) + Strophe.getResourceFromJid(jid);
    },

    _userJoined: function(jid) {
        var user_id = Strophe.getNodeFromJid(jid);
        if (jid in jarnxmpp.ce.participants) return;
        jarnxmpp.ce.participants[jid] = '';
        jarnxmpp.Presence.getUserInfo(user_id, function(data) {
            $.gritter.add({
                title: 'Also editing this document',
                text: data.fullname,
                image: data.portrait_url,
                sticky: false,
                time: 3000,
            });

        });
    },

    _userLeft: function(jid) {
        var user_id = Strophe.getNodeFromJid(jid);
        if (!(jid in jarnxmpp.ce.participants)) return;
        delete jarnxmpp.ce.participants[jid];
        var participant_id = 'node-participant-' + jarnxmpp.ce._idFromJID(jid);
        participant_id = jarnxmpp.ce._jqID(participant_id);
        $(participant_id).remove();

        jarnxmpp.Presence.getUserInfo(user_id, function(data) {
            $.gritter.add({
                title: 'The user is no longer editing this document',
                text: data.fullname,
                image: data.portrait_url,
                sticky: false,
                time: 3000,
            });

        });
    },

    onPatchIQ: function (iq) {
        var iq_id = $(iq).attr('id');
        $(iq).find('>patch:first').each(function () {
            var node = $(this).attr('node');
            var node_id = jarnxmpp.ce.nodeToId[node];
            var patch_text = $(this).text();
            var user_jid = $(this).attr('user');
            var selector = jarnxmpp.ce._jqID(node_id);
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
                    $.gritter.add({
                        title: 'Error',
                        text: 'An error occured, resetting text...',
                        sticky: false,
                        time: 3000,
                    });
                    jarnxmpp.ce._getShadowCopy(node);
                    return true;
                }
            });
            // Set shadow
            jarnxmpp.ce.shadow_copies[node] = shadow;
            jarnxmpp.ce._applyPatches(node_id, shadow, patches, user_jid);
            var response = $iq({type: 'result', to: jarnxmpp.ce.component, id: iq_id})
                .c('success', {xmlns: jarnxmpp.ce.NS});
            jarnxmpp.connection.send(response);
        });
        return true;
    },

    nodeChanged: function (node_id) {
        if (node_id in jarnxmpp.ce.paused_nodes) return;
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
        jarnxmpp.ce.focused_node = node;
        var message = $msg({to: jarnxmpp.ce.component})
            .c('x', {xmlns: jarnxmpp.ce.NS})
            .c('item', {node: node, action: 'focus', user: jarnxmpp.connection.jid});
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

        var iq = $iq({type: 'set', to: jarnxmpp.ce.component})
            .c('patch', {xmlns: jarnxmpp.ce.NS, node: node}, patch_text);
        jarnxmpp.connection.sendIQ(iq,
            function (response) {},
            function(error) {
               console.log(error);
            });
        return false;
    },

    messageReceived: function (msg) {
        $(msg).find('item').each(function () {
            var node = $(this).attr('node');
            var action = $(this).attr('action');
            var patch_text = $(this).text();
            var user_jid = $(this).attr('user');
            var node_id = jarnxmpp.ce.nodeToId[node];
            if (action === 'focus') {
                jarnxmpp.ce._updateFocus(node_id, user_jid);
            } else if (action === 'user-joined') {
                jarnxmpp.ce._userJoined(user_jid);
            } else if (action === 'user-left') {
                jarnxmpp.ce._userLeft(user_jid);
            }

        });
        return true;
    },
};

$(document).bind('jarnxmpp.connected', function () {
    if (($('form[name="edit_form"]').length &&
        $('base').attr('href').indexOf('portal_factory')===-1) ||
        $('body').hasClass('template-edit')) {
        jarnxmpp.ce._setup();
    }
});

