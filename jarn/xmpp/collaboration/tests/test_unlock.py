import unittest2 as unittest

from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.locking.interfaces import ILockable

from jarn.xmpp.collaboration.testing import COLLABORATION_INTEGRATION_TESTING


class UnlockAdapterTest(unittest.TestCase):

    layer = COLLABORATION_INTEGRATION_TESTING

    def test_atct_not_lockable(self):
        portal = self.layer['portal']
        setRoles(portal, TEST_USER_ID, ['Contributor'])
        portal.invokeFactory('Document', 'adoc',
            title='A title',
            description='Some description',
            text='Some text')
        doc = portal['adoc']

        lockable = ILockable(doc)
        self.assertEqual(False, lockable.locked())
        lockable.lock()
        self.assertEqual(False, lockable.locked())
