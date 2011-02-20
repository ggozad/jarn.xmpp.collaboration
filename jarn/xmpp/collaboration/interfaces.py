from zope.interface import Interface


class IDifferentialSyncronisation(Interface):
    """
    Marker interface for the collaborative editing protocol.
    """


class ICollaborativelyEditable(Interface):
    """
    Marker interface for content that is collaboratively editable.
    """


class ICollaborativeEditingComponent(Interface):
    """
    Marker interface for the collaborative editing component.
    """
