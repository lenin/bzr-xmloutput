# -*- encoding: utf-8 -*-

from bzrlib.log import LineLogFormatter, LogFormatter, LogRevision
from bzrlib.xml_serializer import _escape_cdata
import os

class XMLLogFormatter(LogFormatter):
    """ add a --xml format to 'bzr log'"""

    supports_merge_revisions = True
    supports_delta = True
    supports_tags = True
    log_count = 0
    last_log_was_merge = False

    def __init__(self, to_file, show_ids=False, show_timezone='original'):
        super(XMLLogFormatter, self).__init__(to_file=to_file, 
                               show_ids=show_ids, show_timezone=show_timezone)
        self.is_merge = False
        self.is_first = True
        self.first_log_is_merged = False
        XMLLogFormatter.last_log_was_merge = False
        log_count = 0
        self.previous_merge_depth = 0
        
    def show(self, revno, rev, delta, tags=None):
        lr = LogRevision(rev, revno, 0, delta, tags)
        return self.log_revision(lr)

    def show_merge_revno(self, rev, merge_depth, revno):
        """a call to self._show_helper, XML don't care about formatting """
        lr = LogRevision(rev, merge_depth=merge_depth, revno=revno)
        return self.log_revision(lr)

    def log_revision(self, revision):
        """Log a revision, either merged or not."""
        from bzrlib.osutils import format_date
        to_file = self.to_file
        # to handle merge revision as childs
        if revision.merge_depth > 0:
            if not self.is_merge:
                ## to handle a first log with merge_depth > 0
                if not self.is_first and not self.first_log_is_merged :
                    print >>to_file,  '<merge>',
                else: 
                    self.first_log_is_merged = True
                self.is_merge = True
            else:
                if self.previous_merge_depth < revision.merge_depth:
                    print >>to_file,  '<merge>',
                elif self.previous_merge_depth > revision.merge_depth:
                    print >>to_file,  '</merge>',
            print >>to_file,  '<log>',
            self.__log_revision(revision)
            print >>to_file,  '</log>',
            XMLLogFormatter.last_log_was_merge = True
        else:
            if self.first_log_is_merged:
                self.first_log_is_merged = False
                self.is_merge = False
            else:
                if self.is_merge or XMLLogFormatter.last_log_was_merge:
                    print >>to_file,  '</merge>',
                    self.is_merge = False
                if not self.is_first:
                    print >>to_file,  '</log>',
            print >>to_file,  '<log>',
            self.__log_revision(revision)
            XMLLogFormatter.last_log_was_merge = False
        if self.is_first:
            self.is_first = False
        XMLLogFormatter.log_count = XMLLogFormatter.log_count + 1
        self.previous_merge_depth = revision.merge_depth

    def __log_revision(self, revision):
        from bzrlib.osutils import format_date
        import StringIO
        to_file = self.to_file
        if revision.revno is not None:
            print >>to_file,  '<revno>%s</revno>' % revision.revno,
        if revision.tags:
            print >>to_file,  '<tags>'
            for tag in revision.tags:
                print >>to_file, '<tag>%s</tag>' % tag
            print >>to_file,  '</tags>'
        if self.show_ids:
            print >>to_file,  '<revisionid>%s</revisionid>' % revision.rev.revision_id,
            if len(revision.rev.parent_ids) > 0:
                print >>to_file, '<parents>',
            for parent_id in revision.rev.parent_ids:
                print >>to_file, '<parent>%s</parent>' % parent_id,
            if len(revision.rev.parent_ids) > 0:
                print >>to_file, '</parents>',

        print >>to_file,  '<committer>%s</committer>' % \
                        _escape_cdata(revision.rev.committer),

        try:
            print >>to_file, '<branch-nick>%s</branch-nick>' % \
                _escape_cdata(revision.rev.properties['branch-nick']),
        except KeyError:
            pass
        date_str = format_date(revision.rev.timestamp,
                               revision.rev.timezone or 0,
                               self.show_timezone)
        print >>to_file,  '<timestamp>%s</timestamp>' % date_str,

        print >>to_file,  '<message>',
        if not revision.rev.message:
            print >>to_file, '(no message)'
        else:
            message = revision.rev.message.rstrip('\r\n')
            print >>to_file, os.linesep.join(_escape_cdata(message).splitlines()),
        print >>to_file,  '</message>',
        if revision.delta is not None:
            from statusxml import show_tree_xml
            print >>to_file,  '<affected-files>',
            show_tree_xml(revision.delta, to_file, self.show_ids)
            print >>to_file,  '</affected-files>',


class XMLLineLogFormatter(LineLogFormatter):

    def __init__(self, *args, **kwargs):
        from bzrlib.osutils import terminal_width
        super(XMLLineLogFormatter, self).__init__(*args, **kwargs)
        self._max_chars = terminal_width() - 1

    def log_string(self, revno, rev, max_chars=50):
        """Format log info into one string. Truncate tail of string
        :param  revno:      revision number (int) or None.
                            Revision numbers counts from 1.
        :param  rev:        revision info object
        :return:            formatted truncated string
        """
        out = []
        out.append('<log>')
        if revno:
            # show revno only when is not None
            out.append("<revno>%s</revno>" % revno)
        out.append('<committer>%s</committer>' % self.truncate(self.short_author(rev), 20))
        out.append('<timestamp>%s</timestamp>' % self.date_string(rev))
        ## TODO: fix hardcoded max_chars 
        out.append('<message>%s</message>' % self.truncate(rev.get_summary(), max_chars))
        out.append('</log>')
        return " ".join(out).rstrip('\n')


def line_log(rev):
    lf = XMLLineLogFormatter(None)
    return lf.log_string(None, rev)


