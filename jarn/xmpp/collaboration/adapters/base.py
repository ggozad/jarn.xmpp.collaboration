class CEAdapterBase(object):

    def __init__(self, context):
        self.context = context

    @property
    def htmlIDs(self): #pragma: no cover
        return []

    @property
    def contentUID(self): #pragma: no cover
        return ''

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

    def getNodeTextFromHtmlID(html_id): #pragma: no cover
        return ''

    def _htmlIDToNodeId(self, html_id):
        return self.contentUID + '#' + html_id
