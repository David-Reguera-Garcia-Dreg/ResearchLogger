# !/usr/bin/env python
# -*- coding: utf-8 -*-

##############################################################################
#
# PyKeylogger: Simple Python Keylogger for Windows
# Copyright (C) 2009  nanotube@users.sf.net
#
# http://pykeylogger.sourceforge.net/
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# 2015 modifications by Roxana Lafuente <roxana.lafuente@gmail.com>
##############################################################################

from Tkinter import Label, PhotoImage, Tk
import tkSimpleDialog
import tkMessageBox
import Pmw
from configobj import ConfigObj, flatten_errors
from validate import Validator
import webbrowser
from supportscreen import SupportScreen
from supportscreen import AboutDialog
import sys
import version
import os.path
import re
from myutils import (_settings, _cmdoptions, _mainapp, password_recover,
                     get_main_dir, password_obfuscate, validate_log_filename,
                     validate_image_filename)


class PyKeyloggerControlPanel:

    def __init__(self):
        self.mainapp = _mainapp['mainapp']
        self.panelsettings = ConfigObj(_cmdoptions['cmdoptions'].configfile,
                                       configspec=_cmdoptions['cmdoptions'].configval,
                                       list_values=False)

        self.root = Pmw.initialise(fontScheme='pmw2')
        # Hides the principal window.
        self.root.withdraw()

        # Call the password authentication widget.
        # If password matches, then create the main panel.
        password_correct = self.password_dialog()
        if password_correct:
            # Shows the window that had been hidden
            self.root.deiconify()
            self.initialize_main_panel()
            # Calls the begining of our program.
            # Always begins in the principal window.
            self.root.mainloop()
        else:
            self.root.deiconify()
            self.close()

    def password_dialog(self):
        mypassword = tkSimpleDialog.askstring("Enter Password",
                                              "Password:", show="*")
        if mypassword != password_recover(self.panelsettings['General']['Master Password']):
            if mypassword is not None:
                tkMessageBox.showerror("Incorrect Password",
                                       "Incorrect Password")
            return False
        else:
            return True

    def close(self):
        self.mainapp.panel = False
        self.root.destroy()

    def callback(self):
        tkMessageBox.showwarning(title="Not Implemented",
                                 message="This feature has not yet been "
                                 "implemented")

    def initiate_timer_action(self, ln, an):  # loggername, actionname
        try:
            self.mainapp.event_threads[ln].timer_threads[an].task_function()
        except KeyError:
            # FIXME: Abort if timed screen shot trigger is called.
            pass

    def initialize_main_panel(self):
        # Creates a menu.
        self.root.title("PyKeylogger Control Panel")
        self.root.config(height=200, width=200)

        # Overrides the default exit behaviour.
        self.root.protocol("WM_DELETE_WINDOW", self.close)

        # Display the version in main window
        g = Pmw.Group(self.root, tag_pyclass=None)
        g.pack(fill='both', expand=1, padx=6, pady=6)
        textlabel = Label(g.interior(),
                          text="PyKeylogger " + str(version.version),
                          font=("Helvetica", 18))
        textlabel.pack(padx=2, pady=2, expand='yes', fill='both')

        # Pretty logo display.
        photo = PhotoImage(file=os.path.join(get_main_dir(),
                           version.name + "icon_big.gif"))
        imagelabel = Label(self.root, image=photo, height=160, width=200)
        imagelabel.photo = photo
        imagelabel.pack()

        # Create and pack the MessageBar.
        self.message_bar = Pmw.MessageBar(self.root,
                                          entry_width=50,
                                          entry_relief='groove',
                                          labelpos='w',
                                          label_text='Status:')
        self.message_bar.pack(fill='x', padx=10, pady=10)
        self.message_bar.message('state',
                                 'Please explore the menus.')

        # Create main menu.
        menu = MainMenu(self.root, self.panelsettings, self)


class MainMenu:
    def __init__(self, parent, settings, controlpanel):
        self.balloon = Pmw.Balloon(parent)
        self.menubar = Pmw.MainMenuBar(parent, balloon=self.balloon)
        parent.configure(menu=self.menubar)

        # Actions menu.
        self.menubar.addmenu('Actions', 'Actions you can take')
        sections = settings.sections
        for section in sections:
            if section == 'General':
                continue
            self.menubar.addcascademenu('Actions',
                                        section + ' Actions',
                                        'Actions for %s' % section,
                                        traverseSpec='z',
                                        tearoff=0)
            subsections = settings[section].sections
            for subsection in subsections:
                if subsection == 'General':
                    continue
                ita = controlpanel.initiate_timer_action
                self.menubar.addmenuitem(section + ' Actions', 'command',
                                         'Trigger %s' % subsection,
                                         command=Command(ita,
                                                         section,
                                                         subsection),
                                         label='Trigger %s' % subsection)

        self.menubar.addmenuitem('Actions', 'separator')
        self.menubar.addmenuitem('Actions', 'command',
                                 'Close control panel, without stopping '
                                 'keylogger',
                                 command=controlpanel.close,
                                 label='Close Control Panel')
        self.menubar.addmenuitem('Actions', 'command', 'Quit PyKeylogger',
                                 command=controlpanel.mainapp.stop,
                                 label='Quit PyKeylogger')

        # Configuration menu
        self.menubar.addmenu('Configuration', 'Configure PyKeylogger')
        sections = settings.sections
        for section in sections:
            self.menubar.addmenuitem('Configuration', 'command',
                                     section + ' settings',
                                     command=Command(ConfigPanel, parent,
                                                     section),
                                     label=section + ' Settings')

        # Help menu
        self.menubar.addmenu('Help', 'Help and documentation', name='help')
        self.menubar.addmenuitem('Help', 'command',
                                 'User manual (opens in web browser)',
                                 command=Command(webbrowser.open,
                                                 "http://pykeylogger.wiki."
                                                 "sourceforge.net/Usage_Instr"
                                                 "uctions"),
                                 label='User manual')
        self.menubar.addmenuitem('Help', 'command', 'About PyKeylogger',
                                 command=Command(AboutDialog, parent,
                                                 title="About PyKeylogger"),
                                 label='About')
        self.menubar.addmenuitem('Help', 'command',
                                 'Request for your financial support',
                                 command=Command(SupportScreen, parent,
                                                 title="Please Support PyKey"
                                                 "logger"),
                                 label='Support PyKeylogger!')

        # Configure the balloon to displays its status messages in the
        # message bar.
        hm = controlpanel.message_bar.helpmessage
        self.balloon.configure(statuscommand=hm)


class ConfigPanel():

    def __init__(self, parent, section):
        self.section = section
        self.settings = self.read_settings()
        self.changes_flag = False
        self.dialog = Pmw.Dialog(parent,
                                 buttons=('OK', 'Apply', 'Cancel'),
                                 defaultbutton = 'OK',
                                 title = section + ' Settings',
                                 command = self.execute)

        self.dialog.bind('<Escape>', self.cancel)

        self.balloon = Pmw.Balloon(self.dialog.interior(),
                                   label_wraplength=400)

        notebook = Pmw.NoteBook(self.dialog.interior())
        notebook.pack(fill='both', expand=1, padx=10, pady=10)

        self.entrydict = {section: {}}

        if section == 'General':
            subsections = ['General', ]
            subsettings = self.settings
        else:
            subsettings = self.settings[section]
            subsections = subsettings.sections
        for subsection in subsections:
            page = notebook.add(subsection)
            subsubsettings = subsettings[subsection]
            self.entrydict[section].update({subsection: {}})
            for n, v in subsubsettings.items():
                if not n.startswith('_') and \
                        not n.endswith('Tooltip'):
                    entry = Pmw.EntryField(page,
                                           labelpos='w',
                                           label_text='%s:' % n,
                                           validate=None,
                                           command=None)
                    if n.find("Password") == -1:
                        entry.setvalue(v)
                    else:
                        entry.setvalue(password_recover(v))
                    entry.pack(fill='x', expand=1, padx=10, pady=5)
                    st = subsubsettings[n + ' Tooltip'].replace('\\n', '\n')
                    self.balloon.bind(entry, st)
                    self.entrydict[section][subsection].update({n: entry})

        if len(self.entrydict.keys()) == 1 and \
                self.entrydict.keys()[0] == 'General':
            self.entrydict = self.entrydict['General']

        notebook.setnaturalsize()

    def read_settings(self):
        '''
            Get a fresh copy of the settings from file.
        '''
        settings = ConfigObj(_cmdoptions['cmdoptions'].configfile,
                             configspec=_cmdoptions['cmdoptions'].configval,
                             list_values=False)
        return settings

    def cancel(self, event):
        self.execute('Cancel')

    def execute(self, button):
        if button in ('OK', 'Apply'):
            validation_passed = self.validate()
            if validation_passed:
                self.apply()
                self.changes_flag = True
        if button not in ('Apply',):
            if self.changes_flag:
                tkMessageBox.showinfo("Restart PyKeylogger",
                                      "You must restart PyKeylogger for "
                                      "the new settings to take effect.",
                                      parent=self.dialog.interior())
                self.dialog.destroy()
            else:
                if button not in ('Apply', 'OK'):
                    self.dialog.destroy()

    def validate(self):
        for key1, value1 in self.entrydict.items():
            if not isinstance(value1, dict):  # shouldn't happen
                if key1.find('Password') == -1:
                    self.settings[key1] = value1.getvalue()
                else:
                    gv = password_obfuscate(value1.getvalue())
                    self.settings[key1] = gv
            else:
                for key2, value2 in value1.items():
                    if not isinstance(value2, dict):
                        if key2.find('Password') == -1:
                            self.settings[key1][key2] = value2.getvalue()
                        else:
                            po = password_obfuscate(value2.getvalue())
                            self.settings[key1][key2] = po
                    else:
                        for key3, value3 in value2.items():
                            if not isinstance(value3, dict):
                                if key3.find('Password') == -1:
                                    gv = value3.getvalue()
                                    self.settings[key1][key2][key3] = gv
                                else:
                                    po = password_obfuscate(value3.getvalue())
                                    self.settings[key1][key2][key3] = po
                            else:
                                pass  # shouldn't happen

        errortext = ["Some of your input contains errors. "
                     "Detailed error output below.", ]

        val = Validator()
        val.functions['log_filename_check'] = validate_log_filename
        val.functions['image_filename_check'] = validate_image_filename
        valresult = self.settings.validate(val, preserve_errors=True)
        if valresult is not True:
            for section_list, key, error in flatten_errors(self.settings,
                                                           valresult):
                if key is not None:
                    section_list.append(key)
                else:
                    section_list.append('[missing section]')
                section_string = ','.join(section_list)
                if error is False:
                    error = 'Missing value or section.'
                errortext.append('%s: %s' % (section_string, error))
            tkMessageBox.showerror("Erroneous input. Please try again.",
                                   '\n\n'.join(errortext),
                                   parent=self.dialog.interior())
            self.settings = self.read_settings()
            return False
        else:
            return True

    def apply(self):
        '''
            This is where we write out the modified config file to disk.
        '''
        self.settings.write()


class Command:
    '''
        A class we can use to avoid using the tricky "Lambda" expression.
        "Python and Tkinter Programming" by John Grayson, introduces this
        idiom.

        Thanks to http://mail.python.org/pipermail/tutor/2001-April/004787.html
        for this tip.
    '''

    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def __call__(self):
        apply(self.func, self.args, self.kwargs)


if __name__ == '__main__':
    # some simple testing code

    class BlankKeylogger:
        def stop(self):
            sys.exit()

        def __init__(self):
            pass

    class BlankOptions:
        def __init__(self):
            self.configfile = version.name + ".ini"
            self.configval = version.name + ".val"

    klobject = BlankKeylogger()
    cmdoptions = BlankOptions()
    _cmdoptions = {'cmdoptions': cmdoptions}
    _mainapp = {'mainapp': klobject}
    myapp = PyKeyloggerControlPanel()
