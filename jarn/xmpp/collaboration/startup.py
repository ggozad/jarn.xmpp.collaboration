from zope.component import getGlobalSiteManager
from zope.component import getUtility

from jarn.xmpp.core.interfaces import IXMPPSettings
from jarn.xmpp.twisted.component import XMPPComponent

from jarn.xmpp.collaboration.interfaces import ICollaborativeEditingComponent
from jarn.xmpp.collaboration.protocol import CollaborativeEditingHandler

def setupCollaborationComponent(event):
    gsm = getGlobalSiteManager()
    settings = getUtility(IXMPPSettings)
    component = XMPPComponent(settings.XMPPDomain,
                              5347,
                              'collaboration.localhost',
                              'secret',
                              [CollaborativeEditingHandler()])
    gsm.registerUtility(component, ICollaborativeEditingComponent)
