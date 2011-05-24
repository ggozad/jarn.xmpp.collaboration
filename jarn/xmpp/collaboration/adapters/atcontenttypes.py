from Products.Archetypes.interfaces import IStringField, ITextField
from Products.ATContentTypes.interfaces import IATContentType

from zope.cachedescriptors.property import Lazy as lazy_property
from zope.component import adapts
from zope.interface import implements

from jarn.xmpp.collaboration.interfaces import ICollaborativelyEditable
from jarn.xmpp.collaboration.adapters.base import CEAdapterBase


class ATContentTypesCEAdapter(CEAdapterBase):
    implements(ICollaborativelyEditable)
    adapts(IATContentType)

    @lazy_property
    def _ce_fields(self):
        ce_fields = [field
                     for field in self.context.schema.fields()
                     if (IStringField.providedBy(field)
                         or ITextField.providedBy(field))
                        and field.schemata=='default'
                        and field.getName()!='id']
        return ce_fields

    @property
    def contentUID(self):
        return self.context.UID()


    @property
    def htmlIDs(self):
        return [field.getName() for field in self._ce_fields]

    def getNodeTextFromHtmlID(self, html_id):
        return self.context.schema[html_id].getRaw(self.context).decode('utf-8')

    def setNodeTextFromHtmlID(self, html_id, text):
        self.context.schema[html_id].set(self.context, text)
