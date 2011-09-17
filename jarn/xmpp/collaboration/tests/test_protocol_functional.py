from twisted.trial import unittest
from wokkel.generic import parseXml
from wokkel.test.helpers import XmlStreamStub

from jarn.xmpp.collaboration.tests import mock
from jarn.xmpp.collaboration.dmp import diff_match_patch


class DifferentialSyncronisationHandlerFunctionalTest(unittest.TestCase):
    """
    Functional test for the DifferentialSynchronisationProtocol.
    """

    def setUp(self):
        self.stub = XmlStreamStub()
        self.protocol = mock.MockDifferentialSyncronisationHandler()
        self.protocol.xmlstream = self.stub.xmlstream
        self.protocol.connectionInitialized()

        self.original = \
            """
            Hamlet: Do you see yonder cloud that's almost in shape of a camel?
            Polonius: By the mass, and 'tis like a camel, indeed.
            Hamlet: Methinks it is like a weasel.
            Polonius: It is backed like a weasel.
            Hamlet: Or like a whale?
            Polonius: Very like a whale.
            """

        self.plain = \
            """
            Hamlet: Do you see the cloud over there that's almost the shape of a camel?
            Polonius: By golly, it is like a camel, indeed.
            Hamlet: I think it looks like a weasel.
            Polonius: It is shaped like a weasel.
            Hamlet: Or like a whale?
            Polonius: It's totally like a whale.
            """

        self.trekkie = \
            """
            Kirk: Do you see yonder cloud that's almost in shape of a Klingon?
            Spock: By the mass, and 'tis like a Klingon, indeed.
            Kirk: Methinks it is like a Vulcan.
            Spock: It is backed like a Vulcan.
            Kirk: Or like a Romulan?
            Spock: Very like a Romulan.
            """

        self.final = \
            """
            Kirk: Do you see the cloud over there that's almost the shape of a Klingon?
            Spock: By golly, it is like a Klingon, indeed.
            Kirk: I think it looks like a Vulcan.
            Spock: It is shaped like a Vulcan.
            Kirk: Or like a Romulan?
            Spock: It's totally like a Romulan.
            """

        self.protocol.mock_text = {'hamlet': self.original}
        self.dmp = diff_match_patch()

    def test_full_cycle(self):
        # foo logs in.
        xml = """<presence from='foo@example.com' to='example.com'>
                    <query xmlns='http://jarn.com/ns/collaborative-editing'
                           node='hamlet'/>
                 </presence>"""
        self.stub.send(parseXml(xml))

        # bar logs in.
        xml = """<presence from='bar@example.com' to='example.com'>
                    <query xmlns='http://jarn.com/ns/collaborative-editing'
                           node='hamlet'/>
                 </presence>"""
        self.stub.send(parseXml(xml))

        # foo changes the Sheakespearean text to plain english,
        # and creates a patch.
        original2plain_patch = self.dmp.patch_make(self.original, self.plain)
        original2plain_text = self.dmp.patch_toText(original2plain_patch)
        xml = "<iq from='foo@example.com' to='example.com' type='set'>" + \
              "<patch xmlns='http://jarn.com/ns/collaborative-editing' node='hamlet'>" + \
              original2plain_text + \
              "</patch></iq>"
        self.stub.send(parseXml(xml))

        # Before receiving a patch from the server bar has already updated
        # his own version to trekkie and sends it away.
        original2trekkie_patch = self.dmp.patch_make(self.original, self.trekkie)
        original2trekkie_text = self.dmp.patch_toText(original2trekkie_patch)
        xml = "<iq from='bar@example.com' to='example.com' type='set'>" + \
              "<patch xmlns='http://jarn.com/ns/collaborative-editing' node='hamlet'>" + \
              original2trekkie_text + \
              "</patch></iq>"
        self.stub.send(parseXml(xml))

        # So now, both have obtained a patch to apply each other changes on
        # the already changed document. They are the same and merged perfectly.
        iq_to_foo = self.stub.output[-1]
        plain2final_text = iq_to_foo.patch.children[0]
        plain2final_patch = self.dmp.patch_fromText(plain2final_text)
        foo_result = self.dmp.patch_apply(plain2final_patch, self.plain)
        foo_final = foo_result[0]
        self.assertEqual(self.final, foo_final)

        iq_to_bar = self.stub.output[-3]
        trekkie2final_text = iq_to_bar.patch.children[0]
        trekkie2final_patch = self.dmp.patch_fromText(trekkie2final_text)
        bar_result = self.dmp.patch_apply(trekkie2final_patch, self.trekkie)
        bar_final = bar_result[0]
        self.assertEqual(self.final, bar_final)
