import logging
import transaction
import ZODB.interfaces

from Products.CMFCore.utils import getToolByName
from plone.registry.interfaces import IRegistry
from zope.component import getGlobalSiteManager
from zope.component import getUtility
from zope.component import queryUtility

from jarn.xmpp.twisted.component import XMPPComponent

from jarn.xmpp.collaboration.interfaces import ICollaborativeEditingComponent
from jarn.xmpp.collaboration.interfaces import ICollaborativelyEditable
from jarn.xmpp.collaboration.protocol import DifferentialSyncronisationHandler

logger= logging.getLogger('jarn.xmpp.collaboration')


class CollaborationHandler(DifferentialSyncronisationHandler):
    """ Plone specific component that implements IDifferentialSyncronisation
    """

    def __init__(self, portal):
        connection = ZODB.interfaces.IConnection(portal._p_jar)
        self.db = connection.db()
        self.portal = portal
        self.portal_id = portal.id

    def userJoined(self, node, user):
        logger.info('User %s joined node %s.' % (user, node))

    def userLeft(self, node, user):
        logger.info('User %s left node %s.' % (user, node))

    def getNodeText(self, node):
        transaction.begin()
        ct = getToolByName(self.portal, 'portal_catalog')
        uid, html_id = node.split('#')
        item = ct.unrestrictedSearchResults(UID=uid)
        if not item:
            return ''
        item = ICollaborativelyEditable(item[0].getObject())
        text = item.getNodeTextFromHtmlID(html_id)
        transaction.abort()
        return text

    def setNodeText(self, node, text):
        conn = self.db.open()
        portal = conn.root().data['Application'][self.portal_id]
        transaction.begin()
        ct = getToolByName(portal, 'portal_catalog')
        uid, html_id = node.split('#')
        item = ct.unrestrictedSearchResults(UID=uid)
        if not item:
            return
        item = ICollaborativelyEditable(item[0].getObject())
        item.setNodeTextFromHtmlID(html_id, text)
        transaction.commit()
        conn.close()


def setupCollaborationComponent(portal, event):
    if queryUtility(ICollaborativeEditingComponent) is None:
        gsm = getGlobalSiteManager()
        registry = getUtility(IRegistry)
        component_jid = registry.get('jarn.xmpp.collaborationJID')
        xmpp_domain = registry.get('jarn.xmpp.xmppDomain')
        if component_jid is None or xmpp_domain is None:
            return

        component = XMPPComponent(xmpp_domain, 5347,
            component_jid, 'secret', [CollaborationHandler(portal)])
        gsm.registerUtility(component, ICollaborativeEditingComponent)
