# FedMsg CVS Publisher

## Installation

Ensure `fedmsg` package is installed to CVS server.

Configure and add `CVSROOT/fedmsg-cvs-hook.conf`

Add to `checkoutlist`
```
fedmsg-cvs-hook.conf
```

Add to `CVSROOT/loginfo`:

```
ALL /usr/bin/fedmsg-cvs-hook $CVSROOT/CVSROOT/fedmsg-cvs-hook.conf $USER %p %{sVv}
```

Commit all related files:
- `CVSROOT/fedmsg-cvs-hook.conf`
- `CVSROOT/checkoutlist`
- `CVSROOT/loginfo`