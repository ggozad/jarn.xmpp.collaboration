# Copyright (c) 2003-2009 Ralph Meijer
# See LICENSE for details.

"""
Tests for L{wokkel.ping}.
"""

from zope.interface import verify

from twisted.internet import defer
from twisted.trial import unittest
from twisted.words.protocols.jabber.error import StanzaError
from twisted.words.protocols.jabber.jid import JID
from twisted.words.protocols.jabber.xmlstream import toResponse

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
        """
        Upon receiving a presence, the protocol MUST set itself up,
        as well as send the initial text to the user.
        """
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

        message = self.stub.output[-1]
        self.assertEqual(
            "<message to='test@example.com'>" +
            "<x xmlns='http://jarn.com/ns/collaborative-editing'>" +
            "<item action='set' node='test-node'>foo</item>" +
            "</x></message>", message.toXml())

        xml = """<presence from='test@example.com' to='example.com'
                    type='unavailable'/>"""
        self.stub.send(parseXml(xml))
        self.assertEqual({}, self.protocol.node_participants)
        self.assertEqual({}, self.protocol.participant_nodes)
        self.assertEqual({}, self.protocol.shadow_copies)

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
            for item in info:
                discoInfo.append(item)
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
