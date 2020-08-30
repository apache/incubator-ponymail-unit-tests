#!/usr/bin/env python3
"""
Simple tool for collating multiple mbox files into a single one, sorted by message ID.
Used for multi-import tests where you wish to check that multiple sources give the same ID

WARNING: emails without a Message-ID are currently dropped
"""
import mailbox
import sys

outmbox = sys.argv[1]
msgfiles = sys.argv[2:] # multiple input files allowed

allmessages = {}
noid = 0
crlf = None # assume that all emails have the same EOL
for msgfile in msgfiles:
    messages = mailbox.mbox(
        msgfile, None, create=False
    )
    for key in messages.iterkeys():
        message = messages.get(key)
        msgid = message.get('message-id')
        if msgid:
            msgid = msgid.strip()
            file = messages.get_file(key, True)
            message_raw = b''
            if crlf is None:
                message_raw = file.readline()
                crlf = (message_raw.endswith(b'\r\n'))
            message_raw += file.read()
            file.close()
            allmessages[msgid] = message_raw
        else:
            print("No message id: ", message.get_from())
            noid += 1


nw = 0
with open(outmbox, "wb") as f:
    for key in sorted(allmessages.keys()):
        f.write(allmessages[key])
        if crlf:
            f.write(b'\r\n')
        else:
            f.write(b'\n')
        nw += 1

print("Wrote %u emails to %s with CRLF %s (%u skipped)" % (nw, outmbox, crlf, noid))
