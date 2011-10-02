Introduction
============

``jarn.xmpp.collaboration`` defines a protocol to do real-time collaborative editing through XMPP and provides:

* a generic overridable implementation of the server component.
* a Plone-specific implementation (server component and javascript client).
* adapters for basic Plone content types (Pages and News Items).

It is part of a suite of packages aiming to provide XMPP services to Plone. The other two packages are

* `jarn.xmpp.twisted`_, provides XMPP-specific protocol implementation for twisted.
* `jarn.xmpp.core`_ provides facilities for presence, messaging, chatting and microblogging.

Requirements
============
Please see ``jarn.xmpp.core`` for details on setting up your Plone site and XMPP server. If you are not using the recipe included in `jarn.xmpp.buildout` you will need to configure your ejabberd to allow connections from the collaboration component. For ``ejabberd`` this is done by including the following in your config file::

    {{5347, {0,0,0,0} }, ejabberd_service, [
      {access, all},
      {shaper_rule, fast},
      {ip, {127, 0, 0, 1}},
      {hosts, ["collaboration.localhost"],
       [{password, "secret"}]
      }
     ]},


The instance that is going to be running the xmpp component should include the ``component.zcml``. You can do this in your buildout::

    zcml-additional =
      <configure xmlns="http://namespaces.zope.org/zope">
          <include package="jarn.xmpp.twisted" file="reactor.zcml" />
          <include package="jarn.xmpp.collaboration" file="component.zcml" />
      </configure>

Finally you will need to "activate" the product in the Plone control panel. After doing so, please edit the registry settings and in particular:

* ``jarn.xmpp.collaborationJID`` is the Jabber id of the collaborative editing service component. Essentially if ``myserver`` is your XMPP domain ``collaboration.myserver`` is a good name. This should match the name you gave to ``ejabberd``, see above. Default is ``collaboration.localhost``.

* ``jarn.xmpp.collaborationPassword`` is the password the component will use to connect to your xmpp server, see above. Default is ``secret``.

* ``jarn.xmpp.collaborationPort`` is the port that your XMPP server allows components to connect to, see above. Default is ``5347``.

Usage
=====

Using ``jarn.xmpp.collaboration`` is easy once you have gotten over setting it up. There are no special views to use when you collaboratively edit content. If an adapter to *ICollaborativelyEditable* exists for your content then accessing its edit form will allow multiple users to edit simultaneously.

Out of the box there exist adapters for archetypes as well as dexterity-based content types. For AT content types, fields that implement ``IStringField`` or ``ITextField`` will automatically get collaborative editing support. For Dexterity the fields that will be automatically included are those that provide ``ITextLine``, ``IText`` or ``IRichText`` regardless of the *behavior* by which they are defined. Note that the javascript client assumes that TinyMCE is used. Collaboration on rich text fields will not work with Kupu.

Protocol specification.
=========================

Initialization
--------------
In order to initiate a collaborative editing session, the party sends a ``presence`` stanza to the server component indicating on which node he wishes to work on. The party MUST specify the `node` attribute in the ``query`` element::

    <presence from='foo@example.com/work' to='collaboration.example.com'>
        <query xmlns='http://jarn.com/ns/collaborative-editing' node='collab-node'/>
    </presence>

Upon receipt a ``message`` stanza is sent to anyone else who might be editing the same node notifying them of the new participant::

    <message from='collaboration.example.com' to='bar@example.com/home'>
        <x xmlns='http://jarn.com/ns/collaborative-editing'>
            <item action='user-joined' node='collab-node' user='foo@example.com/work'/>
        </x>
    </message>

The newly joined user also receives a similar notification about existing users ::

    <message from='collaboration.example.com' to='foo@example.com/home'>
        <x xmlns='http://jarn.com/ns/collaborative-editing'>
            <item action='user-joined' node='collab-node' user='bar@example.com/work'/>
        </x>
    </message>

To complete the initialization the new party MUST request the current version of the node from the server::

    <iq id='123' from='foo@example.com/work' to='collaboration.example.com' type='get'>
        <shadowcopy xmlns='http://jarn.com/ns/collaborative-editing' node='collab-node'/>
    </iq>

To which the server replies providing his current copy of the text::

    <iq id='123' from='collaboration.example.com' to='foo@example.com/work'  type='result'>
         <shadowcopy xmlns='http://jarn.com/ns/collaborative-editing' node='collab-node'>Hello world</shadowcopy>
     </iq>

In case the node does not exist, or the user has no privileges granting him access, the server MUST reply with an error, for instance::

    <iq id='123' from='collaboration.example.com' to='foo@example.com/work' type='error'>
        <error xmlns='http://jarn.com/ns/collaborative-editing'>Unauthorized</error>
    </iq>


Editing cycle
-------------
When a party edits the text, it notifies the server by sending an ``iq`` stanza of type ``set``. The stanza contains one ``patch`` element which MUST specify the `node` they apply to, and in their body contain the patch created by the Diff-Match-Patch algorithm in text format. For instance if the text changed from "`Hello world`" to "`Hello world, have a nice day!`" the message would be::

    <iq id='234' from='foo@example.com/work' to='collaboration.example.com' type='set'>
        <patch xmlns='http://jarn.com/ns/collaborative-editing' node='collab-node' digest='b9e8241b3cc82c43af870641078ee03f'>
            @@ -4,8 +4,26 @@\n lo world\n+, have a nice day!\n
        </patch>
    </iq>

If the server succeeds to apply the patch to its shadow copy, it replies with a `success` result::

    <iq id='234' from='collaboration.example.com' to='foo@example.com/work' type='result'>
        <success xmlns='http://jarn.com/ns/collaborative-editing'/>
    </iq>

Additionally the server MUST broadcast the patch to all other parties who are present on the node::

    <iq id='345' from='collaboration.example.com' to='bar@example.com/home' type='set'>
        <patch xmlns='http://jarn.com/ns/collaborative-editing' node='collab-node'>
            @@ -4,8 +4,26 @@\n lo world\n+, have a nice day!\n
        </patch>
    </iq>

The parties  MUST apply it to their text.
If applying the patch fails, the server (or client) MUST reply with an ``iq`` stanza of type `error`. For instance if a patch was sent to the server and for some reason it was not possible to apply it to the shadow copy, the server would reply::

    <iq id='234' from='collaboration.example.com' to='foo@example.com/work' type='error'>
        <error xmlns='http://jarn.com/ns/collaborative-editing'>
            Patch @@ -4,8 +4,26 @@\n lo world\n+, have a nice day!\n could not be applied.
        </error>
    </iq>

In that case the client SHOULD sync again the current copy by sending an ``iq`` stanza of type `get`requesting the shadow copy, see the `Initialization` section above.

Finally, a ``patch`` element MAY have the ``digest`` attribute. In that case, the server SHOULD check the checksum and if there is a mismatch, reply with an error stanza if appropriate. Note that currently the checksum algorithm is not negotiated and is assumed to be MD5 hex digest.

Focusing
--------
In an environment where multiple nodes are edited in the same time (for instance in a context where the content has more than one collaboratively editable field) the client CAN send a notification specifying which particular node he is currently editing::

    <message from='foo@example.com/work' to='collaboration.example.com'>
        <x xmlns='http://jarn.com/ns/collaborative-editing'>
            <item node='collab-node' action='focus' user='foo@example.com/work'/>
        </x>
    </message>

The server MUST propagate the message to all other users that are currently collaborating on the node::

    <message from='collaboration.example.com' to='bar@example.com/home'>
        <x xmlns='http://jarn.com/ns/collaborative-editing'>
            <item node='collab-node' action='focus' user='foo@example.com/work'/>
        </x>
    </message>

Saving
------
At any point a party can request a save. This is done by sending a message whose `item` MUST indicate the node and its action must be set to `save`::

    <message from='foo@example.com/work' to='collaboration.example.com'>
        <x xmlns='http://jarn.com/ns/collaborative-editing'>
            <item node='collab-node' action='save'></item>
        </x>
    </message>

It is up to the server component to enforce any security considerations on saving.

Termination
-----------
The session is terminated when the party sends an `unavailable` presence::

    <presence from='foo@example.com/work' type='unavailable' />

Upon receipt, the server notifies any party that might still be editing the node::

    <message from='collaboration.example.com' to='bar@example.com/home'>
        <x xmlns='http://jarn.com/ns/collaborative-editing'>
            <item action='user-left' node='collab-node' user='foo@example.com/work'/>
        </x>
    </message>

Credits
=======

* Most of this work was done using the 10% time available to `Jarn AS`_ employees for the development of open-source projects.
* David Glick (davisagli) for dexterity support and general awesomeness.
* ``jarn.xmpp.collaboration`` relies on the wonderful `Diff-Match-Patch`_ from Neil Fraser at Google. It is distributed under the Apache License 2.0.

.. _Diff-Match-Patch: http://code.google.com/p/google-diff-match-patch
.. _Jarn AS: http://jarn.com
.. _jarn.xmpp.twisted: http://pypi.python.org/pypi/jarn.xmpp.twisted
.. _jarn.xmpp.core: http://pypi.python.org/pypi/jarn.xmpp.core


