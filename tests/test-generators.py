#!/usr/bin/env python3
"""
This is the archiver ID generator test suite.
It tests live generated IDs against a set of predefined reference constants.
"""
import sys
import os
import mailbox
import yaml
import argparse
import collections

parse_html = False
nonce = None
fake_args = collections.namedtuple('fakeargs', ['verbose', 'ibody'])(False, None)


def generate_specs(args):
    import archiver
    import generators
    archie = archiver.Archiver(parse_html=parse_html)
    yml = {}
    for gen_type in generators.__GENERATORS:
        sys.stderr.write("Generating specs for type '%s'...\n" % gen_type)
        archiver.archiver_generator = gen_type
        gen_spec = []
        mbox = mailbox.mbox(args.mboxfile, None, create=False)
        for key in mbox.keys():
            message_raw = mbox.get_bytes(key)  # True raw format, as opposed to calling .as_bytes()
            message = mbox.get(key)
            lid = args.lid or archiver.normalize_lid(message.get('list-id', '??'))
            json, _, _, _ = archie.compute_updates(fake_args, lid, False, message, message_raw)
            gen_spec.append({
                'index': key,
                'message-id': message.get('message-id').strip(),
                'generated': json['mid'],
            })
        yml[gen_type] = gen_spec
    with open(args.generate, 'w') as f:
        yaml.dump({'args': {'cmd': " ".join(sys.argv)}, 'generators': {args.mboxfile: yml}}, f)
        f.close()


def run_tests(args):
    import archiver
    errors = 0
    tests_run = 0
    archie = archiver.Archiver(parse_html=parse_html)
    yml = yaml.safe_load(open(args.load, 'r'))
    for mboxfile, run in yml['generators'].items():
        for gen_type, tests in run.items():
            archiver.archiver_generator = gen_type
            mbox = mailbox.mbox(mboxfile, None, create=False)
            no_messages = len(mbox.keys())
            no_tests = len(tests)
            if no_messages != no_tests:
                sys.stderr.write("Warning: %s run for %s contains %u tests, but mbox file has %u emails!\n" %
                                 (gen_type, mboxfile, no_tests, no_messages))
            for test in tests:
                tests_run += 1
                message_raw = mbox.get_bytes(test['index'])  # True raw format, as opposed to calling .as_bytes()
                message = mbox.get(test['index'])
                lid = args.lid or archiver.normalize_lid(message.get('list-id', '??'))
                json, _, _, _ = archie.compute_updates(fake_args, lid, False, message, message_raw)
                if json['mid'] != test['generated']:
                    errors += 1
                    sys.stderr.write("""[FAIL] %s, index %u: Expected '%s', got '%s'!\n""" %
                                     (gen_type, test['index'], test['generated'], json['mid']))
                else:
                    print("[PASS] %s index %u" % (gen_type, test['index']))
    print("[DONE] %u tests run, %u failed." % (tests_run, errors))
    if errors:
        sys.exit(-1)


def main():
    parser = argparse.ArgumentParser(description='Command line options.')
    parser.add_argument('--generate', dest='generate', type=str,
                        help='Generate a test yaml spec, output to file specified here')
    parser.add_argument('--load', dest='load', type=str,
                        help='Load and run tests from a yaml spec file')
    parser.add_argument('--mbox', dest='mboxfile', type=str,
                        help='If generating spec, which mbox corpus file to use for testing')
    parser.add_argument('--listid', dest='lid', type=str,
                        help='List-ID header override if needed')
    parser.add_argument('--rootdir', dest='rootdir', type=str, required=True,
                        help="Root directory of Apache Pony Mail")
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
