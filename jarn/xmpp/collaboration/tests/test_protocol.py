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

from jarn.xmpp.collaboration import protocol


class DifferentialSyncronisationHandlerTest(unittest.TestCase):
    """
    Tests for the DifferentialSynchronisationProtocol.
    """

    def setUp(self):
        self.stub = XmlStreamStub()
        self.protocol = protocol.DifferentialSyncronisationHandler()
        self.protocol.xmlstream = self.stub.xmlstream
        self.protocol.connectionInitialized()

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
