"""

A setuptool installer that crucially declares the consumer on an entry-point
that moksha is looking for.

Without this, fedmsg-hub won't find your consumer.
"""

from setuptools import setup
setup(
    name='fedmsg-cvs',
    entry_points="""
    [moksha.consumer]
    cvs = cvs_consumer:CVSConsumer
    """,
)
