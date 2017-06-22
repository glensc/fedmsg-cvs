#!/usr/bin/python
# coding: utf-8
# Requires:
# - fedmsg
#
# Setup:
# Put to CVSROOT/loginfo:
# ALL $CVSROOT/CVSROOT/fedmsg-cvs-hook $USER %p %{sVv}

import sys
import re
import os
from subprocess import check_output
from itertools import izip
import fedmsg

class FedmsgCvsHook():
    def __init__(self, argv, stdin):
        self.user, self.module = argv[1:3]
        self.files = argv[3:]
        self.commit_msg = self.get_commit_message(stdin)
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
        files = []
        for filename, oldrev, newrev in self.grouped(self.files, 3):
            if filename in ['- New directory']:
                continue
            file = self.buildFileMessage(self.module, filename, oldrev, newrev)
            files.append(file)

        return files

    def buildFileMessage(self, module, filename, oldrev, newrev):
        file = {}
        file['filename'] = os.path.join(module, filename)
        file['old_rev'] = oldrev if oldrev != 'NONE' else None
        file['new_rev'] = newrev if newrev != 'NONE' else None
        file['commitid'] = self.get_commit_id(filename)
        return file

    def get_commit_id(self, filename):
        # skip when mocking
        if not os.path.exists('CVS/Entries'):
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
