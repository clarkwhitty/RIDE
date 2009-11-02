#  Copyright 2008-2009 Nokia Siemens Networks Oyj
#  
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#  
#      http://www.apache.org/licenses/LICENSE-2.0
#  
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import wx
from wx.lib.scrolledpanel import ScrolledPanel

from robotide.context import SETTINGS


class PluginManager(object):
    _title = 'Manage Plugins'

    def __init__(self, notebook):
        self._notebook = notebook
        self._panel = None
        self.settings = SETTINGS.add_section('plugins')

    def show(self, plugins):
        if not self._panel:
            self._panel = PluginPanel(self._notebook)
        if not self._is_visible():
            self._add_to_notebook()
        self._panel.display(plugins)

    def _is_visible(self):
        for index in range(self._notebook.GetPageCount()):
            if self._notebook.GetPageText(index) == self._title:
                return True
        return False

    def _add_to_notebook(self):
        self._notebook.AddPage(self._panel, self._title)
        self._notebook.SetSelection(self._notebook.GetPageIndex(self._panel))

    def _save_settings(self):
        """Saves the state of the plugins to the settings file"""
        for plugin in self._app._plugins.plugins:
            self.settings[plugin.name] = plugin.active
        self.settings.save()


class PluginPanel(wx.Panel):

    def __init__(self, notebook):
        wx.Panel.__init__(self, notebook)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self._create_header(), 0, wx.LEFT|wx.RIGHT|wx.TOP, border=16)
        sizer.Add(self._create_line(), 0, wx.EXPAND|wx.LEFT|wx.RIGHT, border=16)
        self.plugin_panel = self._create_body()
        sizer.Add(self.plugin_panel, 1, wx.EXPAND|wx.ALL, border=16)
        self.SetSizer(sizer)

    def _create_header(self):
        header_panel = wx.Panel(self, wx.ID_ANY)
        header = wx.StaticText(header_panel, wx.ID_ANY, "Installed Plugins")
        header.SetFont(wx.Font(14, wx.SWISS, wx.NORMAL, wx.BOLD))
        return header

    def _create_line(self):
        return wx.StaticLine(self)

    def _create_body(self):
        panel = ScrolledPanel(self, wx.ID_ANY, style=wx.TAB_TRAVERSAL)
        panel.SetupScrolling()
        plugin_panel_sizer = wx.FlexGridSizer(1, 2, hgap=8, vgap=8)
        plugin_panel_sizer.AddGrowableCol(1, 1)
        panel.SetSizer(plugin_panel_sizer)
        return panel

    def display(self, plugins):
        plugin_panel_sizer = self.plugin_panel.GetSizer()
        plugin_panel_sizer.Clear(True)
        st1 = wx.StaticText(self.plugin_panel, wx.ID_ANY, "Enabled")
        st2 = wx.StaticText(self.plugin_panel, wx.ID_ANY, "Plugin")
        boldFont = wx.SystemSettings_GetFont(wx.SYS_DEFAULT_GUI_FONT)
        boldFont.SetWeight(wx.FONTWEIGHT_BOLD)
        st1.SetFont(boldFont)
        st2.SetFont(boldFont)
        plugin_panel_sizer.Add(st1, 0, wx.BOTTOM, border=8)
        plugin_panel_sizer.Add(st2, 0, wx.BOTTOM|wx.EXPAND, border=8)
        for plugin in plugins:
            cb = wx.CheckBox(self.plugin_panel, wx.ID_ANY)
            cb.SetValue(plugin.active)
            p = PluginRow(self.plugin_panel, wx.ID_ANY, plugin)
            plugin_panel_sizer.Add(cb, 0, wx.ALIGN_CENTER_HORIZONTAL)
            plugin_panel_sizer.Add(p,  0, wx.EXPAND)
            self.plugin_panel.Bind(wx.EVT_CHECKBOX, lambda evt, plugin=plugin: self.OnCheckbox(plugin, evt), cb)
            if plugin.error:
                cb.Enable(False)
        self.Layout()
        self.plugin_panel.Layout()

    def OnCheckbox(self, plugin, evt):
        """Handle checkbox events"""
        if evt.IsChecked():
            plugin.activate()
        else:
            plugin.deactivate()
        # FIXME: saves the wrong settings
        self._save_settings()
        # TODO: move to Plugin
        nb = self.get_notebook()
        nb.SetSelection(nb.GetPageIndex(self.panel))


class PluginRow(wx.Panel):
    """Panel to display the details and configuration options of a plugin."""

    # TODO: there needs to be some smarter handling of long descriptions,
    # such as having them auto-wrap to the size of the window and/or
    # accept some basic HTML.tags.
    def __init__(self, parent, id, plugin):
        wx.Panel.__init__(self, parent, id)
        config = plugin.config_panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(wx.StaticText(self, wx.ID_ANY, plugin.name), 0)
        # TODO: Add plugin metadata 
        sizer.Add(self._get_description(plugin), 0, wx.EXPAND)
        if config:
            sizer.Add(config, 1, wx.EXPAND|wx.LEFT, border=16)
        self.SetSizer(sizer)

    def _name_ctrl(self):
        """Return a suitable control for displaying the plugin name

        This will return a HyperlinkCtrl if an url is defined,
        a StaticText otherwise.
        """
        text = self.plugin.name + " (version %s)" % self.plugin.version
        if self.plugin.url:
            ctrl = wx.HyperlinkCtrl(self, wx.ID_ANY, text, self.plugin.url)
        else:
            ctrl = None
        return ctrl

    def _get_description(self, plugin):
        """Returns an appropriate descriptive string for a plugin"""
        if not plugin.error:
            return wx.StaticText(self, label=plugin.doc)
        text = "This plugin is disabled because it failed to load properly.\n" \
               + "Error: " + plugin.error
        desc = wx.StaticText(self, label=text)
        desc.SetForegroundColour("firebrick")
        return desc
