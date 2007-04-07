#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# @author Guillermo Gonzalez
# This code is a modified copy from bzrlib.annotate (see there for copyrights and licensing)
# @version 0.1


import sys

from bzrlib.annotate import _annotate_file
from xml.sax import saxutils

def annotate_file_xml(branch, rev_id, file_id, to_file=None, 
            show_ids=False, wt_root_path=None):
    if to_file is None:
        to_file = sys.stdout

    prevanno=''
    last_rev_id = None
    print >>to_file, '<annotation workingtree-root="%s">' % wt_root_path
    if show_ids:
        w = branch.repository.weave_store.get_weave(file_id,
            branch.repository.get_transaction())
        annotations = list(w.annotate_iter(rev_id))
        for origin, text in annotations:
            if last_rev_id != origin:
                this = origin
            else:
                this = ''
            to_file.write('<entry fid="%s">%s</entry>' % (this, text))
            last_rev_id = origin
        print >>to_file, '</annotation>'
        return

    annotation = list(_annotate_file(branch, rev_id, file_id))
    for (revno_str, author, date_str, line_rev_id, text) in annotation:
        anno = 'revno="%s" author="%s" date="%s"' % \
                    (saxutils.escape(revno_str), author, date_str)
        if anno.lstrip() == 'revno="" author="" date=""': 
            anno = prevanno
        print >>to_file, '<entry %s>%s</entry>' % (anno, saxutils.escape(text))
        prevanno = anno
    print >>to_file, '</annotation>'

