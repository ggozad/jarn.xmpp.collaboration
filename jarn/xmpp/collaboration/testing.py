from plone.app.testing import PloneSandboxLayer
from plone.app.testing import applyProfile
from plone.app.testing import IntegrationTesting, FunctionalTesting
from zope.configuration import xmlconfig

from jarn.xmpp.core.testing import XMPPCORE_FIXTURE


class CollaborationFixture(PloneSandboxLayer):

    defaultBases = (XMPPCORE_FIXTURE, )

    def setUpZope(self, app, configurationContext):
        # Load ZCML
        import jarn.xmpp.collaboration
        xmlconfig.file('configure.zcml', jarn.xmpp.collaboration,
                       context=configurationContext)

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'jarn.xmpp.collaboration:default')

COLLABORATION_FIXTURE = CollaborationFixture()

COLLABORATION_INTEGRATION_TESTING = IntegrationTesting(
    bases=(COLLABORATION_FIXTURE, ),
    name="CollaborationFixture:Integration")

COLLABORATION_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(COLLABORATION_FIXTURE, ),
    name="CollaborationFixture:Functional")
