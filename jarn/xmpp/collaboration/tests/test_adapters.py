import unittest2 as unittest

from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID

from jarn.xmpp.collaboration.interfaces import ICollaborativelyEditable
from jarn.xmpp.collaboration.testing import COLLABORATION_INTEGRATION_TESTING


class CEAdapterTest(unittest.TestCase):

    layer = COLLABORATION_INTEGRATION_TESTING

    def test_atdocument(self):
        portal = self.layer['portal']
        setRoles(portal, TEST_USER_ID, ['Contributor'])
        portal.invokeFactory('Document', 'adoc',
            title='A title',
            description='Some description')
        doc = portal['adoc']
        uid = doc.UID()
        ce = ICollaborativelyEditable(doc)
        self.assertEqual(uid, ce.contentUID)
        self.assertEqual(['title',
                          'description',
                          'text'],
                         ce.htmlIDs)
        self.assertEqual([uid + '#' + 'title',
                          uid + '#' + 'description',
                          uid + '#' + 'text'],
                         ce.nodeIDs)
        self.assertEqual(['text'], ce.tinyIDs)

    def test_atnewsitem(self):
        portal = self.layer['portal']
        setRoles(portal, TEST_USER_ID, ['Contributor'])
        portal.invokeFactory('News Item', 'news',
            title='A title',
            description='Some description')
        doc = portal['news']
        uid = doc.UID()
        ce = ICollaborativelyEditable(doc)
        self.assertEqual(uid, ce.contentUID)
        self.assertEqual(['title',
                          'description',
                          'text',
                          'imageCaption'],
                         ce.htmlIDs)
        self.assertEqual([uid + '#' + 'title',
                          uid + '#' + 'description',
                          uid + '#' + 'text',
                          uid + '#' + 'imageCaption'],
                         ce.nodeIDs)
        self.assertEqual(['text'], ce.tinyIDs)
