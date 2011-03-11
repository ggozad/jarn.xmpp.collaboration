import json
import logging

from plone.app.layout.viewlets.common import ViewletBase
from plone.registry.interfaces import IRegistry
from zope.component import getUtility
from zope.component import queryUtility

from jarn.xmpp.collaboration.interfaces import ICollaborativeEditingComponent
from jarn.xmpp.collaboration.interfaces import ICollaborativelyEditable

logger = logging.getLogger('jarn.xmpp.collaborate')


class CollaborateViewlet(ViewletBase):
    """
    """

    @property
    def available(self):
        return queryUtility(ICollaborativeEditingComponent) is not None

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
        registry = getUtility(IRegistry)
        component_jid = registry.get('jarn.xmpp.collaborationJID')
        if component_jid is None:
            return ""
        return """
        jarnxmpp.ce.component = '%s';
        jarnxmpp.ce.nodeToId = %s;
        jarnxmpp.ce.idToNode = %s;
        """ % (component_jid, self.nodeToId, self.idToNode)
