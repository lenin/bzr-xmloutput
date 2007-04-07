#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# @author Guillermo Gonzalez
# This code is a modified copy from bzrlib.annotate (see there for copyrights and licensing)
# @version 0.1


import sys
import time

from bzrlib import (
    errors,
    patiencediff,
    tsort,
    )
from bzrlib.config import extract_email_address
from bzrlib.annotate import _annotate_file

def annotate_file_xml(branch, rev_id, file_id, verbose=False, full=False,
                  to_file=None, show_ids=False, wt_root_path=None):
    if to_file is None:
        to_file = sys.stdout

    prevanno=''
    last_rev_id = None
    print >>to_file, '<annotation branch_root="%s">' % wt_root_path
    if show_ids:
        w = branch.repository.weave_store.get_weave(file_id,
            branch.repository.get_transaction())
        annotations = list(w.annotate_iter(rev_id))
        #max_origin_len = max(len(origin) for origin, text in annotations)
        for origin, text in annotations:
            if full or last_rev_id != origin:
                this = origin
            else:
                this = ''
            to_file.write('<entry fid="%s">%s</entry>' % (this, text))
            last_rev_id = origin
        print >>to_file, '</annotation>'
        return

    annotation = list(_annotate_file(branch, rev_id, file_id))
    if len(annotation) == 0:
        max_origin_len = max_revno_len = max_revid_len = 0
    else:
        max_origin_len = max(len(x[1]) for x in annotation)
        max_revno_len = max(len(x[0]) for x in annotation)
        max_revid_len = max(len(x[3]) for x in annotation)

    if not verbose:
        max_revno_len = min(max_revno_len, 12)
    max_revno_len = max(max_revno_len, 3)

    for (revno_str, author, date_str, line_rev_id, text) in annotation:
        if verbose:
            anno = 'revno="%s" author="%s" date="%8s"' % (revno_str, author, date_str)
        else:
            if len(revno_str) > max_revno_len:
                revno_str = revno_str[:max_revno_len-1] + '>'
            anno = 'revno="%s" author="%s"' % (revno_str, author)

        if anno.lstrip() == "" and full: anno = prevanno
        print >>to_file, '<entry %s>%s</entry>' % (anno, text)
        prevanno=anno
    print >>to_file, '</annotation>'

