from plone.registry.interfaces import IRegistry
from zope.component import getGlobalSiteManager
from zope.component import getUtility
from zope.component import queryUtility

from jarn.xmpp.twisted.component import XMPPComponent

from jarn.xmpp.collaboration.interfaces import ICollaborativeEditingComponent
from jarn.xmpp.collaboration.protocol import DifferentialSyncronisationHandler


def setupCollaborationComponent(portal, event):
    if queryUtility(ICollaborativeEditingComponent) is None:
        gsm = getGlobalSiteManager()
        registry = getUtility(IRegistry)
        component_jid = registry.get('jarn.xmpp.collaborationJID')
        xmpp_domain = registry.get('jarn.xmpp.xmppDomain')
        if component_jid is None or xmpp_domain is None:
            return

        component = XMPPComponent(xmpp_domain, 5347,
            component_jid, 'secret', [DifferentialSyncronisationHandler()])
        gsm.registerUtility(component, ICollaborativeEditingComponent)
