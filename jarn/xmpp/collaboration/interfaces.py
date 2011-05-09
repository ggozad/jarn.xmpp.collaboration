from zope.interface import Interface


class ICollaborativelyEditable(Interface):
    """
    Marker interface for objects that are collaboratively editable.
    """


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
