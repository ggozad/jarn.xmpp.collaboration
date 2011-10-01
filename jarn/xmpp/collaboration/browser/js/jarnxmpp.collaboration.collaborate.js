jarnxmpp.ce = jarnxmpp.ce || {};
jarnxmpp.ce.tiny_ids = {};
jarnxmpp.ce.last_update = {};
jarnxmpp.ce.paused_nodes = {};
jarnxmpp.ce.focused_node = null;
jarnxmpp.ce.participants = {};

/* Helper functions */

jarnxmpp.ce._jqID = function (id) {
    return '#' + id.replace(/(:|\.)/g,'\\$1');
};

jarnxmpp.ce._idFromJID = function(jid) {
    return Strophe.getNodeFromJid(jid) + Strophe.getResourceFromJid(jid);
};

/* Get/Set content of node */

jarnxmpp.ce._getContent = function (node) {
    var node_id = jarnxmpp.ce.nodeToId[node];
    if (node_id in jarnxmpp.ce.tiny_ids) {
        var editor = window.tinyMCE.getInstanceById(node_id);
        return $(editor.getBody()).html();
    } else {
        return $(jarnxmpp.ce._jqID(node_id)).val();
    }
};

jarnxmpp.ce._setContent = function (node, content) {
    var node_id = jarnxmpp.ce.nodeToId[node];
    if (node_id in jarnxmpp.ce.tiny_ids) {
        var editor = window.tinyMCE.getInstanceById(node_id);
        editor.setContent(content);
    } else
        $(jarnxmpp.ce._jqID(node_id)).val(content);
};


/* Catch node changes but possibly delay them so as to not send more than 1
per sec. Should be possible to do without, but need to investigate as it seems
that when the server is flooded with iqs it might disconnect the client. */

jarnxmpp.ce.nodeBlur = function (node_id) {
    if (node_id in jarnxmpp.ce.paused_nodes) return;
    var now = new Date().getTime();
    var node = jarnxmpp.ce.idToNode[node_id];
    if ((now-jarnxmpp.ce.last_update[node]) < 1000.0) {
        $(this).doTimeout('jarnxmpp.ce.delayedNodeChanged', 1000, function() {
            now = new Date().getTime();
            jarnxmpp.ce.last_update[node] = now;
            var event = $.Event('jarnxmpp.ce.nodeChanged');
            event.node = node;
            event.text = jarnxmpp.ce._getContent(node);
            $(document).trigger(event);
        });
        return true;
    }
    $.doTimeout('jarnxmpp.ce.delayedNodeChanged');
    jarnxmpp.ce.last_update[node] = now;
    var event = $.Event('jarnxmpp.ce.nodeChanged');
    event.node = node;
    event.text = jarnxmpp.ce._getContent(node);
    $(document).trigger(event);
    return false;
};

/* Event handler for applyPatch event */

jarnxmpp.ce.onApplyPatch = function (event) {
    var node = event.node;
    var content = event.shadow;
    var patches = event.patches;
    var user_jid = event.jid;
    var node_id = jarnxmpp.ce.nodeToId[node];
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
            bookmark_content = jarnxmpp.ce._getContent(node);
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
            jarnxmpp.ce._setContent(node, content);
            $(jqid).setSelection(new_start, new_start + selection.length);
        }
    } else {
        // The field has no focus, just set the content
        jarnxmpp.ce._setContent(node, content);
    }
    var participant_id = 'node-participant-' + jarnxmpp.ce._idFromJID(user_jid);
    participant_id = jarnxmpp.ce._jqID(participant_id);
    $(participant_id).fadeTo('fast', 0.1);
    $(participant_id).fadeTo('fast', 1.0);
};

/* User joined/left event handlers */

jarnxmpp.ce.onUserJoined = function(event) {
    var jid = event.jid;
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
};

jarnxmpp.ce.onUserLeft = function(event) {
    var jid = event.jid;
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
};

/* Focus event & handler */

jarnxmpp.ce.ownNodeFocused = function (node) {
    jarnxmpp.ce.focused_node = node;
    jarnxmpp.ce.sendNodeFocus(node, jarnxmpp.connection.jid);
    event = $.Event('jarnxmpp.ce.nodeFocus');
    event.node = node;
    event.jid = jarnxmpp.connection.jid;
    $(document).trigger(event);
};

jarnxmpp.ce.onNodeFocus = function(event) {
    var node_id = jarnxmpp.ce.nodeToId[event.node];
    var participant_id = 'node-participant-' + jarnxmpp.ce._idFromJID(event.jid);
    $('#' + participant_id).remove();

    var user_id = Strophe.getNodeFromJid(event.jid);
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
};

/* Show error to user*/

jarnxmpp.ce.onErrorOccured = function (event) {
    $.gritter.add({
        title: 'Error',
        text: event.text,
        sticky: false,
        time: 3000,
    });
};

/* Setup functions */

jarnxmpp.ce._setup = function () {
    var context_url = $('base').attr('href');
    $.getJSON(context_url + '/@@collaborate', function(data) {
        if (data===null)
            // Not Ceditable.
            return;
        jarnxmpp.ce.component = data.component;
        jarnxmpp.ce.nodeToId = data.nodeToId;
        jarnxmpp.ce.idToNode = data.idToNode;
        // Setup up nodes.
        for (var key in jarnxmpp.ce.nodeToId)
            if (jarnxmpp.ce.nodeToId.hasOwnProperty(key))
                jarnxmpp.ce._setupNode(key);

        $(document).bind('jarnxmpp.ce.nodeChanged', jarnxmpp.ce.sendPatch);
        $(document).bind('jarnxmpp.ce.applyPatch', jarnxmpp.ce.onApplyPatch);
        $(document).bind('jarnxmpp.ce.nodeFocus', jarnxmpp.ce.onNodeFocus);
        $(document).bind('jarnxmpp.ce.userJoined', jarnxmpp.ce.onUserJoined);
        $(document).bind('jarnxmpp.ce.userLeft', jarnxmpp.ce.onUserLeft);
        $(document).bind('jarnxmpp.ce.error', jarnxmpp.ce.onErrorOccured);
    });
};

jarnxmpp.ce._setupNode = function (node) {
    var node_id = jarnxmpp.ce.nodeToId[node];
    var jqid = jarnxmpp.ce._jqID(node_id);
    var text = jarnxmpp.ce._getContent(node);
    jarnxmpp.ce.shadow_copies[node] = text;
    jarnxmpp.ce.last_update[node] = new Date().getTime();
    jarnxmpp.ce.sendPresence(node);
    var editor = window.tinyMCE.getInstanceById(node_id);

    if (editor!==undefined) {
        jarnxmpp.ce.tiny_ids[node_id] = '';
        editor.onKeyUp.add(function (ed, l) {
            jarnxmpp.ce.nodeBlur(editor.id);
        });
        editor.onChange.add(function (ed, l) {
            jarnxmpp.ce.nodeBlur(editor.id);
        });
        editor.onActivate.add(function (ed) {
            jarnxmpp.ce.ownNodeFocused(jarnxmpp.ce.idToNode[editor.id]);
        });
    }  else {
        $(jqid).bind('blur keyup paste', function () {
            jarnxmpp.ce.nodeBlur(this.id);
        });
        $(jqid).bind('focus', function() {
            jarnxmpp.ce.ownNodeFocused(jarnxmpp.ce.idToNode[this.id]);
        });
    }
    $(jqid).before($('<div>').attr('id', node_id + '-participants').addClass('node-participants'));
    jarnxmpp.ce.getShadowCopy(node);
};

$(document).bind('jarnxmpp.connected', function () {
    if (($('form[name="edit_form"]').length &&
        $('base').attr('href').indexOf('portal_factory')===-1) ||
        $('body').hasClass('template-edit')) {
        jarnxmpp.ce._setup();
    }
});

