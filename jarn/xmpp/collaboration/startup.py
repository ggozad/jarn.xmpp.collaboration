from zope.component import getGlobalSiteManager
from zope.component import getUtility

from jarn.xmpp.core.interfaces import IXMPPSettings
from jarn.xmpp.twisted.component import XMPPComponent

from jarn.xmpp.collaboration.interfaces import ICollaborativeEditingComponent
from jarn.xmpp.collaboration.protocol import DifferentialSyncronisationHandler


def setupCollaborationComponent(event):
    gsm = getGlobalSiteManager()
    settings = getUtility(IXMPPSettings)
    component = XMPPComponent(settings.XMPPDomain,
                              5347,
                              'collaboration.localhost',
                              'secret',
                              [DifferentialSyncronisationHandler()])
    gsm.registerUtility(component, ICollaborativeEditingComponent)
