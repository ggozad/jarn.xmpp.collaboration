import logging

from twisted.words.xish.domish import Element
from zope.interface import implements
from wokkel import disco, iwokkel
from wokkel.subprotocols import XMPPHandler

from jarn.xmpp.collaboration.interfaces import IDifferentialSyncronisation
from jarn.xmpp.collaboration.dmp import diff_match_patch

NS_CE= 'http://jarn.com/ns/collaborative-editing'
CE_PRESENCE = "/presence"
CE_MESSAGE = "/message/x[@xmlns='%s']" % NS_CE

logger= logging.getLogger('jarn.xmpp.collaboration')


class DifferentialSyncronisationClientProtocol(XMPPHandler):
    """
    Client protocol for Collaborative Editing.
    """
    pass


class DifferentialSyncronisationHandler(XMPPHandler):
    """
    Server protocol for Collaborative Editing.
    """

    implements(IDifferentialSyncronisation, iwokkel.IDisco)

    def __init__(self):
        self.node_participants = {}
        self.participant_nodes = {}
        self.participant_focus = {}
        self.shadow_copies = {}
        self.dmp = diff_match_patch()
        super(DifferentialSyncronisationHandler, self).__init__()

    def connectionInitialized(self):
        self.xmlstream.addObserver(CE_PRESENCE, self._onPresence)
        self.xmlstream.addObserver(CE_MESSAGE, self._onMessage)
        logger.info('Collaboration component connected.')

    def _onIQRequest(self, iq):
        pass

    def _onPresence(self, presence):
        sender = presence['from']
        type = presence.getAttribute('type')
        if type=='unavailable':
            if sender in self.participant_nodes:
                for node in self.participant_nodes[sender]:
                    self.node_participants[node].remove(sender)
                    self.userLeft(sender, node)
                    if not self.node_participants[node]:
                        del self.node_participants[node]
                        del self.shadow_copies[node]
                del self.participant_nodes[sender]
            if sender in self.participant_focus:
                # Notify those that participate in the focused node that
                # the user left. In principle, it is possible that there are
                # other common nodes whose participants should also be
                # informed but hey!
                focus_node = self.participant_focus[sender]
                if focus_node in self.node_participants:
                    participants = self.node_participants[focus_node]
                    self._sendFocus('', sender, participants)
                del self.participant_focus[sender]

            return

        query = presence.query
        node = ''
        if query:
            node = presence.query.getAttribute('node')
        if not node:
            # Ignore, malformed initial presence
            return

        if node in self.node_participants:
            self.node_participants[node].add(sender)
        else:
            self.node_participants[node] = set([sender])

        if sender in self.participant_nodes:
            self.participant_nodes[sender].add(node)
        else:
            self.participant_nodes[sender] = set([node])

        # Send shadow copy text.
        if node not in self.shadow_copies:
            self.shadow_copies[node] = self.getNodeText(sender, node)
        self._sendShadowCopy(sender, node)

        # Send participants focus
        for participant in (self.node_participants[node] - set([sender])):
            if participant in self.participant_focus and self.participant_focus[participant] == node:
                self._sendFocus(node, participant, [sender])
        self.userJoined(sender, node)

    def _onMessage(self, message):
        sender = message['from']
        x = message.x
        if x is None:
            return
        for elem in x.elements():
            node = elem['node']
            action = elem['action']
            if action=='patch' and node in self.shadow_copies:
                diff = elem.children[0]
                self._handlePatch(node, sender, diff)
            elif action=='focus' and node in self.shadow_copies:
                self.participant_focus[sender] = node
                recipients = [jid for jid in (self.node_participants[node] - set([sender]))]
                self._sendFocus(node, sender, recipients)
            elif action=='save' and node in self.shadow_copies:
                self.setNodeText(sender, node, self.shadow_copies[node])

    def _handlePatch(self, node, sender, diff):
        patches = self.dmp.patch_fromText(diff)
        shadow = self.shadow_copies[node]

        (new_text, res) = self.dmp.patch_apply(patches, shadow)
        if False in res:
            # Do I need to do something or not?
            # Maybe revert the patch?
            logger.error('Patch %s could not be applied on node %s' % \
                         (diff, node))
        else:
            logger.info('Patch from %s applied on %s'%(sender, node))
        self.shadow_copies[node] = new_text

        message = Element((None, "message", ))
        x = message.addElement((NS_CE, 'x'))
        item = x.addElement('item', content=diff)
        item['action'] = 'patch'
        item['node'] = node
        item['user'] = sender

        for jid in (self.node_participants[node] - set([sender])):
            message['to'] = jid
            self.xmlstream.send(message)

    def _sendShadowCopy(self, jid, node):
        text = self.shadow_copies[node]
        message = Element((None, "message", ))
        message['to'] = jid
        x = message.addElement((NS_CE, 'x'))
        item = x.addElement('item', content=text)
        item['action'] = 'set'
        item['node'] = node
        self.xmlstream.send(message)

    def _sendFocus(self, node, sender, recipients):
        message = Element((None, "message", ))
        x = message.addElement((NS_CE, 'x'))
        item = x.addElement('item')
        item['action'] = 'focus'
        item['node'] = node
        item['user'] = sender


        for jid in recipients:
            message['to'] = jid
            self.xmlstream.send(message)

    # Disco
    def getDiscoInfo(self, requestor, target, nodeIdentifier=''):
        """
        Get identity and features from this entity, node.

        This handler supports Collaborative Editing, but only without a
        nodeIdentifier specified.
        """
        if not nodeIdentifier:
            return [disco.DiscoFeature(NS_CE)]
        else:
            return []

    def getDiscoItems(self, requestor, target, nodeIdentifier=''):
        """
        Get contained items for this entity, node.

        This handler does not support items.
        """
        return []

    # Implemented by sub-classing.
    def userJoined(self, user, node):
        """
        Called when a user has joined a CE session.

        This method is to meant to be overriden by components.
        """
        pass

    def userLeft(self, user, node):
        """
        Called when a user has left a CE session.

        This method is to meant to be overriden by components.
        """
        pass

    def getNodeText(self, user, node):
        """
        Returns the text of the node before a CE session is started.

        This method is to meant to be overriden by components.
        """
        pass

    def setNodeText(self, user, node, text):
        """
        Saves the text of the node during/after a CE session.

        This method is to meant to be overriden by components.
        """
        pass
