#!/usr/bin/python
# coding: utf-8
# Requires:
# - fedmsg
#
# Setup:
# Put to CVSROOT/loginfo:
# ALL $CVSROOT/CVSROOT/fedmsg-cvs-hook /path/to/config.conf $USER %p %{sVv}

import sys
import subprocess
from itertools import izip
import fedmsg

def parse_config(filename):
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
def grouped(iterable, n):
    "s -> (s0,s1,s2,...sn-1), (sn,sn+1,sn+2,...s2n-1), (s2n,s2n+1,s2n+2,...s3n-1), ..."
    return izip(*[iter(iterable)]*n)

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
def get_commit_message():
    lines = sys.stdin.readlines()

    for i in range(len(lines)):
        if lines[i] == "Log Message:\n":
            break

    return lines[i + 1:]

def get_commit_summary():
    lines = get_commit_message()
    return lines[0].strip()

def cut(s, maxlen = 24):
    if len(s) > maxlen:
        return s[0:maxlen] + "..."
    return s

user, module = sys.argv[2:4]
files = sys.argv[4:]
commit_msg = get_commit_summary()
c = parse_config(sys.argv[1])

module_url = "%s/%s/" % (c['CVSWEB_URL'], module)
summary = "in *<%s|%s>* by *%s*: %s" % (module_url, module, user, commit_msg)

msg = {
    'user': user,
    'module': module,
    'message' : commit_msg,
    'files': [],
}

defopts = { 'url': c['CVSWEB_URL'], 'module': module }
for filename, oldrev, newrev in grouped(files, 3):
    opts = defopts.copy()
    opts['file'] = filename

    opts['rev'] = newrev
    opts['log_url'] = c['LOG_URL'] % opts

    opts['rev'] = oldrev
    opts['old_url'] = c['CO_URL'] % opts

    opts['rev'] = newrev
    opts['new_url'] = c['CO_URL'] % opts
    # temporary for formatting
    del opts['rev']

    opts['old_rev'] = oldrev
    opts['new_rev'] = newrev
    opts['diff_url'] = c['DIFF_URL'] % opts

    msg['files'].append(opts)

# until this is in place, add name="relay_inbound": http://paste.fedoraproject.org/155599/74653371/
# https://github.com/fedora-infra/fedmsg/issues/426

fedmsg.publish(topic='commit', modname='cvs', active=True, name='relay_inbound', msg=msg)
