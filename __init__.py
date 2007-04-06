#!/usr/bin/env python2.4


from bzrlib.commands import display_command, Command, register_command
from bzrlib.builtins import tree_files

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
    encoding_type = 'replace'
    
    @display_command
    def run(self, show_ids=False, file_list=None, revision=None, short=False, versioned=False):
        from xmlhelper import show_tree_status_xml
        
        tree, file_list = tree_files(file_list)
        
        show_tree_status_xml(tree, show_ids=show_ids,
                specific_files=file_list, revision=revision,
                to_file=self.outf, versioned=versioned)
        
register_command(cmd_statusxml)
