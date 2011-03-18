import json
import logging

from plone.registry.interfaces import IRegistry
from zope.component import getUtility
from zope.component import queryUtility
from zope.publisher.browser import BrowserView

from jarn.xmpp.collaboration.interfaces import ICollaborativeEditingComponent
from jarn.xmpp.collaboration.interfaces import ICollaborativelyEditable

logger = logging.getLogger('jarn.xmpp.collaborate')


class CollaborateView(BrowserView):
    """
    """

    def __init__(self, context, request):
        super(CollaborateView, self).__init__(context, request)
        try:
            self.ceditable = ICollaborativelyEditable(self.context)
        except TypeError:
            self.ceditable = None

    @property
    def available(self):
        return self.ceditable is not None and \
            queryUtility(ICollaborativeEditingComponent)

    @property
    def nodeToId(self):
        return self.ceditable.nodeToId

    @property
    def idToNode(self):
        return self.ceditable.idToNode

    def __call__(self):
        if not self.available:
            return
        registry = getUtility(IRegistry)
        component_jid = registry.get('jarn.xmpp.collaborationJID')
        if component_jid is None:
            return
        return json.dumps({
            'component': component_jid,
            'nodeToId': self.nodeToId,
            'idToNode': self.idToNode})
