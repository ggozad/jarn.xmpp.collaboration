import json
import logging

from plone.app.layout.viewlets.common import ViewletBase
from zope.component import getUtility

from jarn.xmpp.core.interfaces import IXMPPSettings
from jarn.xmpp.collaboration.interfaces import ICollaborativelyEditable


logger = logging.getLogger('jarn.xmpp.collaborate')


class CollaborateViewlet(ViewletBase):
    """
    """

    def update(self):
        super(CollaborateViewlet, self).update()
        self.settings = getUtility(IXMPPSettings)

    @property
    def nodeToId(self):
        try:
            return json.dumps(ICollaborativelyEditable(self.context).nodeToId)
        except TypeError:
            return '{}'

    @property
    def idToNode(self):
        try:
            return json.dumps(ICollaborativelyEditable(self.context).idToNode)
        except TypeError:
            return '{}'

    @property
    def setup(self):
        return """
        jarnxmpp.ce.component = 'collaboration.localhost';
        jarnxmpp.ce.nodeToId = %s;
        jarnxmpp.ce.idToNode = %s;
        """ % (self.nodeToId, self.idToNode)
