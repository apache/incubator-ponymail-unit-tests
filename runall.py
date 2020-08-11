#!/usr/bin/env python3

import sys
import os
import subprocess
import argparse
import yaml
import time

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Command line options.')
    parser.add_argument('--rootdir', dest='rootdir', type=str, required=True,
                        help="Root directory of Apache Pony Mail")
    parser.add_argument('--load', dest='load', type=str, nargs='+',
                        help="Load only specific yaml spec files instead of all test specs")
    parser.add_argument('--fof', dest='failonfail', action='store_true',
                        help="Stop running more tests if an error is encountered")
    args = parser.parse_args()

    if args.load:
        spec_files = args.load
    else:
        spec_files = [os.path.join('yaml', x) for x in os.listdir('yaml') if x.endswith('.yaml')]

    tests_success = 0
    tests_failure = 0
    tests_total = 0
    now = time.time()

    failbreak = False
    for spec_file in spec_files:
        with open(spec_file, 'r') as f:
            yml = yaml.safe_load(f)
            for test_type in yml:
                if test_type == 'args':
                    continue
                tests_total += 1
                print("Running '%s' tests from %s..." % (test_type, spec_file))
                try:
                    subprocess.check_call(('/usr/bin/python3', 'tests/test-%s.py' % test_type, '--rootdir', args.rootdir, '--load', spec_file))
                    tests_success += 1
                except subprocess.CalledProcessError as e:
                    print("%s test from %s failed with code %d" % (test_type, spec_file, e.returncode))
                    tests_failure += 1
                    if args.failonfail:
                        failbreak = True
                        break
        if failbreak:
            break

    print("-------------------------------------")
    print("Done with %u tests in %.2f seconds" % (tests_total, time.time() - now))
    print("%u Were GOOD, %u were BAD" % (tests_success, tests_failure))
    print("-------------------------------------")
    if tests_failure:
        sys.exit(-1)
