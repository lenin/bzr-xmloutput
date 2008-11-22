#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Copyright (C) 2007 Guillermo Gonzalez
#
# The code taken from bzrlib is under: Copyright (C) 2005, 2006, 2007 Canonical Ltd
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA
#
# Contributors:
#               Martin Albisetti

"""
This code is a modified copy from bzrlib.annotate
(see there for copyrights and licensing)
"""

import sys

_annotate_file = None
try:
    from bzrlib.annotate import _expand_annotations
except ImportError:
    # to support bzr < 1.8
    from bzrlib.annotate import _annotate_file


from bzrlib.annotate import _annotations
from bzrlib.xml_serializer import _escape_cdata
from bzrlib import user_encoding
from bzrlib import osutils

empty_annotation = 'revno="" author="" date=""'

def annotate_file_xml(branch, rev_id, file_id, to_file=None,
            show_ids=False, wt_root_path=None, file_path=None, full=False):
    if to_file is None:
        to_file = sys.stdout

    encoding = getattr(to_file, 'encoding', None) or \
            osutils.get_terminal_encoding()
    prevanno=''
    last_rev_id = None
    to_file.write('<?xml version="1.0"?>')
    to_file.write(('<annotation workingtree-root="%s" %s>' % \
                  (wt_root_path.encode(encoding),
                  'file="%s"' % file_path)).encode(encoding, 'replace'))

    annotations = _annotations(branch.repository, file_id, rev_id)
    if _annotate_file:
        annotation = list(_annotate_file(branch, rev_id, file_id))
    else:
        annotation = list(_expand_annotations(annotations, branch))

    for (revno_str, author, date_str, line_rev_id,
        text, origin) in _annotation_iter(annotation, annotations):
        if not show_ids:
            origin = None
        prevanno = _show_entry(to_file, prevanno, revno_str, author,
            date_str, line_rev_id, text, origin)
    to_file.write('</annotation>')


def _annotation_iter(annotation, annotations):
    for ((revno_str, author, date_str, line_rev_id, text), \
            (origin, text_dup)) in zip(annotation, annotations):
        yield (revno_str, author, date_str, line_rev_id, text, origin)


def _show_entry(to_file, prevanno, revno_str, author,
                date_str, line_rev_id, text, fid):
    anno = 'revno="%s" author="%s" date="%s"' % \
                (_escape_cdata(revno_str), _escape_cdata(author), date_str)
    if anno.lstrip() == empty_annotation:
        anno = prevanno
    if fid:
        to_file.write('<entry %s fid="%s">%s</entry>' % \
                    (anno, fid, _escape_cdata(text)))
    else:
        to_file.write('<entry %s>' % anno)
        to_file.write('%s</entry>' % _escape_cdata(text))
    return anno
