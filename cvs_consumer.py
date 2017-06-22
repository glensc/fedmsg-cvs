"""

Consumer to show how to write a service that does stuff in
response to message on the `fedmsg bus <http://fedmsg.rtfd.org>`_.
"""

import fedmsg
import fedmsg.consumers
import moksha.hub.reactor

class CVSConsumer(fedmsg.consumers.FedmsgConsumer):
    # cvs_consumer_enabled must be set to True in the config in fedmsg.d/ for
    # this consumer to be picked up and run when the fedmsg-hub starts.
    config_key = "cvs.consumer.enabled"

    def __init__(self, hub):
        # listen to file commits
        self.topic = self.abs_topic(hub.config, "cvs.file-commit")

        super(CVSConsumer, self).__init__(hub)

        # This is required.
        # It is the number of seconds that we should wait
        # until we ultimately act on a cvs-file commit messages.
        self.delay = self.hub.config['cvs.consumer.delay']

        # We use this to manage our state
        self.queued_messages = []

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
        msg = msg['body']
        self.log.info("CVS: Got a message %r" % msg['topic'])

        def delayed_consume():
	    if self.queued_messages:
                try:
                    self.action(self.queued_messages)
                finally:
                    # Empty our list at the end of the day.
                    self.queued_messages = []
            else:
                self.log.debug("Woke up, but there were no messages.")

        self.queued_messages.append(msg)

        moksha.hub.reactor.reactor.callLater(self.delay, delayed_consume)

    def action(self, messages):
	commits = {}
	for msg in messages:
            self.log.info("msg: %r" % msg)
            commitid = msg['msg']['commitid']
            if not commits.has_key(commitid):
                commits[commitid] = {
                    'files': [],
                }

            for file in msg['msg']['files']:
                # prepend "module" to filename
                file['filename'] = msg['msg']['module'] + '/' + file['filename']
                # commitid not relevant
                del file['commitid']
                commits[commitid]['files'].append(file)

            commits[commitid]['commitid'] = commitid
            commits[commitid]['user'] = msg['msg']['user']
            commits[commitid]['message'] = msg['msg']['message']
            # which one to use, oldest? newest?
            commits[commitid]['timestamp'] = msg['timestamp']

        for commitid, commit in commits.items():
            fedmsg.publish(topic='commit', modname='cvs', active=True, name='relay_inbound', msg=commit)
