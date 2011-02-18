import logging

from plone.app.layout.viewlets.common import ViewletBase
from zope.component import getUtility

from jarn.xmpp.core.interfaces import IXMPPSettings

logger = logging.getLogger('jarn.xmpp.collaborate')


class CollaborateViewlet(ViewletBase):
    """
    """

    def update(self):
        super(CollaborateViewlet, self).update()
        self.settings = getUtility(IXMPPSettings)

    @property
    def html_ids(self):
        return ['parent-fieldname-title']

    @property
    def setup(self):
        return """
        jarnxmpp.ce.component = 'collaboration.localhost';
        jarnxmpp.ce.html_ids =  %s;
        """ % (str(self.html_ids))
