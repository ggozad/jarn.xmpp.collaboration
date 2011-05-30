from plone.registry.interfaces import IRegistry

from plone.app.testing import PloneSandboxLayer
from plone.app.testing import applyProfile
from plone.app.testing import IntegrationTesting, FunctionalTesting
from zope.configuration import xmlconfig
from zope.component import getUtility


from jarn.xmpp.core.testing import XMPPCORE_NO_REACTOR_FIXTURE

try:
    import plone.app.dexterity
    HAS_DEXTERITY = True
except ImportError:
    HAS_DEXTERITY = False


class CollaborationFixture(PloneSandboxLayer):

    defaultBases = (XMPPCORE_NO_REACTOR_FIXTURE, )

    def setUpZope(self, app, configurationContext):
        # Load ZCML
        if HAS_DEXTERITY:
            self.loadZCML(name='meta.zcml', package=plone.app.dexterity)
            self.loadZCML(package=plone.app.dexterity)

        import jarn.xmpp.collaboration
        xmlconfig.file('configure.zcml', jarn.xmpp.collaboration,
                       context=configurationContext)

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'jarn.xmpp.collaboration:default')
        registry = getUtility(IRegistry)
        registry['jarn.xmpp.collaborationJID'] = 'collaboration.localhost'

        if HAS_DEXTERITY:
            self.applyProfile(portal, 'plone.app.dexterity:default')

            # Surely there are better ways of doing this than TTW, feel free to
            # replace.
            import transaction
            from plone.testing.z2 import Browser
            from plone.app.testing import TEST_USER_ID, TEST_USER_PASSWORD
            from plone.app.testing import setRoles
            from plone.testing import z2

            setRoles(portal, TEST_USER_ID, ['Manager'])
            transaction.commit()

            with z2.zopeApp() as app:
                browser = Browser(app)
                browser.handleErrors = False
                browser.addHeader('Authorization', 'Basic %s:%s' %
                    (TEST_USER_ID, TEST_USER_PASSWORD, ))
                # Create a type
                browser.open('http://nohost/plone/@@dexterity-types')
                browser.getControl('Add New Content Type').click()
                browser.getControl('Type Name').value = 'MyType'
                browser.getControl('Short Name').value = 'mytype'
                browser.getControl('Add').click()

                #Add fields
                browser.getLink('MyType').click()
                fields = [('textline', 'Text line (String)'),
                          ('text', 'Text'),
                          ('richtext', 'Rich Text')]

                for field_id, field_type in fields:
                    browser.getControl('Add new field').click()
                    browser.getControl('Title').value = field_id
                    browser.getControl('Short Name').value = field_id
                    browser.getControl('Field type').getControl(
                        value=field_type).selected = True
                    browser.getControl('Add').click()

            # Setup behaviors
            portal.portal_types.mytype.behaviors = (
                'plone.app.dexterity.behaviors.metadata.IDublinCore',
                'plone.app.content.interfaces.INameFromTitle',
                'jarn.xmpp.collaboration.interfaces.ICollaborativelyEditable')
            setRoles(portal, TEST_USER_ID, ['Member'])


COLLABORATION_FIXTURE = CollaborationFixture()

COLLABORATION_INTEGRATION_TESTING = IntegrationTesting(
    bases=(COLLABORATION_FIXTURE, ),
    name="CollaborationFixture:Integration")

COLLABORATION_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(COLLABORATION_FIXTURE, ),
    name="CollaborationFixture:Functional")
