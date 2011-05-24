from zope.interface import Interface, Attribute


class ICollaborativelyEditable(Interface):
    """
    Provides interface needed to collaboratively edit an object.
    """

    nodeToId = Attribute("""A mapping of node id -> html id for this object""")
    idToNode = Attribute("""A mapping of html id -> node id for this object""")

    def getNodeTextFromHtmlID(html_id):
        """Get the text of the object identified by html_id."""

    def setNodeTextFromHtmlID(html_id, text):
        """Set the text of the object identified by html_id."""


class INonLockable(Interface):
    """
    Marker interface for objects that should not be TTW lockable.
    """


class IDifferentialSyncronisation(Interface):
    """
    Marker interface for the collaborative editing protocol.
    """


class ICollaborativeEditingComponent(Interface):
    """
    Marker interface for the collaborative editing component.
    """
