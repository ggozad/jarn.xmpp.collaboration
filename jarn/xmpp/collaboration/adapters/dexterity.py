from zope.cachedescriptors.property import Lazy as lazy_property
from zope.component import adapts
from zope.interface import implements
from zope.schema import getFieldsInOrder
from zope.schema.interfaces import ITextLine, IText

from plone.uuid.interfaces import IUUID
from plone.dexterity.interfaces import IDexterityContent
from plone.dexterity.utils import iterSchemata
from plone.app.textfield.interfaces import IRichText, IRichTextValue

from jarn.xmpp.collaboration.adapters.base import CEAdapterBase
from jarn.xmpp.collaboration.interfaces import ICollaborativelyEditable


class DexterityCEAdapter(CEAdapterBase):
    implements(ICollaborativelyEditable)
    adapts(IDexterityContent)

    def __init__(self, context):
        self.context = context

    @lazy_property
    def _ce_fields(self):
        field_dict = {}
        for schemata in iterSchemata(self.context):
            for name, field in getFieldsInOrder(schemata):
                if ITextLine.providedBy(field) or \
                   IText.providedBy(field) or \
                   IRichText.providedBy(field):
                    field_dict[name] = field
        return field_dict

    @property
    def htmlIDs(self):
        ids = []
        fields = self._ce_fields.items()
        for name, field in fields:
            if ITextLine.providedBy(field) or IText.providedBy(field):
                ids.append('form-widgets-%s' % name)
            elif IRichText.providedBy(field):
                ids.append('form.widgets.%s' % name) # Talk about uniformity ;)
        return ids

    @property
    def contentUID(self):
        return IUUID(self.context)

    def getNodeTextFromHtmlID(self, html_id):
        name = html_id[13:]
        value = self._ce_fields[name].get(self.context)
        if IRichTextValue.providedBy(value):
            return value.raw
        return value

    def setNodeTextFromHtmlID(self, html_id, text):
        name = html_id[13:]
        field = self._ce_fields[name]
        text = field.fromUnicode(text)
        field.set(self.context, text)
