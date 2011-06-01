import unittest2 as unittest

from plone.uuid.interfaces import IUUID
from zope.component import queryAdapter

from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID

from jarn.xmpp.collaboration.interfaces import ICollaborativelyEditable
from jarn.xmpp.collaboration.testing import COLLABORATION_INTEGRATION_TESTING
from jarn.xmpp.collaboration.testing import HAS_DEXTERITY


class DexterityCEAdapterTest(unittest.TestCase):

    layer = COLLABORATION_INTEGRATION_TESTING

    def setUp(self):
        portal = self.layer['portal']
        setRoles(portal, TEST_USER_ID, ['Contributor'])
        portal.invokeFactory('mytype', 'adoc',
            title='A title',
            description='A description',
            textline='A textline',
            text='Some text',
            richtext='Some richtext')
        self.doc = portal['adoc']

    def test_can_adapt(self):
        self.assertTrue(
            queryAdapter(self.doc, ICollaborativelyEditable) is not None)

    def test_contentUID(self):
        uid = IUUID(self.doc)
        ce = ICollaborativelyEditable(self.doc)
        self.assertEqual(uid, ce.contentUID)

    def test_htmlIds(self):
        ce = ICollaborativelyEditable(self.doc)
        self.assertEqual(set(['form-widgets-title',
                              'form-widgets-description',
                              'form-widgets-rights',
                              'form-widgets-textline',
                              'form-widgets-text',
                              'form.widgets.richtext']),
                         set(ce.htmlIDs))

    def test_nodeIds(self):
        uid = IUUID(self.doc)
        ce = ICollaborativelyEditable(self.doc)
        self.assertEqual(set([uid + '#' + 'form-widgets-title',
                              uid + '#' + 'form-widgets-description',
                              uid + '#' + 'form-widgets-rights',
                              uid + '#' + 'form-widgets-textline',
                              uid + '#' + 'form-widgets-text',
                              uid + '#' + 'form.widgets.richtext']),
                          set(ce.nodeIDs))

    def test_getNodeTextFromHtmlID(self):
        ce = ICollaborativelyEditable(self.doc)
        self.assertEqual(ce.getNodeTextFromHtmlID('form-widgets-text'),
                         'Some text')

    def test_setNodeTextFromHtmlID(self):
        ce = ICollaborativelyEditable(self.doc)
        ce.setNodeTextFromHtmlID('form-widgets-text',
                                 'New text'.decode('utf-8'))
        self.assertEqual('New text', self.doc.text)

    def test_nodeToId(self):
        uid = IUUID(self.doc)
        ce = ICollaborativelyEditable(self.doc)
        self.assertEqual('form-widgets-text',
                         ce.nodeToId[uid + '#' + 'form-widgets-text'])

    def test_idToNode(self):
        uid = IUUID(self.doc)
        ce = ICollaborativelyEditable(self.doc)
        self.assertEqual(uid + '#' + 'form-widgets-text',
                         ce.idToNode['form-widgets-text'])


def test_suite():
    suite = unittest.TestSuite()
    if HAS_DEXTERITY:
        suite.addTest(unittest.makeSuite(DexterityCEAdapterTest))
    return suite
