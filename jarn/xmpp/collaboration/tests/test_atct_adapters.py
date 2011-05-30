import unittest2 as unittest

from zope.component import queryAdapter

from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID

from jarn.xmpp.collaboration.interfaces import ICollaborativelyEditable
from jarn.xmpp.collaboration.testing import COLLABORATION_INTEGRATION_TESTING


class ATCTCEAdapterTest(unittest.TestCase):

    layer = COLLABORATION_INTEGRATION_TESTING

    def setUp(self):
        portal = self.layer['portal']
        setRoles(portal, TEST_USER_ID, ['Contributor'])
        portal.invokeFactory('Document', 'adoc',
            title='A title',
            description='Some description',
            text='Some text')
        self.doc = portal['adoc']

    def test_can_adapt(self):
        self.assertTrue(queryAdapter(self.doc, ICollaborativelyEditable) is not None)

    def test_contentUID(self):
        uid = self.doc.UID()
        ce = ICollaborativelyEditable(self.doc)
        self.assertEqual(uid, ce.contentUID)

    def test_htmlIds(self):
        ce = ICollaborativelyEditable(self.doc)
        self.assertEqual(['title',
                          'description',
                          'text'],
                         ce.htmlIDs)

    def test_nodeIds(self):
        uid = self.doc.UID()
        ce = ICollaborativelyEditable(self.doc)
        self.assertEqual([uid + '#' + 'title',
                          uid + '#' + 'description',
                          uid + '#' + 'text'],
                          ce.nodeIDs)

    def test_getNodeTextFromHtmlID(self):
        ce = ICollaborativelyEditable(self.doc)
        self.assertEqual(ce.getNodeTextFromHtmlID('text'),
                         'Some text')

    def test_setNodeTextFromHtmlID(self):
        ce = ICollaborativelyEditable(self.doc)
        ce.setNodeTextFromHtmlID('text', 'New text')
        self.assertEqual('New text', self.doc.getRawText())

    def test_nodeToId(self):
        ce = ICollaborativelyEditable(self.doc)
        uid = self.doc.UID()
        self.assertEqual('text', ce.nodeToId[uid + '#' + 'text'])

    def test_idToNode(self):
        ce = ICollaborativelyEditable(self.doc)
        uid = self.doc.UID()
        self.assertEqual(uid + '#' + 'text', ce.idToNode['text'])
