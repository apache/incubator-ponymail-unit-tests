#!/usr/bin/env python3
"""
Simple tool for collating multiple mbox files into a single one, sorted by message ID.
Used for multi-import tests where you wish to check that multiple sources give the same ID

WARNING: emails without a Message-ID are currently silently dropped
The code also assumes that mboxes have CRLF line-endings
"""
import mailbox
import sys

outmbox = sys.argv[1]
msgfiles = sys.argv[2:]

allmessages = {}
for msgfile in msgfiles:
    messages = mailbox.mbox(
        msgfile, None, create=False
    )
    for key in messages.iterkeys():
        message = messages.get(key)
        message_raw = messages.get_bytes(key)
        msgid = message.get('message-id')
        if msgid:
            msgid = msgid.strip()
            allmessages[msgid] = message_raw


nw = 0
with open(outmbox, "wb") as f:
    for key in sorted(allmessages.keys()):
        f.write(b"From TEST@TEST\r\n")
        f.write(allmessages[key])
        f.write(b"\r\n")
        nw += 1

print("Wrote %u emails to %s" % (nw, outmbox))
