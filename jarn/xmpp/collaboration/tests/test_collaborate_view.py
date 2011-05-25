import json
import unittest2 as unittest

from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from zope.component import getGlobalSiteManager

from jarn.xmpp.collaboration.interfaces import ICollaborativeEditingComponent
from jarn.xmpp.collaboration.testing import COLLABORATION_INTEGRATION_TESTING
from jarn.xmpp.collaboration.tests.mock import MockCollaborationComponent


class CollaborateViewTest(unittest.TestCase):

    layer = COLLABORATION_INTEGRATION_TESTING

    def setUp(self):
        ICollaborativeEditingComponent
        gsm = getGlobalSiteManager()
        component = MockCollaborationComponent()
        gsm.registerUtility(component, ICollaborativeEditingComponent)

    def test_collaborate_view(self):
        portal = self.layer['portal']
        setRoles(portal, TEST_USER_ID, ['Contributor'])
        portal.invokeFactory('Document', 'adoc',
            title='A title',
            description='Some description',
            text='Some text')
        doc = portal['adoc']
        view = doc.unrestrictedTraverse('@@collaborate')
        result = json.loads(view())

        self.assertTrue('nodeToId' in result)
        self.assertTrue('idToNode' in result)
        self.assertTrue('component' in result)
        self.assertEqual(result['component'], 'collaboration.localhost')
        uid = doc.UID()
        nodeToId = result['nodeToId']
        idToNode = result['idToNode']

        fields = ['title', 'description', 'text']
        for field in fields:
            self.assertEqual(nodeToId[uid + '#' + field], field)
            self.assertEqual(idToNode[field], uid + '#' + field)
