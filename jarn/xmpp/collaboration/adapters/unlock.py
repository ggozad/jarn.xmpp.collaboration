from plone.locking.interfaces import ILockSettings
from zope.component import adapts
from zope.interface import implements

from jarn.xmpp.collaboration.interfaces import INonLockable


class CollaborativelyEditableLocking(object):
    """ Adapter to disable locking for ICollaborativelyEditable objects.
    """

    implements(ILockSettings)
    adapts(INonLockable)

    def __init__(self, context):
        self.context = context

    @property
    def lock_on_ttw_edit(self):
        return False
