from Products.ATContentTypes.interfaces.document import IATDocument
from zope.component import adapts
from zope.interface import implements

from jarn.xmpp.collaboration.interfaces import ICollaborativelyEditable


class ATContentTypeCEAdapterBase(object):

    def __init__(self, context):
        self.context = context

    @property
    def htmlIDs(self):
        return ['parent-fieldname-title', 'parent-fieldname-description']

    @property
    def contentUID(self):
        return self.context.UID()

    @property
    def nodeIDs(self):
        return [self._htmlIDToNodeId(html_id) for html_id in self.htmlIDs]

    @property
    def nodeToId(self):
        r = dict()
        for html_id in self.htmlIDs:
            r[self._htmlIDToNodeId(html_id)] = html_id
        return r

    @property
    def idToNode(self):
        r = dict()
        for html_id in self.htmlIDs:
            r[html_id] = self._htmlIDToNodeId(html_id)
        return r

    def _htmlIDToNodeId(self, html_id):
        return self.contentUID + '#' + html_id

    def _UIDAndIDFromNodeID(self, nodeid):
        return tuple(nodeid.split('#'))


class ATDocumentCEAdapter(ATContentTypeCEAdapterBase):

    implements(ICollaborativelyEditable)
    adapts(IATDocument)
