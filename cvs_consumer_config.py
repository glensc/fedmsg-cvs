"""

This is a config file that must appear in ./fedmsg.d/ alongside the other
config files from the fedmsg development checkout.

In production, this should go into /etc/fedmsg.d/ but for development it can
just live in your cwd/pwd.

"""

config = {
    # whether the consumer is enabled
    'cvs.consumer.enabled': True,

    # allow 60 seconds to collect file commits for same commitid
    'cvs.consumer.delay': 60,
}
