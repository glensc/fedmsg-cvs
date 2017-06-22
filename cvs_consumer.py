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

        self.cvsweb_url = self.hub.config['cvs.cvsweb_url']
        self.co_url = self.hub.config['cvs.co_url']
        self.diff_url = self.hub.config['cvs.diff_url']
        self.log_url = self.hub.config['cvs.log_url']

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
                self.updateFile(file)
                commits[commitid]['files'].append(file)

            commits[commitid]['commitid'] = commitid
            commits[commitid]['user'] = msg['msg']['user']
            commits[commitid]['message'] = msg['msg']['message']
            # which one to use, oldest? newest?
            commits[commitid]['timestamp'] = msg['timestamp']

        for commitid, commit in commits.items():
            fedmsg.publish(topic='commit', modname='cvs', active=True, name='relay_inbound', msg=commit)

    def updateFile(self, file):
        """
        update `file` object: add urls, drop commitid
        """
        file['urls'] = self.buildUrlsMessage(file)
        # commitid not relevant
        del file['commitid']

    def buildUrlsMessage(self, file):
        urls = {}

        if file['old_rev']:
            urls['old_url'] = self.buildUrl(self.co_url, file, file['old_rev'])
        if file['new_rev']:
            urls['new_url'] = self.buildUrl(self.co_url, file, file['new_rev'])

        if file['old_rev'] and file['new_rev']:
            urls['diff_url'] = self.buildUrl(self.diff_url, file)
        if file['new_rev']:
            urls['log_url'] = self.buildUrl(self.log_url, file, file['new_rev'])

        return urls

    def buildUrl(self, url, file, rev = None):
        params = {
            'url': self.cvsweb_url,
        }
        params.update(file)
        if rev:
            params['rev'] = rev
        return url % params
