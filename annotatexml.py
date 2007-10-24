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

"""This code is a modified copy from bzrlib.annotate (see there for copyrights and licensing)"""

import sys

from bzrlib.annotate import _annotate_file
from bzrlib.xml_serializer import _escape_cdata

def annotate_file_xml(branch, rev_id, file_id, to_file=None, 
            show_ids=False, wt_root_path=None, file_path=None):
    if to_file is None:
        to_file = sys.stdout

    prevanno=''
    last_rev_id = None
    print >>to_file, '<?xml version="1.0"?>'
    print >>to_file, '<annotation workingtree-root="%s" %s>' % (wt_root_path, 'file="'+file_path+'"')
    if show_ids:
        w = branch.repository.weave_store.get_weave(file_id,
            branch.repository.get_transaction())
        annotations = list(w.annotate_iter(rev_id))
        for origin, text in annotations:
            if last_rev_id != origin:
                this = origin
            else:
                this = ''
            to_file.write('<entry fid="%s">%s</entry>' % (_escape_cdata(this), _escape_cdata(text)))
            last_rev_id = origin
        print >>to_file, '</annotation>'
        return

    annotation = list(_annotate_file(branch, rev_id, file_id))
    for (revno_str, author, date_str, line_rev_id, text) in annotation:
        anno = 'revno="%s" author="%s" date="%s"' % \
                    (_escape_cdata(revno_str), _escape_cdata(author), date_str)
        if anno.lstrip() == 'revno="" author="" date=""': 
            anno = prevanno
        print >>to_file, '<entry %s>%s</entry>' % (anno, _escape_cdata(text))
        prevanno = anno
    print >>to_file, '</annotation>'

