"""

This is a config file that must appear in ./fedmsg.d/ alongside the other
config files from the fedmsg development checkout.

In production, this should go into /etc/fedmsg.d/ but for development it can
just live in your cwd/pwd.

"""

config = {
    # whether the consumer is enabled
    'cvs.consumer.enabled': True,

    # allow this amount of seconds to collect file commits for same commitid
    'cvs.consumer.delay': 15,

    # URL to CVSWEB
    'cvs.cvsweb_url': 'https://cvs.example.net',

    # ViewVC specific
    'cvs.co_url': '%(url)s/%(filename)s?view=markup&revision=%(rev)s',
    'cvs.diff_url': '%(url)s/%(filename)s?r1=%(old_rev)s&r2=%(new_rev)s&f=h',
    'cvs.log_url': '%(url)s/%(filename)s?r1=%(rev)s#rev%(rev)s',
}
