#!/bin/bash

### We use SSH XForwarding.
## Open the following lines in the remote host SSHD config in /etc/ssh/sshd_config:
# X11Forwarding yes
# X11DisplayOffset 10
# X11UseLocalhost yes
# PermitTTY yes
# PrintMotd no
# PrintLastLog yes
# TCPKeepAlive yes

# Must ssh -x pi@<my-ip-addr> if intending to run me from the remote host
export DISPLAY=localhost:10.0
python3 ./bird-watcher.py
