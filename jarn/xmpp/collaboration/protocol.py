from zope.interface import implements
from wokkel import disco, iwokkel
from wokkel.subprotocols import XMPPHandler

from jarn.xmpp.collaboration.interfaces import ICollaborativeEditing

NS_CE= 'http://jarn.com/ns/collaborative-editing'
PRESENCE = "/presence/collaborate[@xmlns='%s']" % NS_CE
CE_REQUEST = "/iq[@type='get']/collaborate[@xmlns='%s']" % NS_CE


class CollaborativeEditingClientProtocol(XMPPHandler):
    pass


class CollaborativeEditingHandler(XMPPHandler):
    """
    """

    implements(ICollaborativeEditing, iwokkel.IDisco)

    def connectionInitialized(self):
        self.xmlstream.addObserver(CE_REQUEST, self.onRequest)

    def onRequest(self, iq):
        pass

    def getDiscoInfo(self, requestor, target, nodeIdentifier=''):
        """
        Get identity and features from this entity, node.

        This handler supports XMPP Ping, but only without a nodeIdentifier
        specified.
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
