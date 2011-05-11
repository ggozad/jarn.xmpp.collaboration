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
Please see ``jarn.xmpp.core`` for details on setting up your Plone site and xmpp server. Additionally, your XMPP server must accept connections from external componenents. For ``ejabberd`` this is done by::

    {5347, ejabberd_service, [
        {access, all},
        {shaper_rule, fast},
        {ip, {127, 0, 0, 1}},
        {hosts, ["collaboration.myserver"],
            [{password, "secret"}]
        }
    ]},

The instance that is going to be running the xmpp component should include the ``component.zcml``. You can do this in your buildout::

    zcml-additional =
      <configure xmlns="http://namespaces.zope.org/zope">
          <include package="jarn.xmpp.twisted" file="reactor.zcml" />
          <include package="jarn.xmpp.collaboration" file="component.zcml" />
      </configure>

Usage
=====

Using ``jarn.xmpp.collaboration`` is easy once you have gotten over setting it up. There are no special views to use when you collaboratively edit content. If an adapter to *ICollaborativelyEditable* exists for your content then accessing its edit form will allow multiple users to edit simultaneously.

Out of the box there exist adapters for ATDocument and ATNewsItem as well as a base adapter to ease adapting Archtypes-based content types. These can be used as starting points to allow editing on custom types.

Protocol specification.
=========================

Initialization
--------------
In order to initiate a collaborative editing session, the party sends a presence to the server indicating on which node he wishes to work on. The party MUST specify the `node` attribute in the `query` element::

    <presence from='foo@example.com/work' to='collaboration.example.com'>
        <query xmlns='http://jarn.com/ns/collaborative-editing'
            node='collab-node'/>
    </presence>

Upon receipt the server sends a message to the party setting the initial text of the node. If the node is already being edited the initial text is the most current copy on the server::

    <message from='collaboration.example.com' to='foo@example.com/work'>
        <x xmlns='http://jarn.com/ns/collaborative-editing'>
            <item action='set' node='collab-node'>Hello world</item>
        </x>
    </message>

Editing cycle
-------------
When a party edits the text, it notifies the server by sending a message. The message contains one or more `item` elements which MUST specify the `node` they apply to, have the attribute `action` set to `patch`, and in their body contain the patch created by the Diff-Match-Patch algorithm in text format. For instance if the text changed from "`Hello world`" to "`Hello world, have a nice day!`" the message would be::

    <message from='foo@example.com/work' to='collaboration.example.com'>
        <x xmlns='http://jarn.com/ns/collaborative-editing'>
            <item node='collab-node' action='patch'>@@ -4,8 +4,26 @@\n lo world\n+, have a nice day!\n</item>
        </x>
    </message>

If the server succeeds to apply the patch to its shadow copy, it broadcasts the patch to all other parties who are present on the node. The parties  MUST apply it to their text::

    <message from='collaboration.example.com' to='bar@example.com/home'>
        <x xmlns='http://jarn.com/ns/collaborative-editing'>
            <item node='collab-node' action='patch'>@@ -4,8 +4,26 @@\n lo world\n+, have a nice day!\n</item>
        </x>
    </message>

If the server fails to apply the patch (because for instance there was a network problem and the client fell out of sync, or the diff-match-patch application failed), it SHOULD send a ``set`` action to the party with its shadow copy as text.

Focusing
--------
In an environment where multiple nodes are edited in the same time (for instance in a context where the content has more than one collaboratively editable fields) the client CAN send a notification specifying which particular node he is currently editing::

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

Credits
=======

* Most of this work was done using the 10% time available to `Jarn AS`_ employees for the development of open-source projects.
* ``jarn.xmpp.collaboration`` relies on the wonderful `Diff-Match-Patch`_ from Neil Fraser at Google. It is distributed under the Apache License 2.0.

.. _Diff-Match-Patch: http://code.google.com/p/google-diff-match-patch
.. _Jarn AS: http://jarn.com
.. _jarn.xmpp.twisted: http://pypi.python.org/pypi/jarn.xmpp.twisted
.. _jarn.xmpp.core: http://pypi.python.org/pypi/jarn.xmpp.core

