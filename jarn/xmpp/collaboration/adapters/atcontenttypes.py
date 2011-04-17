from Products.ATContentTypes.interfaces.document import IATDocument
from Products.ATContentTypes.interfaces.news import IATNewsItem

from zope.component import adapts
from zope.interface import implements

from jarn.xmpp.collaboration.interfaces import ICollaborativelyEditable


class ATContentTypeCEAdapterBase(object):

    def __init__(self, context):
        self.context = context

    @property
    def htmlIDs(self):
        return []

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

    def getNodeTextFromHtmlID(html_id):
        return ''

    def _htmlIDToNodeId(self, html_id):
        return self.contentUID + '#' + html_id

    def _UIDAndIDFromNodeID(self, nodeid):
        return tuple(nodeid.split('#'))


class ATDocumentCEAdapter(ATContentTypeCEAdapterBase):

    implements(ICollaborativelyEditable)
    adapts(IATDocument)

    @property
    def htmlIDs(self):
        return ['title', 'description', 'text']

    @property
    def tinyIDs(self):
        return ['text']

    def getNodeTextFromHtmlID(self, html_id):
        text = ''
        if html_id == 'title':
            text = self.context.Title()
        elif html_id == 'description':
            text = self.context.Description()
        elif html_id == 'text':
            text =self.context.getRawText()
        text = text.decode('utf-8')
        return text

    def setNodeTextFromHtmlID(self, html_id, text):
        if html_id == 'title':
            self.context.setTitle(text)
        elif html_id == 'description':
            self.context.setDescription(text)
        elif html_id == 'text':
            self.context.setText(text, mimetype='text/html')


class ATNewsItemCEAdapter(ATContentTypeCEAdapterBase):

    implements(ICollaborativelyEditable)
    adapts(IATNewsItem)

    @property
    def htmlIDs(self):
        return ['title', 'description', 'text', 'imageCaption']

    @property
    def tinyIDs(self):
        return ['text']

    def getNodeTextFromHtmlID(self, html_id):
        text = ''
        if html_id == 'title':
            text = self.context.Title()
        elif html_id == 'description':
            text = self.context.Description()
        elif html_id == 'text':
            text =self.context.getRawText()
        elif html_id == 'imageCaption':
            text =self.context.getImageCaption()
        text = text.decode('utf-8')
        return text

    def setNodeTextFromHtmlID(self, html_id, text):
        if html_id == 'title':
            self.context.setTitle(text)
        elif html_id == 'description':
            self.context.setDescription(text)
        elif html_id == 'text':
            self.context.setText(text, mimetype='text/html')
        elif html_id == 'imageCaption':
            text =self.context.setImageCaption(text)
