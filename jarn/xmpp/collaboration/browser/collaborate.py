import logging

from plone.app.layout.viewlets.common import ViewletBase
from plone.registry.interfaces import IRegistry
from zope.component import getUtility
from zope.component import queryUtility

from jarn.xmpp.collaboration.interfaces import ICollaborativeEditingComponent

logger = logging.getLogger('jarn.xmpp.collaborate')


class CollaborateViewlet(ViewletBase):
    """
    """

    @property
    def available(self):
        return queryUtility(ICollaborativeEditingComponent) is not None

    @property
    def html_ids(self):
        return ['parent-fieldname-title']

    @property
    def setup(self):
        registry = getUtility(IRegistry)
        component_jid = registry.get('jarn.xmpp.collaborationJID')
        if component_jid is None:
            return ""
        return """
        jarnxmpp.ce.component = '%s';
        jarnxmpp.ce.html_ids =  %s;
        """ % (component_jid, str(self.html_ids))
