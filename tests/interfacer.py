#!/usr/bin/env python3

"""
This is a wrapper to standardise the API for different versions
"""

import sys
import inspect

class Archiver(object):
    def __init__(self, archiver_, args):
        self.expected_archie_parameters = inspect.signature(archiver_.Archiver).parameters
        self.expected_compute_parameters = inspect.signature(archiver_.Archiver.compute_updates).parameters

        # <= 0.11:
        if 'parseHTML' in self.expected_archie_parameters:
            if hasattr(args, 'generator'):
              archiver_.archiver_generator = args.generator
            self.archie = archiver_.Archiver(parseHTML=args.parse_html)
        # prepare for updated archiver
        elif 'ignore_body' in self.expected_archie_parameters:
            self.archie = archiver_.Archiver(generator=getattr(args, 'generator', None),
                                             parse_html=args.parse_html,
                                             ignore_body=None) # To be provided later
        else: # 0.12+
            if hasattr(args, 'generator'):
                self.archie = archiver_.Archiver(generator=args.generator, parse_html=args.parse_html)
            else:
                self.archie = archiver_.Archiver(parse_html=args.parse_html)

        if 'raw_msg' in self.expected_compute_parameters:
          self.compute = self._compute_foal
        # PM 0.12 parameters
        elif 'args' in self.expected_compute_parameters:
            self.compute = self._compute_12
        # PM <= 0.11 parameters (missing args)
        else:
            self.compute = self._compute_11

    def _compute_foal(self, fake_args, lid, private, message, message_raw):
        if 'args' in self.expected_compute_parameters: # temporary until foal updated
            return self.archie.compute_updates(fake_args, lid, private, message, message_raw)[0]
        else:
            return self.archie.compute_updates(lid, private, message, message_raw)[0]

    def _compute_12(self, fake_args, lid, private, message, message_raw):
        return self.archie.compute_updates(fake_args, lid, private, message)[0]

    def _compute_11(self, fake_args, lid, private, message, message_raw):
        return self.archie.compute_updates(lid, private, message)[0]

    def compute_updates(self, fake_args, lid, private, message, message_raw):
        return self.compute(fake_args, lid, private, message, message_raw)
