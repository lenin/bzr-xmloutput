#!/usr/bin/env python2.4

# @author Guillermo Gonzalez
# @version 0.1
"""
This plugin provides xml output for two commands:
 * add a --xml option to 'bzr log'
 * and sprovide a 'bzr statusxml' command

(most of this is code was modified from bzrlib.cmd_status, 
bzrlib.status, bzrlib.delta.TreeDelta.show and bzrlib.log.LongLogFormatter)
"""
from bzrlib.commands import display_command, Command, register_command
from bzrlib.builtins import tree_files
from bzrlib.log import log_formatter, show_log, LogFormatter, log_formatter_registry

# Try to override default command but fail :(
#class cmd_status(builtins.cmd_status):
class cmd_statusxml(Command):

    """Display status summary (in XML).

    Almost equal to 'bzr status', except the --short option and the output 
    is in xml format.
    This reports on versioned and unknown files, reporting them
    grouped by state.  Possible states are:

    <added/>
        Versioned in the working copy but not in the previous revision.

    <removed/>
        Versioned in the previous revision but removed or deleted
        in the working copy.

    <renamed/>
        Path of this file changed from the previous revision;
        the text may also have changed.  This includes files whose
        parent directory was renamed.

    <modified/>
        Text has changed since the previous revision.

    <kind changed/>
        File kind has been changed (e.g. from file to directory).

    <unknown/>
        Not versioned and not matching an ignore pattern.

    Each group can have multiple child's of this element's:

    <file [oldpath] [oldkind, newkind] [fid]>
    <directory [oldpath] [oldkind, newkind] [suffix]>


    as a simple example: 
    <status workingtree_root="/home/guillo/Unison-root/sandbox/bazaar/bzr/0.15/">
        <renamed>
            <file oldpath="INSTALL"  >INSTALL.txt</file>
        </renamed>
        <kind changed>
            <directory oldkind="file" newkind="directory">NEWS</directory>
        </kind changed>
        <modified>
            <file>bzrlib/symbol_versioning.py</file>
        </modified>
        <unknown>
            <file>.project</file>
            <directory>bzrlib/dir/</directory>
        </unknown>
    </status>


    To see ignored files use 'bzr ignored'.  For details in the
    changes to file texts, use 'bzr diff'.
    

    If no arguments are specified, the status of the entire working
    directory is shown.  Otherwise, only the status of the specified
    files or directories is reported.  If a directory is given, status
    is reported for everything inside that directory.

    If a revision argument is given, the status is calculated against
    that revision, or between two revisions if two are provided.
    """
    takes_args = ['file*']
    takes_options = ['show-ids', 'revision']
    #takes_options.append('xml')
    encoding_type = 'replace'
    
    @display_command
    def run(self, show_ids=False, file_list=None, revision=None):
        from xmlhelper import show_tree_status_xml
        tree, file_list = tree_files(file_list)
        show_tree_status_xml(tree, show_ids=show_ids,
                specific_files=file_list, revision=revision,
                to_file=self.outf, versioned=False)

# Try to override default command but fail :(
#    def run(self, show_ids=False, file_list=None, revision=None, short=False, 
#               versioned=False, xml=False):
#        if xml:
#            from xmlhelper import show_tree_status_xml
#            tree, file_list = tree_files(file_list)
#            show_tree_status_xml(tree, show_ids=show_ids,
#                    specific_files=file_list, revision=revision,
#                    to_file=self.outf, versioned=versioned)
#        else:
#            cmd_status.run(show_ids=show_ids, file_list=file_list, 
#                            revision=revision, short=short, versioned=False)
        
register_command(cmd_statusxml)
#register_command(cmd_status, decorate=True)


""" add a --xml format to 'bzr log'"""
class XMLLogFormatter(LogFormatter):

    def __init__(self, to_file, show_ids=False, show_timezone='original'):
        super(XMLLogFormatter, self).__init__(to_file=to_file, 
                               show_ids=show_ids, show_timezone=show_timezone)

    def show(self, revno, rev, delta):
        return self._show_helper(revno=revno, rev=rev, delta=delta)

    def show_merge_revno(self, rev, merge_depth, revno):
        """a call to self._show_helper, XML don't care about formatting """
        return self._show_helper(revno=revno, rev=rev, merged=True, delta=None)

    def _show_helper(self, rev=None, revno=None, indent='', 
                    merged=False, delta=None):
        """Show a revision, either merged or not."""
        from xml.sax import saxutils
        from bzrlib.osutils import format_date
        to_file = self.to_file
        print >>to_file,  '<log>',
        if revno is not None:
            print >>to_file,  '<revno>%s</revno>' % revno,
        if merged:
            print >>to_file,  '<merged>%s</merged>' % rev.revision_id,
        elif self.show_ids:
            print >>to_file,  '<revision-id>%s</revision_id>' % rev.revision_id,
        if self.show_ids:
            if len(rev.parent_ids) > 0:
                print >>to_file, '<parents>',
            for parent_id in rev.parent_ids:
                print >>to_file, '<parent>%s</parent>' % parent_id,
            if len(rev.parent_ids) > 0:
                print >>to_file, '</parents>',
        print >>to_file,  '<committer>%s</committer>' % \
                        saxutils.escape(rev.committer),
        try:
            print >>to_file, '<branch-nick>%s</branch-nick>' % \
                saxutils.escape(rev.properties['branch-nick']),
        except KeyError:
            pass
        date_str = format_date(rev.timestamp,
                               rev.timezone or 0,
                               self.show_timezone)
        print >>to_file,  '<timestamp>%s<timestamp>' % date_str,

        print >>to_file,  '<message>',
        if not rev.message:
            print >>to_file,  '  (no message)',
        else:
            print >>to_file,  saxutils.escape(rev.message),
        print >>to_file,  '</message>',
        if delta is not None:
            from xmlhelper import show_tree_xml
            #delta.show(to_file, self.show_ids)
            show_tree_xml(delta, to_file, self.show_ids)
        print >>to_file,  '</log>',



log_formatter_registry.register('xml', XMLLogFormatter,
                              'Detailed (not well formed) XML log format')
