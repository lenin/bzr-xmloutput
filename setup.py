#!/usr/bin/env python
# Copyright (C) 2007-2009 Guillermo Gonzalez
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

"""A Bazaar plugin that provides a option to generate XML output for
builtins commands"""

from info import *
from distutils.core import setup
from extras.bdist_nsis import bdist_nsis


if __name__ == '__main__':
    cmdclass = {
        'bdist_nsis': bdist_nsis,
    }
    setup(
        name='bzr-' + bzr_plugin_name,
        version='.'.join([str(i) for i in bzr_plugin_version]),
        maintainer='Guillermo Gonzalez',
        maintainer_email='guillo.gonzo@gmail.com',
        description="""A Bazaar plugin that provides a option to generate XML output for builtins commands""",
        license='GNU GPL',
        url='https://launchpad.net/bzr-xmloutput',
        packages=['bzrlib.plugins.xmloutput'],
        package_dir={'bzrlib.plugins.xmloutput': '.'},
        long_description="""This plugin adds an option (--xml) to log and provides an xml version of some builtinss commands that generate XML output and a xmlrpc service.""",
        cmdclass={'bdist_nsis': bdist_nsis, },
)

