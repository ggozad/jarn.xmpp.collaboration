import json
import logging

from plone.registry.interfaces import IRegistry
from zope.component import getUtility
from zope.component import queryUtility
from zope.component import queryAdapter
from zope.publisher.browser import BrowserView

from jarn.xmpp.collaboration.interfaces import ICollaborativeEditingComponent
from jarn.xmpp.collaboration.interfaces import ICollaborativelyEditable

logger = logging.getLogger('jarn.xmpp.collaborate')


class CollaborateView(BrowserView):
    """
    """

    def __init__(self, context, request):
        super(CollaborateView, self).__init__(context, request)
        self.ceditable = queryAdapter(self.context, ICollaborativelyEditable)

    def __call__(self):
        registry = getUtility(IRegistry)
        component_jid = registry.get('jarn.xmpp.collaborationJID')
        component = queryUtility(ICollaborativeEditingComponent)

        if self.ceditable is None or component is None or component_jid is None:
            return #pragma no cover

        return json.dumps({
            'component': component_jid,
            'nodeToId': self.ceditable.nodeToId,
            'idToNode': self.ceditable.idToNode})
