#!/usr/bin/python
# coding: utf-8
# Requires:
# - fedmsg
#
# Setup:
# Put to CVSROOT/loginfo:
# ALL $CVSROOT/CVSROOT/fedmsg-cvs-hook /path/to/config.conf $USER %p %{sVv}

import sys
import re
import os
from subprocess import check_output
from itertools import izip
import fedmsg

class FedmsgCvsHook():
    def __init__(self, argv, stdin):
        self.user, self.module = argv[2:4]
        self.files = argv[4:]
        self.commit_msg = self.get_commit_message(stdin)
        self.config = self.parse_config(argv[1])
        self.commitid_pattern = re.compile('Commit Identifier:\s+(?P<commitid>\S+)')

    def buildMessage(self):
        msg = {
            'user': self.user,
            'module': self.module,
            'message' : self.commit_msg,
            'files': self.buildFilesMessage(),
        }
        # grab commit id from all files
        msg['commitid'] = self.getCommitId(msg['files'])

        return msg

    def getCommitId(self, files):
        commitids = [file['commitid'] for file in files]
        # make unique
        commitids = list(set(commitids))

        # return as string with single item
        if len(commitids) == 1:
            return commitids[0]

        # this should not happen!
        # but either way, return None or list
        return commitids

    def buildFilesMessage(self):
        c = self.config
        defopts = { 'url': c['CVSWEB_URL'], 'module': self.module }
        files = []
        for filename, oldrev, newrev in self.grouped(self.files, 3):
            if filename in ['- New directory']:
                continue
            file = self.buildFileMessage(defopts, filename, oldrev, newrev)
            files.append(file)

        return files

    def buildFileMessage(self, defopts, filename, oldrev, newrev):
        file = {}
        file['filename'] = filename
        file['old_rev'] = oldrev if oldrev != 'NONE' else None
        file['new_rev'] = newrev if newrev != 'NONE' else None
        file['commitid'] = self.get_commit_id(filename)
        file['urls'] = self.buildUrlsMessage(defopts, file)
        return file

    def buildUrlsMessage(self, defopts, file):
        opts = defopts.copy()
        opts.update(file)
        urls = {}

        if opts['old_rev']:
            urls['old_url'] = self.buildUrl('CO_URL', opts, opts['old_rev'])
        if opts['new_rev']:
            urls['new_url'] = self.buildUrl('CO_URL', opts, opts['new_rev'])

        if opts['old_rev'] and opts['new_rev']:
            urls['diff_url'] = self.buildUrl('DIFF_URL', opts)
        if opts['new_rev']:
            urls['log_url'] = self.buildUrl('LOG_URL', opts, opts['new_rev'])

        return urls

    def buildUrl(self, url, opts, rev = None):
        if rev:
            opts['rev'] = rev
        return self.config[url] % opts

    def get_commit_id(self, filename):
        if not os.path.exists(filename):
            return None

        command = 'cvs -Qn status '.split()
        command.append(filename)

        out = check_output(command)
        m = self.commitid_pattern.findall(out)
        if len(m):
            return m[0]
        return None

    def get_commit_message(self, stdin):
        """
        Commit message is multiline with preformatted by CVS client.
        Read up STDIN up to: 'Log Message:\n',

        Example:
        ['Update of /usr/local/cvs/test/slack\n',
         'In directory localhost:/home/glen/scm/cvs/test-CVSROOT/testdir/slack\n',
         '\n',
         'Modified Files:\n',
         '\tslack.txt slack2.txt \n',
         'Log Message:\n',
         '- slack\n',
         '\n']
        """
        lines = stdin.readlines()

        for i in range(len(lines)):
            if lines[i] == "Log Message:\n":
                break

        return ''.join(lines[i + 1:]).strip()

    def parse_config(self, filename):
        """Parse configuration file.

        Args:
          filename: Path to the configuration file to parse.
        Returns:
          Dictionary of values defined in the file.
        """
        with open(filename) as f:
            data = f.read()
            compiled = compile(data, filename, "exec")
            result = { 'main': sys.modules[__name__] }
            eval(compiled, result)
            return result

    # http://stackoverflow.com/a/5389547
    def grouped(self, iterable, n):
        "s -> (s0,s1,s2,...sn-1), (sn,sn+1,sn+2,...s2n-1), (s2n,s2n+1,s2n+2,...s3n-1), ..."
        return izip(*[iter(iterable)]*n)

if len(sys.argv) > 3:
    hook = FedmsgCvsHook(sys.argv, sys.stdin)
    msg = hook.buildMessage()

    # until this is in place, add name="relay_inbound": http://paste.fedoraproject.org/155599/74653371/
    # https://github.com/fedora-infra/fedmsg/issues/426
    fedmsg.publish(topic='file-commit', modname='cvs', active=True, name='relay_inbound', msg=msg)
