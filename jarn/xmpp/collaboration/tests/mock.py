from jarn.xmpp.collaboration.protocol import DifferentialSyncronisationHandler


class MockDifferentialSyncronisationHandler(DifferentialSyncronisationHandler):
    """
    A mock implementation of the DifferentialSyncronisationHandler which
    contains a sample text node and handles events that are to be overriden
    by component implementations.
    """

    def __init__(self):
        super(MockDifferentialSyncronisationHandler, self).__init__()
        self.mock_text = {'test-node': ''}
        self.mock_users = {}

    def getNodeText(self, user, node):
        return self.mock_text.get(node)

    def setNodeText(self, user, node, text):
        self.mock_text['node'] = text

    def userJoined(self, user, node):
        pass

    def userLeft(self, user, node):
        pass


class MockCollaborationComponent(object):
    """
    A mock collaboration component.
    """

    pass