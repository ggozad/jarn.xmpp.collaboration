from zope.interface import verify

from twisted.internet import defer
from twisted.trial import unittest
from twisted.words.protocols.jabber.jid import JID

from wokkel import disco, iwokkel
from wokkel.generic import parseXml
from wokkel.test.helpers import XmlStreamStub

from jarn.xmpp.collaboration.tests import mock


class DifferentialSyncronisationHandlerTest(unittest.TestCase):
    """
    Tests for the DifferentialSynchronisationProtocol.
    """

    def setUp(self):
        self.stub = XmlStreamStub()
        self.protocol = mock.MockDifferentialSyncronisationHandler()
        self.protocol.xmlstream = self.stub.xmlstream
        self.protocol.connectionInitialized()

    def test_onPresence(self):
        # User test@example.com joins
        self.protocol.mock_text['test-node'] = 'foo'
        xml = """<presence from='test@example.com' to='example.com'>
                    <query xmlns='http://jarn.com/ns/collaborative-editing'
                           node='test-node'/>
                 </presence>"""
        self.stub.send(parseXml(xml))
        self.assertEqual({u'test-node': set([u'test@example.com'])},
                         self.protocol.node_participants)
        self.assertEqual({u'test@example.com': set([u'test-node'])},
                          self.protocol.participant_nodes)
        self.assertEqual({u'test-node': 'foo'},
                         self.protocol.shadow_copies)

        # Another user joins:
        xml = """<presence from='test2@example.com' to='example.com'>
                    <query xmlns='http://jarn.com/ns/collaborative-editing'
                           node='test-node'/>
                 </presence>"""
        self.stub.send(parseXml(xml))

        # The new user should receive a user-joined for the existing user.
        message = self.stub.output[-1]
        self.assertEqual(
            "<message to='test2@example.com'>" +
            "<x xmlns='http://jarn.com/ns/collaborative-editing'>" +
            "<item action='user-joined' node='test-node' user='test@example.com'/>" +
            "</x></message>", message.toXml())

        #The already active user should receive a user-joined
        message = self.stub.output[-2]
        self.assertEqual(
            "<message to='test@example.com'>" +
            "<x xmlns='http://jarn.com/ns/collaborative-editing'>" +
            "<item action='user-joined' node='test-node' user='test2@example.com'/>" +
            "</x></message>", message.toXml())

        # Then test@example.com leaves the node.

        xml = """<presence from='test@example.com' to='example.com'
                    type='unavailable'/>"""
        self.stub.send(parseXml(xml))

        # Make sure the test@example.com is indeed gone,
        self.assertEqual({u'test-node': set([u'test2@example.com'])},
                         self.protocol.node_participants)
        self.assertEqual({u'test2@example.com': set([u'test-node'])},
                         self.protocol.participant_nodes)

        # test2@example should have received a notification
        message = self.stub.output[-1]
        self.assertEqual(
            "<message to='test2@example.com'>" +
            "<x xmlns='http://jarn.com/ns/collaborative-editing'>" +
            "<item action='user-left' node='test-node' user='test@example.com'/>" +
            "</x></message>", message.toXml())

        # Then test2@example.com leaves as well.
        xml = """<presence from='test2@example.com' to='example.com'
                    type='unavailable'/>"""
        self.stub.send(parseXml(xml))

        self.assertEqual({}, self.protocol.node_participants)
        self.assertEqual({}, self.protocol.participant_nodes)
        self.assertEqual({}, self.protocol.shadow_copies)

    def test_getShadowCopyIQ(self):
        # User test@example.com joins
        self.protocol.mock_text['test-node'] = 'foo'
        xml = """<presence from='test@example.com' to='example.com'>
                    <query xmlns='http://jarn.com/ns/collaborative-editing'
                           node='test-node'/>
                 </presence>"""
        self.stub.send(parseXml(xml))

        # And requests the shadow copy of 'test-node'
        xml = """<iq from='test@example.com' to='example.com' type='get'>
                    <shadowcopy xmlns='http://jarn.com/ns/collaborative-editing'
                           node='test-node'/>
                 </iq>"""
        self.stub.send(parseXml(xml))
        response = self.stub.output[-1]
        self.assertEqual("<iq to='test@example.com' from='example.com' type='result'>" +
                         "<shadowcopy xmlns='http://jarn.com/ns/collaborative-editing' node='test-node'>foo</shadowcopy>" +
                         "</iq>", response.toXml())

        # Requesting the shadow copy of an non-existent node should result in Unauthorized error
        xml = """<iq from='test@example.com' to='example.com' type='get'>
                    <shadowcopy xmlns='http://jarn.com/ns/collaborative-editing'
                           node='unknown-node'/>
                 </iq>"""
        self.stub.send(parseXml(xml))
        response = self.stub.output[-1]
        self.assertEqual("<iq to='test@example.com' from='example.com' type='error'>" +
                         "<error xmlns='http://jarn.com/ns/collaborative-editing'>Unauthorized</error></iq>",
                         response.toXml())

        # User test2@example.com who has not sent a presence to the component should not be able
        # to retrieve the text.
        xml = """<iq from='test2@example.com' to='example.com' type='get'>
                 <shadowcopy xmlns='http://jarn.com/ns/collaborative-editing'
                           node='test-node'/>
                 </iq>"""
        self.stub.send(parseXml(xml))
        response = self.stub.output[-1]
        self.assertEqual("<iq to='test2@example.com' from='example.com' type='error'>" +
                         "<error xmlns='http://jarn.com/ns/collaborative-editing'>Unauthorized</error></iq>",
                         response.toXml())

    def test_onPatch(self):
        # 'foo' is the initial text. foo and bar present.
        self.protocol.mock_text['test-node'] = 'foo'
        xml = """<presence from='foo@example.com' to='example.com'>
                    <query xmlns='http://jarn.com/ns/collaborative-editing'
                           node='test-node'/>
                 </presence>"""
        self.stub.send(parseXml(xml))
        xml = """<presence from='bar@example.com' to='example.com'>
                    <query xmlns='http://jarn.com/ns/collaborative-editing'
                           node='test-node'/>
                 </presence>"""
        self.stub.send(parseXml(xml))

        # bar sends a patch changing the text to 'foobar'.
        xml = """<iq from='bar@example.com' to='example.com' id='id_1' type='set'>
                    <patch xmlns='http://jarn.com/ns/collaborative-editing'
                        node='test-node'>@@ -1,3 +1,6 @@\n foo\n+bar\n</patch>
                </iq>"""
        self.stub.send(parseXml(xml))

        # He should have received a 'success' reply
        response = self.stub.output[-2]
        self.assertEqual(
            "<iq to='bar@example.com' from='example.com' id='id_1' type='result'>" +
            "<success xmlns='http://jarn.com/ns/collaborative-editing'/></iq>", 
            response.toXml())

        # foo receives the same patch.
        iq = self.stub.output[-1]
        self.assertEqual(
            "<iq to='foo@example.com' type='set' id='H_0'>" +
            "<patch xmlns='http://jarn.com/ns/collaborative-editing' " +
            "node='test-node' user='bar@example.com'>@@ -1,3 +1,6 @@\n foo\n+bar\n</patch></iq>",
            iq.toXml())

        # The shadow copy is 'foobar'
        self.assertEqual(u'foobar', self.protocol.shadow_copies['test-node'])

    def test_interfaceIDisco(self):
        """
        The handler should provice Service Discovery information.
        """
        verify.verifyObject(iwokkel.IDisco, self.protocol)

    def test_getDiscoInfo(self):
        """
        The namespace should be returned as a supported feature.
        """

        def cb(info):
            discoInfo = disco.DiscoInfo()
            for item in info:
                discoInfo.append(item)
            self.assertIn('http://jarn.com/ns/collaborative-editing',
                          discoInfo.features)

        d = defer.maybeDeferred(self.protocol.getDiscoInfo,
                                JID('user@example.org/home'),
                                JID('pubsub.example.org'),
                                '')
        d.addCallback(cb)
        return d

    def test_getDiscoInfoNode(self):
        """
        The namespace should not be returned for a node.
        """

        def cb(info):
            discoInfo = disco.DiscoInfo()
            self.assertEqual([], info)
            self.assertNotIn('http://jarn.com/ns/collaborative-editing',
                             discoInfo.features)

        d = defer.maybeDeferred(self.protocol.getDiscoInfo,
                                JID('user@example.org/home'),
                                JID('pubsub.example.org'),
                                'test')
        d.addCallback(cb)
        return d

    def test_getDiscoItems(self):
        """
        Items are not supported by this handler.
        """

        def cb(items):
            self.assertEquals(0, len(items))

        d = defer.maybeDeferred(self.protocol.getDiscoItems,
                                JID('user@example.org/home'),
                                JID('pubsub.example.org'),
                                '')
        d.addCallback(cb)
        return d
