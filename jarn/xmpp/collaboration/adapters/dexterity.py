from zope.cachedescriptors.property import Lazy as lazy_property
from zope.component import adapts, getUtility
from zope.interface import implements
from zope.schema.interfaces import ITextLine

from plone.uuid.interfaces import IUUID
from plone.dexterity.interfaces import IDexterityFTI, IDexterityContent
from plone.app.textfield.interfaces import IRichText, IRichTextValue

from jarn.xmpp.collaboration.adapters.atcontenttypes import ATContentTypeCEAdapterBase
from jarn.xmpp.collaboration.interfaces import ICollaborativelyEditable


class DexterityCEAdapter(ATContentTypeCEAdapterBase):
    implements(ICollaborativelyEditable)
    adapts(IDexterityContent)

    def __init__(self, context):
        self.context = context

    @lazy_property
    def _schema(self):
        fti = getUtility(IDexterityFTI, name=self.context.portal_type)
        schema = fti.lookupSchema()
        return schema

    @property
    def htmlIDs(self):
        ids = []
        schema = self._schema
        for f in schema:
            field = schema[f]
            if ITextLine.providedBy(field) or IRichText.providedBy(field):
                ids.append('form.widgets.%s' % f)
        return ids

    @property
    def tinyIDs(self):
        ids = []
        schema = self._schema
        for f in schema:
            if IRichText.providedBy(schema[f]):
                ids.append('form.widgets.%s' % f)
        return ids

    @property
    def contentUID(self):
        return IUUID(self.context)

    def getNodeTextFromHtmlID(self, html_id):
        fname = html_id[13:]
        value = self._schema[fname].get(self.context)
        if IRichTextValue.providedBy(value):
            return value.raw
        return value

    def setNodeTextFromHtmlID(self, html_id, text):
        fname = html_id[13:]
        field = self._schema[fname]
        text = field.fromUnicode(text)
        field.set(self.context, text)
