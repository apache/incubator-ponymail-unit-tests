#!/usr/bin/env python3
"""
This is the archiver parser test suite.
It tests live parsings against a set of predefined reference constants.
"""
import sys
import os
import mailbox
import yaml
import argparse
import collections
import hashlib
import inspect

nonce = None
fake_args = collections.namedtuple('fakeargs', ['verbose', 'ibody'])(False, None)


def generate_specs(args):
    import archiver
    expected_archie_args = inspect.signature(archiver.Archiver).parameters
    # <= 0.11:
    if 'parseHTML' in expected_archie_args:
        archie = archiver.Archiver(parseHTML=args.html)
    else:
        archie = archiver.Archiver(parse_html=args.html)
    expected_compute_parameters = inspect.signature(archie.compute_updates).parameters
    sys.stderr.write("Generating parsing specs for file '%s'...\n" % args.mboxfile)
    items = {}
    for mboxfile in args.mboxfile:
        tests = []
        mbox = mailbox.mbox(mboxfile, None, create=False)
        for key in mbox.keys():
            message_raw = mbox.get_bytes(key)  # True raw format, as opposed to calling .as_bytes()
            message = mbox.get(key)
            lid = archiver.normalize_lid(message.get('list-id', '??'))
            # Foal parameters
            if 'raw_msg' in expected_compute_parameters:
                json, _, _, _ = archie.compute_updates(fake_args, lid, False, message, message_raw)
            # PM 0.12 parameters
            elif 'args' in expected_compute_parameters:
                json, _, _, _ = archie.compute_updates(fake_args, lid, False, message)
            # PM <= 0.11 parameters (missing args)
            else:
                # May return 2 or 4 values; only want first
                json = archie.compute_updates(lid, False, message)[0]
            body_sha3_256 = None
            if json and json.get('body') is not None:
                body_sha3_256 = hashlib.sha3_256(json['body'].encode('utf-8')).hexdigest()
            tests.append({
                'index': key,
                'message-id': message.get('message-id', '').strip(),
                'body_sha3_256': body_sha3_256,
                'attachments': json['attachments'] if json else [],
            })
        items[mboxfile] = tests
    with open(args.generate, 'w') as f:
        yaml.dump({'args': {'cmd': " ".join(sys.argv), 'parse_html': True if args.html else False}, 'parsing': items}, f)
        f.close()


def run_tests(args):
    import archiver
    errors = 0
    tests_run = 0
    yml = yaml.safe_load(open(args.load, 'r'))
    parse_html = yml.get('args', {}).get('parse_html', False)
    expected_archie_parameters = inspect.signature(archiver.Archiver).parameters
    expected_compute_parameters = inspect.signature(archiver.Archiver.compute_updates).parameters
    # <= 0.11:
    if 'parseHTML' in expected_archie_parameters:
        archie = archiver.Archiver(parseHTML=parse_html)
    else:
        archie = archiver.Archiver(parse_html=parse_html)

    for mboxfile, tests in yml['parsing'].items():
        mbox = mailbox.mbox(mboxfile, None, create=False)
        no_messages = len(mbox.keys())
        no_tests = len(tests)
        if no_messages != no_tests:
            sys.stderr.write("Warning: %s run for parsing test of %s contains %u tests, but mbox file has %u emails!\n" %
                             ('TBA', mboxfile, no_tests, no_messages))
        for test in tests:
            tests_run += 1
            message_raw = mbox.get_bytes(test['index'])  # True raw format, as opposed to calling .as_bytes()
            message = mbox.get(test['index'])
            lid = archiver.normalize_lid(message.get('list-id', '??'))
            # Foal parameters
            if 'raw_msg' in expected_compute_parameters:
                json, _, _, _ = archie.compute_updates(fake_args, lid, False, message, message_raw)
            # PM 0.12 parameters
            elif 'args' in expected_compute_parameters:
                json, _, _, _ = archie.compute_updates(fake_args, lid, False, message)
            # PM <= 0.11 parameters (missing args)
            else:
                # May return 2 or 4 values; only want first
                json = archie.compute_updates(lid, False, message)[0]
            body_sha3_256 = None
            if json and json.get('body') is not None:
                body_sha3_256 = hashlib.sha3_256(json['body'].encode('utf-8')).hexdigest()
            if body_sha3_256 != test['body_sha3_256']:
                errors += 1
                sys.stderr.write("""[FAIL] parsing index %2u: Expected: %s Got: %s\n""" %
                                 (test['index'], test['body_sha3_256'], body_sha3_256))
            att = json['attachments'] if json else []
            att_expected = test['attachments'] or []
            if att != att_expected:
                errors += 1
                sys.stderr.write("""[FAIL] attachments index %2u: Expected: %s Got: %s\n""" %
                                 (test['index'], att_expected, att))
            else:
                print("[PASS] index %u" % (test['index']))
    print("[DONE] %u tests run, %u failed." % (tests_run, errors))
    if errors:
        sys.exit(-1)


def main():
    parser = argparse.ArgumentParser(description='Command line options.')
    parser.add_argument('--generate', dest='generate', type=str,
                        help='Generate a test yaml spec, output to file specified here')
    parser.add_argument('--load', dest='load', type=str,
                        help='Load and run tests from a yaml spec file')
    parser.add_argument('--mbox', dest='mboxfile', type=str, nargs='+',
                        help='If generating spec, which mbox corpus file to use for testing')
    parser.add_argument('--rootdir', dest='rootdir', type=str, required=True,
                        help="Root directory of Apache Pony Mail")
    parser.add_argument('--html', dest='html', action='store_true',
                        help="Enable HTML parsing if generating test specs")
    args = parser.parse_args()

    if args.rootdir:
        tools_dir = os.path.join(args.rootdir, 'tools')
    else:
        tools_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', "tools")
    sys.path.append(tools_dir)

    if args.generate:
        if not args.mboxfile:
            sys.stderr.write("Generating a test spec requires an mbox filepath passed with --mbox!\n")
            sys.exit(-1)
        generate_specs(args)
    elif args.load:
        run_tests(args)


if __name__ == '__main__':
    main()
