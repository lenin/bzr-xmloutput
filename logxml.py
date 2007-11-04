# -*- encoding: utf-8 -*-

import bzrlib
from bzrlib.lazy_import import lazy_import
lazy_import(globals(), """
from bzrlib import (
    debug,
    )
""")

from bzrlib.log import LineLogFormatter, LogFormatter, LogRevision
from bzrlib.xml_serializer import _escape_cdata
import os

class XMLLogFormatter(LogFormatter):
    """ add a --xml format to 'bzr log'"""

    supports_merge_revisions = True
    supports_delta = True
    supports_tags = True
    
    def __init__(self, to_file, show_ids=False, show_timezone='original'):
        super(XMLLogFormatter, self).__init__(to_file=to_file, 
                               show_ids=show_ids, show_timezone=show_timezone)
        self.log_count = 0
        self.start_with_merge = False
        self.nested_merge_count = 0
        self.previous_merge_depth = 0
        self.debug_enabled = 'debug' in debug.debug_flags
        self.open_logs = 0
        self.open_merges = 0
        self.stack = []
        
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
        if self.debug_enabled:
            self.__debug(revision)
        actions = []
        # to handle merge revision as childs
        if revision.merge_depth > 0 and not self.start_with_merge:
            if self.previous_merge_depth < revision.merge_depth:
                if self.log_count > 0:
                    merge_depth_diference = revision.merge_depth - \
                        self.previous_merge_depth
                    for m in range(0, merge_depth_diference):
                        actions.append(self.__open_merge)
                    if merge_depth_diference > 1: 
                        self.nested_merge_count += 1
                elif self.log_count == 0:
                    # first log is inside a merge, we show it as a top level 
                    # we could support  a merge tag without parent log.
                    self.start_with_merge = True
            elif self.previous_merge_depth > revision.merge_depth:
                # TODO: testcase for more than one level of nested merges
                actions.append({self.__close_merge:self.previous_merge_depth - \
                                                   revision.merge_depth})
                if self.nested_merge_count > 0:
                    self.nested_merge_count -= 1
                else:
                    actions.append(self.__close_log)
            else:
                if self.open_logs > 0:
                    actions.append(self.__close_log)
        elif self.previous_merge_depth < revision.merge_depth:
            actions.append({self.__close_merge:self.previous_merge_depth - \
                                               revision.merge_depth})
            if self.nested_merge_count > 0:
                self.nested_merge_count -= 1
            else:
                actions.append(self.__close_log)
        elif self.open_merges > 0:
            actions.append({self.__close_merge:self.open_merges})
            #actions.append(self.__close_merge)
            actions.append(self.__close_log)
        else:
            actions.append(self.__close_log)
            if self.start_with_merge:
                # we only care about the first log, the following logs are 
                # handlend in the logic of nested merges
                self.start_with_merge = False
                
        for action in actions:
            if type(action) == dict:
                action.keys()[0](action[action.keys()[0]])
            else:
                action()
        self.__open_log()
        self.__log_revision(revision)

        self.log_count = self.log_count + 1
        self.previous_merge_depth = revision.merge_depth

    def __open_merge(self):
        self.to_file.write('<merge>')
        self.open_merges += 1
        self.stack.append('merge')

    def __close_merge(self, num=1):
        for item in self.stack.__reversed__():
      	    self.to_file.write('</%s>' % item)
            self.stack.pop()
            if item == 'merge':
                self.open_merges -= 1
                num -= 1
                if num == 0:
                    return
            if item == 'log':
                self.open_logs -= 1

    def __open_log(self):
        self.to_file.write('<log>',)
        self.open_logs = self.open_logs + 1
        self.stack.append('log')

    def __close_log(self):
        for item in self.stack.__reversed__():
       	    self.to_file.write('</%s>' % item)
            self.stack.pop()
            if item == 'log':
                self.open_logs -= 1
                return
            if item == 'merge':
                self.open_merges -= 1

    def __log_revision(self, revision):
        from bzrlib.osutils import format_date
        import StringIO
        if revision.revno is not None:
            self.to_file.write('<revno>%s</revno>' % revision.revno)
        if revision.tags:
            self.to_file.write('<tags>')
            for tag in revision.tags:
                self.to_file.write('<tag>%s</tag>' % tag)
            self.to_file.write('</tags>')
        if self.show_ids:
            self.to_file.write('<revisionid>%s</revisionid>' %  
                                revision.rev.revision_id)
            if len(revision.rev.parent_ids) > 0:
                self.to_file.write('<parents>')
            for parent_id in revision.rev.parent_ids:
                self.to_file.write('<parent>%s</parent>' % parent_id)
            if len(revision.rev.parent_ids) > 0:
                self.to_file.write('</parents>')

        self.to_file.write('<committer>%s</committer>' % \
                        _escape_cdata(revision.rev.committer))

        try:
            self.to_file.write('<branch-nick>%s</branch-nick>' % \
                _escape_cdata(revision.rev.properties['branch-nick']))
        except KeyError:
            pass
        date_str = format_date(revision.rev.timestamp,
                               revision.rev.timezone or 0,
                               self.show_timezone)
        self.to_file.write('<timestamp>%s</timestamp>' % date_str)

        self.to_file.write('<message>')
        if not revision.rev.message:
            self.to_file.write('(no message)')
        else:
            message = _escape_cdata(revision.rev.message.rstrip('\r\n'))
            self.to_file.write(os.linesep.join(message).splitlines())
        self.to_file.write('</message>')
        if revision.delta is not None:
            from statusxml import show_tree_xml
            self.to_file.write('<affected-files>')
            show_tree_xml(revision.delta, to_file, self.show_ids)
            self.to_file.write('</affected-files>')

    def begin_log(self):
        self.to_file.write('<?xml version="1.0" encoding="%s"?>' % \
                bzrlib.user_encoding)
        self.to_file.write('<logs>')

    def end_log(self):
        #if the last logged was inside a merge (and it was only one log)
        if self.open_logs > 1 and self.open_merges > 0:
            self.to_file.write('</log>')
            self.open_logs = self.open_logs - 1
        if not self.start_with_merge:
            # In case that the last log was inside a merge we need to close it
            if self.open_merges > 0:
                for merge in range(0, self.open_merges):
                    self.to_file.write('</merge>')
                    self.open_merges = self.open_merges - 1
            # to close the last opened log
            if self.open_logs > 0:
                self.to_file.write('</log>')
                self.open_logs = self.open_logs - 1
        else: 
            if self.open_logs > 0:
                self.to_file.write('</log>')
            selfogFormatter.open_logs = self.open_logs - 1
        self.to_file.write('</logs>')
        
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
        out.append('<committer>%s</committer>' % 
                   self.truncate(self.short_author(rev), 20))
        out.append('<timestamp>%s</timestamp>' % self.date_string(rev))
        ## TODO: fix hardcoded max_chars 
        out.append('<message>%s</message>' % 
                   self.truncate(rev.get_summary(), max_chars))
        out.append('</log>')
        return " ".join(out).rstrip('\n')

def line_log(rev):
    lf = XMLLineLogFormatter(None)
    return lf.log_string(None, rev)

