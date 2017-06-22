# FedMsg CVS Publisher

This plugin creates FedMsg messages from CVS commits,
It also includes FedMsg Consumer which emits FedMsg messages grouped by CVS
commitid.

Flow:
- cvs hook emits `net.ed.prod.cvs.file-commit` messages
- consumer gathers `net.ed.prod.cvs.file-commit` messages and emits
  `net.ed.prod.cvs.commit` messages grouped by commit-id.

## Hook Installation

Ensure `fedmsg` package is installed to CVS server.

Add to `CVSROOT/loginfo`:

```
ALL /usr/sbin/fedmsg-cvs-hook $USER %p %{sVv}
```

## Consumer Installation

```
# Copy the cvs_consumer_config.py into ./fedmsg.d/ directory.
# For production copy to /etc/fedmsg.d directory.
cp cvs_consumer_config.py fedmsg.d

# Setup your consumer by running
python setup.py develop

# Start the fedmsg-hub (which should pick up your consumer) with:
fedmsg-hub
```
