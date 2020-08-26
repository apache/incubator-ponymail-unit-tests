#!/usr/bin/env python3

import sys
import os
import subprocess
import argparse
import yaml
import time
import re

if __name__ == '__main__':
    PYTHON3 = sys.executable
    parser = argparse.ArgumentParser(description='Command line options.')
    parser.add_argument('--rootdir', dest='rootdir', type=str, required=True,
                        help="Root directory of Apache Pony Mail")
    parser.add_argument('--load', dest='load', type=str, nargs='+',
                        help="Load only specific yaml spec files instead of all test specs")
    parser.add_argument('--nomboxo', dest = 'nomboxo', action='store_true',
                        help = 'Skip Mboxo processing')
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
    sub_success = 0
    sub_failure = 0
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
                    if args.nomboxo:
                        rv = subprocess.check_output((PYTHON3, 'tests/test-%s.py' % test_type, '--rootdir', args.rootdir, '--load', spec_file, '--nomboxo'))
                    else:
                        rv = subprocess.check_output((PYTHON3, 'tests/test-%s.py' % test_type, '--rootdir', args.rootdir, '--load', spec_file))
                    tests_success += 1
                except subprocess.CalledProcessError as e:
                    rv = e.output
                    print("%s test from %s failed with code %d" % (test_type, spec_file, e.returncode))
                    tests_failure += 1
                    if args.failonfail:
                        failbreak = True
                        break
                finally:
                    # Fetch successes and failures from this spec run, add to total
                    m = re.search(r"^\[DONE\] (\d+) tests run, (\d+) failed.", rv.decode('ascii'), re.MULTILINE)
                    if m:
                        sub_success += int(m.group(1)) - int(m.group(2))
                        sub_failure += int(m.group(2))
        if failbreak:
            break

    print("-------------------------------------")
    print("Done with %u specification%s in %.2f seconds" % (tests_total, 's' if tests_total != 1 else '', time.time() - now))
    print("Specs processed: %4u" % tests_total)
    print("Total tests run: %4u" % (sub_success+sub_failure))
    print("Tests succeeded: %4u" % sub_success)
    print("Tests failed:    %4u" % sub_failure)
    print("-------------------------------------")
    if tests_failure:
        sys.exit(-1)
