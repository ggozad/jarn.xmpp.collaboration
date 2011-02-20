from zope.interface import Interface


class IDifferentialSyncronisation(Interface):
    """ Marker interface for the collaborative editing protocol.
    """


class ICollaborativeEditingComponent(Interface):
    """ Marker interface for the collaborative editing component.
    """
