import unittest2 as unittest

from jarn.xmpp.collaboration.dmp import diff_match_patch as dmp


class DiffMatchPatchTest(unittest.TestCase):

    def setUp(self):
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

        self.dmp = dmp()

    def test_apply(self):
        patch_original_plain = self.dmp.patch_make(self.original, self.plain)
        text, result = self.dmp.patch_apply(patch_original_plain, self.trekkie)
        self.assertEqual(result, [True, True, True, True, True, True])
        self.assertEqual(text, self.final)
