"""

Consumer to show how to write a service that does stuff in
response to message on the `fedmsg bus <http://fedmsg.rtfd.org>`_.
"""

import fedmsg
import fedmsg.consumers
from moksha.hub.reactor import reactor
from twisted.internet import task

class CVSConsumer(fedmsg.consumers.FedmsgConsumer):
    # cvs_consumer_enabled must be set to True in the config in fedmsg.d/ for
    # this consumer to be picked up and run when the fedmsg-hub starts.
    config_key = "cvs.consumer.enabled"

    # reactor delayed call id for cancelling
    callId = None

    def __init__(self, hub):
        # listen to file commits
        self.topic = self.abs_topic(hub.config, "cvs.file-commit")

        super(CVSConsumer, self).__init__(hub)

        self.cvsweb_url = hub.config['cvs.cvsweb_url']
        self.co_url = hub.config['cvs.co_url']
        self.diff_url = hub.config['cvs.diff_url']
        self.log_url = hub.config['cvs.log_url']

        # This is required.
        # It is the number of seconds that we should wait
        # until we ultimately act on a cvs file commit messages.
        self.delay = hub.config['cvs.consumer.delay']

        self.log.info("CVS: delay %ds" % self.delay)

        # We use this to manage our state
        self.queued_messages = []

        # Setup publish thread
        self.publish_queue = []

        def publishTask():
            self.log.debug("CVS: publish: %d" % len(self.publish_queue))
            for commit in self.publish_queue:
                fedmsg.publish(topic='commit', modname='cvs', active=True, name='relay_inbound', msg=commit)
            self.publish_queue = []

        self.publishTask = task.LoopingCall(publishTask)
        self.publishTask.start(self.delay)

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
        self.log.info("CVS: got a message %r" % msg['topic'])

        # first cancel to avoid race condition and losing messages.
        # this also makes delay requirement smaller for commit that itself may
        # take 5 minutes, but delay between commits is smaller.
        if self.callId:
            self.log.debug("CVS: cancel (size=%d): %r" % (len(self.queued_messages), self.callId))
            self.callId.cancel()
            self.callId = None

        def delayed_consume():
            self.log.debug("CVS: clear (size=%d): %r" % (len(self.queued_messages), self.callId))
            self.callId = None
            if self.queued_messages:
                try:
                    self.action(self.queued_messages)
                finally:
                    # Empty our list at the end of the day.
                    self.queued_messages = []
            else:
                self.log.debug("CVS: Woke up, but there were no messages.")

        self.queued_messages.append(msg)

        self.callId = reactor.callLater(self.delay, delayed_consume)
        self.log.debug("CVS: created call: %r" % self.callId)

    def action(self, messages):
        self.log.debug("CVS: action: %d" % len(messages))
        commits = {}
        for msg in messages:
            self.log.debug("msg: %r" % msg)
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

        # append to list. do not publish in this thread
        self.publish_queue.extend(commits.values())

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
