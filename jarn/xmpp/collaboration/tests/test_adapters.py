import unittest2 as unittest

from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID

from jarn.xmpp.collaboration.interfaces import ICollaborativelyEditable
from jarn.xmpp.collaboration.testing import COLLABORATION_INTEGRATION_TESTING


class DiffMatchPatchTest(unittest.TestCase):

    layer = COLLABORATION_INTEGRATION_TESTING

    def test_atcontenttypes(self):
        portal = self.layer['portal']
        setRoles(portal, TEST_USER_ID, ['Contributor'])
        portal.invokeFactory('Document', 'adoc',
            title='A title',
            description='Some description')
        doc = portal['adoc']
        uid = doc.UID()
        ce = ICollaborativelyEditable(doc)
        self.assertEqual(uid, ce.contentUID)
        self.assertEqual(['parent-fieldname-title',
                          'parent-fieldname-description'],
                         ce.htmlIDs)
        self.assertEqual([uid + '#' + 'parent-fieldname-title',
                          uid + '#' + 'parent-fieldname-description'],
                         ce.nodeIDs)
