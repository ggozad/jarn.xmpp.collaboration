import logging

from plone.registry.interfaces import IRegistry
from zope.component import getGlobalSiteManager
from zope.component import getUtility
from zope.component import queryUtility

from jarn.xmpp.twisted.component import XMPPComponent

from jarn.xmpp.collaboration.interfaces import ICollaborativeEditingComponent
from jarn.xmpp.collaboration.protocol import DifferentialSyncronisationHandler

logger= logging.getLogger('jarn.xmpp.collaboration')


class CollaborationHandler(DifferentialSyncronisationHandler):
    """ Plone specific component that implements IDifferentialSyncronisation
    """

    def userJoined(self, node, user):
        """
        Called when a user has joined a CE session.

        This method is to meant to be overriden by components.
        """
        logger.info('User %s joined node %s.' % (user, node))

    def userLeft(self, node, user):
        """
        Called when a user has left a CE session.

        This method is to meant to be overriden by components.
        """
        logger.info('User %s left node %s.' % (user, node))

    def getNodeText(self, node):
        """
        Returns the text of the node before a CE session is started.

        This method is to meant to be overriden by components.
        """
        if node.endswith('title'):
            return 'Welcome to Plone'
        return 'Congratulations! You have successfully installed Plone.'

    def setNodeText(self, node):
        """
        Saves the text of the node during/after a CE session.

        This method is to meant to be overriden by components.
        """
        pass


def setupCollaborationComponent(portal, event):
    if queryUtility(ICollaborativeEditingComponent) is None:
        gsm = getGlobalSiteManager()
        registry = getUtility(IRegistry)
        component_jid = registry.get('jarn.xmpp.collaborationJID')
        xmpp_domain = registry.get('jarn.xmpp.xmppDomain')
        if component_jid is None or xmpp_domain is None:
            return

        component = XMPPComponent(xmpp_domain, 5347,
            component_jid, 'secret', [CollaborationHandler()])
        gsm.registerUtility(component, ICollaborativeEditingComponent)
