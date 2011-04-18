import logging
import transaction
import Zope2

from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import noSecurityManager
from Products.CMFCore.utils import getToolByName
from plone.registry.interfaces import IRegistry
from twisted.words.protocols.jabber.jid import JID
from zExceptions import BadRequest
from zope.app.component.hooks import setSite
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
        super(CollaborationHandler, self).__init__()
        self.portal_id = portal.id

    def userJoined(self, user, node):
        logger.info('User %s joined node %s.' % (user, node))

    def userLeft(self, user, node):
        logger.info('User %s left node %s.' % (user, node))

    def getNodeText(self, jid, node):
        transaction.begin()
        app = Zope2.app()
        text = ''
        try:
            try:
                portal = app.unrestrictedTraverse(self.portal_id, None)
                if portal is None:
                    raise BadRequest(
                        'Portal with id %s not found' % self.portal_id)
                setSite(portal)
                acl_users = getToolByName(portal, 'acl_users')
                user_id = JID(jid).user
                user = acl_users.getUserById(user_id)
                if user is None:
                    raise BadRequest(
                        'Invalid user %s' % user_id)
                newSecurityManager(None, user)
                ct = getToolByName(portal, 'portal_catalog')
                uid, html_id = node.split('#')
                item = ct.unrestrictedSearchResults(UID=uid)
                if not item:
                    raise BadRequest(
                        'Content with UID %s not found' % uid)
                item = ICollaborativelyEditable(item[0].getObject())
                text = item.getNodeTextFromHtmlID(html_id)
                transaction.commit()
            except:
                transaction.abort()
                raise
        finally:
            noSecurityManager()
            setSite(None)
            app._p_jar.close()
        return text

    def setNodeText(self, jid, node, text):
        transaction.begin()
        app = Zope2.app()
        try:
            try:
                portal = app.unrestrictedTraverse(self.portal_id, None)
                if portal is None:
                    raise BadRequest(
                        'Portal with id %s not found' % self.portal_id)
                setSite(portal)
                acl_users = getToolByName(portal, 'acl_users')
                user_id = JID(jid).user
                user = acl_users.getUserById(user_id)
                if user is None:
                    raise BadRequest(
                        'Invalid user %s' % user_id)
                newSecurityManager(None, user)
                ct = getToolByName(portal, 'portal_catalog')
                uid, html_id = node.split('#')
                item = ct.unrestrictedSearchResults(UID=uid)
                if not item:
                    raise BadRequest(
                        'Content with UID %s not found' % uid)
                item = ICollaborativelyEditable(item[0].getObject())
                item.setNodeTextFromHtmlID(html_id, text)
                transaction.commit()
            except:
                transaction.abort()
                raise
        finally:
            noSecurityManager()
            setSite(None)
            app._p_jar.close()
        return text


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
