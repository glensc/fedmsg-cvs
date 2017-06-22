"""

Consumer to show how to write a service that does stuff in
response to message on the `fedmsg bus <http://fedmsg.rtfd.org>`_.
"""

import fedmsg.consumers

class CVSConsumer(fedmsg.consumers.FedmsgConsumer):
    # cvs_consumer_enabled must be set to True in the config in fedmsg.d/ for
    # this consumer to be picked up and run when the fedmsg-hub starts.
    config_key = "cvs.consumer.enabled"

    def __init__(self, hub):
        # listen to file commits
        self.topic = self.abs_topic(hub.config, "cvs.file-commit")
        # produce commits by commitids
        self.send_topic = self.abs_topic(hub.config, "cvs.commit")

        super(CVSConsumer, self).__init__(hub)
        self.log.info("topic: %s, send_topic: %s" % (self.topic, self.send_topic))

    # no proper way to configure just topic suffix
    # https://github.com/fedora-infra/fedmsg/pull/428
    def abs_topic(self, config, topic):
        """
        prefix topic with topic_prefix and environment config values
        """
        topic_prefix = config.get('topic_prefix')
        environment = config.get('environment')
        return "%s.%s.%s" % (topic_prefix, environment, topic)

    def consume(self, msg):
        self.log.info("CVS[%(topic)s]: %(user)s: %(module)s: %(message)s" % {
            'topic': msg['topic'],
            'user': msg['body']['msg']['user'],
            'module': msg['body']['msg']['module'],
            'message': msg['body']['msg']['message'],
        })
        self.log.info("%r" % msg)

        message = {
            'commitid' : msg['body']['msg']['commitid'],
        }
        self.log.info("send %s: %r" % (self.send_topic, message))
