from plone.locking.interfaces import ILockSettings
from zope.component import adapts
from zope.component import queryAdapter
from zope.interface import implements

from Products.ATContentTypes.interfaces import IATContentType

from jarn.xmpp.collaboration.interfaces import ICollaborativelyEditable


class CollaborativelyEditableLocking(object):
    """ Adapter to disable locking for ICollaborativelyEditable objects.
    """

    implements(ILockSettings)
    adapts(IATContentType)

    def __init__(self, context):
        self.context = context

    @property
    def lock_on_ttw_edit(self):
        if queryAdapter(self.context, ICollaborativelyEditable) is not None:
            return False
        return True
