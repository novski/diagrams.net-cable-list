import sys
import os
import platform
import subprocess
from pathlib import Path
import wx
import logging
from scripts import globallogger
from main import main
from argparse import Namespace

# from wx.lib import inspection as insp


wxEVT_SINGLEFILE_DROPPED = wx.NewEventType()
EVT_SINGLEFILE_DROPPED = wx.PyEventBinder(wxEVT_SINGLEFILE_DROPPED, 1)


class CustomHandler(logging.Handler):
    def __init__(self, target):
        logging.Handler.__init__(self)
        self.target = target

    def emit(self, record):
        self.target.AppendText(record.getMessage() + "\n")

    def clear(self):
        self.target.Clear()

# ---------------------------------------------------------------------------

class FileDropEvent(wx.PyCommandEvent):
    def __init__(self, evtType):
        wx.PyCommandEvent.__init__(self, evtType)
        self._items = []

    def SetSingleItem(self, item):
        self._items = [item]

    def GetSingleItem(self):
        if not self._items:
            return ""
        return self._items[0]

    def AddItem(self, item):
        self._items.append(item)

# ---------------------------------------------------------------------------

class SingleFileDropTarget(wx.FileDropTarget):
    def __init__(self, dstHandler):
        wx.FileDropTarget.__init__(self)
        self._target = dstHandler

    def OnDropFiles(self, x, y, filenames):
        # As we can only accept one file at a time
        # we take only the first element of the provided list
        # and tell the destination handler that a new file has been dropped
        evt = FileDropEvent(wxEVT_SINGLEFILE_DROPPED)
        evt.SetSingleItem(filenames[0])
        self._target.GetEventHandler().AddPendingEvent(evt)
        return True

# ---------------------------------------------------------------------------

class MainFrame(wx.Frame):
    def __init__(self):
        self.renumber = False
        self.exportCablelist = False
        self.exportCablelistFiletype = "csv"
        self.output = False
        self.outputname = False
        self.txtresults = ""

        # insp.InspectionTool().Show()
        wx.Frame.__init__(self, None, title=wx.GetApp().GetAppName())
        self._createControls()
        self._connectControls()

        self.menubar = wx.MenuBar()
        menu = wx.Menu()
        menu_item_1 = menu.Append(101, "&Info")
        menu_item_2 = menu.Append(102, "&Log's")
        menu_item_3 = menu.Append(wx.ID_EXIT, "&Exit...")

        self.menubar.Append(menu, "&File")
        self.SetMenuBar(self.menubar)

        self.Bind(wx.EVT_MENU, self.Info, id=101)
        self.Bind(wx.EVT_MENU, self.Log, id=102)
        self.Bind(wx.EVT_MENU, self.OnClose, id=wx.ID_EXIT)

    def _createControls(self):
        # Add a panel to the frame (needed under Windows to have a nice background)
        pnl = wx.Panel(self, wx.ID_ANY)
        # A Statusbar in the bottom of the window
        self.CreateStatusBar(1)
        sMsg = "Draw.io cable list v.0.2.1"
        self.SetStatusText(sMsg)

        szrMain = wx.BoxSizer(wx.VERTICAL)
        szrMain.AddSpacer(5)

        stbSzr = wx.StaticBoxSizer(wx.VERTICAL, pnl, "Select the File:")
        stBox = stbSzr.GetStaticBox()
        label = wx.StaticText(
            stBox,
            wx.ID_STATIC,
            "Drop any uncompressd draw.io file from the files manager",
        )
        stbSzr.Add(label, 0, wx.LEFT | wx.RIGHT | wx.TOP, 5)
        stbSzr.AddSpacer(5)
        label = wx.StaticText(stBox, wx.ID_STATIC, "to the field below or")
        stbSzr.Add(label, 0, wx.LEFT | wx.RIGHT, 5)
        stbSzr.AddSpacer(5)
        openFileDlgBtn = wx.Button(stBox, label="choose a File")
        openFileDlgBtn.Bind(wx.EVT_BUTTON, self._onOpenFileSource)
        stbSzr.Add(openFileDlgBtn, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        stbSzr.AddSpacer(5)
        label = wx.StaticText(stBox, wx.ID_STATIC, "the path of the chosen File is:")
        stbSzr.Add(label, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        stbSzr.AddSpacer(5)
        self._txtSourceFile = wx.TextCtrl(stBox, -1, wx.EmptyString)
        dt = SingleFileDropTarget(self)
        self._txtSourceFile.SetDropTarget(dt)
        stbSzr.Add(
            self._txtSourceFile, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 5
        )
        szrMain.Add(stbSzr, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 5)

        stbSzr = wx.StaticBoxSizer(wx.VERTICAL, pnl, "choose option:")
        stBox = stbSzr.GetStaticBox()
        stbSzr.AddSpacer(2)
        self.cb1 = wx.CheckBox(
            stBox,
            id=1,
            label='renumber all cables with "Source" and "Target" Tags',
            pos=(15, 15),
        )
        self.Bind(wx.EVT_CHECKBOX, self._onCheckedRenumber, id=1)
        stbSzr.Add(self.cb1, 0, wx.LEFT | wx.RIGHT | wx.TOP, 5)
        stbSzr.AddSpacer(15)
        self.cb2 = wx.CheckBox(stBox, id=2, label="Export Cable list as:", pos=(15, 15))
        self.Bind(wx.EVT_CHECKBOX, self._onCheckedCablelist, id=2)
        stbSzr.Add(self.cb2, 0, wx.LEFT | wx.RIGHT | wx.TOP, 5)
        stbSzr.AddSpacer(5)
        lblList = ["csv", "json"]
        self.rbox = wx.RadioBox(
            stBox,
            pos=(175, 40),
            choices=lblList,
            majorDimension=1,
            style=wx.RA_SPECIFY_ROWS,
        )
        self.rbox.Bind(wx.EVT_RADIOBOX, self.onRadioBox)
        stbSzr.AddSpacer(5)

        szrMain.Add(stbSzr, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)

        stbSzr = wx.StaticBoxSizer(wx.VERTICAL, pnl, "output Path:")
        stBox = stbSzr.GetStaticBox()
        stbSzr.AddSpacer(2)
        label = wx.StaticText(
            stBox, wx.ID_STATIC, "The generated files will be placed here:"
        )
        stbSzr.Add(label, 0, wx.LEFT | wx.RIGHT, 5)
        stbSzr.AddSpacer(5)
        self._txtOutputFile = wx.TextCtrl(
            stBox, -1, wx.EmptyString, style=wx.TE_PROCESS_ENTER
        )
        self._txtOutputFile.Bind(wx.EVT_TEXT_ENTER, self.OnEnterTxtOutputFile)
        stbSzr.Add(
            self._txtOutputFile, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 5
        )
        stbSzr.AddSpacer(2)
        label = wx.StaticText(
            stBox,
            wx.ID_STATIC,
            "If you like to change the Path or the Filename, "
            + "type it without sufix (.xy) in the line above and press Enter to apply.",
        )
        stbSzr.Add(label, 0, wx.LEFT | wx.RIGHT, 5)
        stbSzr.AddSpacer(10)
        openOutputDlgBtn = wx.Button(stBox, label="choose a different output Path")
        stbSzr.Add(openOutputDlgBtn, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        openOutputDlgBtn.Bind(wx.EVT_BUTTON, self._onOpenFileDestination)
        stbSzr.AddSpacer(2)
        szrMain.Add(stbSzr, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 5)

        stbSzr = wx.StaticBoxSizer(wx.HORIZONTAL, pnl, "execute:")
        stBox = stbSzr.GetStaticBox()
        stbSzr.AddSpacer(2)
        executeOkDlgBtn = wx.Button(stBox, label="OK")
        executeCancelDlgBtn = wx.Button(stBox, label="CANCEL")
        executeOkDlgBtn.Bind(wx.EVT_BUTTON, self._executeCommands)
        executeCancelDlgBtn.Bind(wx.EVT_BUTTON, self._executeCommands)
        stbSzr.Add(executeOkDlgBtn, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        stbSzr.Add(executeCancelDlgBtn, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        szrMain.Add(stbSzr, 1, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 5)

        self.txtresults = wx.TextCtrl(
            stBox, size=(420, 200), style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL
        )
        stbSzr.Add(
            self.txtresults,
            1,
            flag=wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND,
            border=5,
        )

        l = CustomHandler(self.txtresults)
        l.setLevel(logging.INFO)
        logger.addHandler(l)

        szrMain.AddSpacer(10)

        pnl.SetSizer(szrMain)
        szrMain.SetSizeHints(self)

    def _connectControls(self):
        self.Bind(EVT_SINGLEFILE_DROPPED, self._onSourceFileDropped)

    def _onCheckedRenumber(self, e):
        cb = e.GetEventObject()
        self.renumber = cb.GetValue()

    def _onCheckedCablelist(self, e):
        cb = e.GetEventObject()
        self.exportCablelist = cb.GetValue()

    def onRadioBox(self, e):
        self.exportCablelistFiletype = self.rbox.GetStringSelection()

    def _onSourceFileDropped(self, evt):
        self._txtSourceFile.ChangeValue(evt.GetSingleItem())

    def _onOpenFileSource(self, event):
        """
        Create and show the Open FileDialog
        """
        dlg = wx.FileDialog(
            self,
            message="Choose a file",
            defaultDir=str(home_directory),
            defaultFile="",
            wildcard="Diagrams.net Drawing (*.drawio)|*.drawio|" "XML Files (*.xml)|*.xml",
            style=wx.FD_OPEN | wx.FD_MULTIPLE | wx.FD_CHANGE_DIR,
        )
        if dlg.ShowModal() == wx.ID_OK:
            self.paths = dlg.GetPaths()
            self._txtSourceFile.ChangeValue(self.paths[0])
            self.sourceFilePath = self.paths[0]
            if self.output == False:
                self.outputPath = os.path.dirname(self.paths[0])
                self.filename = os.path.basename(self.paths[0])
                self.file_sufix_list = os.path.splitext(
                    self.outputPath + os.path.sep + self.filename
                )
                self.outputFilepath = (
                    self.outputPath + os.path.sep + self.file_sufix_list[0]
                )
                self._txtOutputFile.ChangeValue(
                    self.file_sufix_list[0] + "-output" + self.file_sufix_list[1]
                )
        dlg.Destroy()

    def _onOpenFileDestination(self, event):
        """
        Create and show the Open DirectoryDialog
        """
        dlg = wx.DirDialog(
            self,
            message="Choose a path",
            defaultPath=str(self.outputPath),
            style=wx.FD_OPEN | wx.FD_MULTIPLE | wx.FD_CHANGE_DIR,
        )
        if dlg.ShowModal() == wx.ID_OK:
            self.outputPath = dlg.GetPath()
            self.filename = os.path.basename(self.filename)
            self.file_sufix_list = os.path.splitext(
                self.outputPath + os.path.sep + self.filename
            )
            self.outputFilepath = self.file_sufix_list[0]
            self._txtOutputFile.ChangeValue(
                self.file_sufix_list[0] + "-output" + self.file_sufix_list[1]
            )
            self.output = True
        dlg.Destroy()

    def OnEnterTxtOutputFile(self, event):
        self.outputFilepath = self._txtOutputFile.GetValue()
        self.outputPath = os.path.dirname(self.outputFilepath)
        self.filename = os.path.basename(self.outputFilepath)
        self._txtOutputFile.ChangeValue(self.outputFilepath)
        self.output = True
        self.outputname = True

    def _executeCommands(self, event):
        eo = event.GetEventObject()
        if eo.GetLabel() == "CANCEL":
            self.Close(True)
        if eo.GetLabel() == "OK":
            try:
                logger.info("starting main routine..")
                args = Namespace(
                    filepath=self.sourceFilePath,
                    cablesheet=self.exportCablelistFiletype
                    if self.exportCablelist == True
                    else None,
                    renumber=str(self.renumber),
                    outputpath=Path(self.outputFilepath).parent
                    if self.output == True
                    else None,
                    outputname=self.filename if self.outputname == True else None,
                )
                main(args)
            except AttributeError as a:
                logger.info(
                    f"error:{a} -> please provide a file. "\
                    + " You can choose one with the button" \
                    + " or drop it to the line"
                )

    def Info(self, event):
        id_selected = event.GetId()
        logger.info("Info panel will follow in future version.")

    def Log(self, event):
        """
        Create and show the Open DirectoryDialog
        """
        # if event.GetId() == 103:
        dlg = wx.FileDialog(
            self,
            message="Choose a Logfile",
            wildcard="Log's (*.log)|*.log",
            defaultDir=working_directory + os.pathsep + "log",
            style=wx.FD_OPEN | wx.FD_MULTIPLE | wx.FD_CHANGE_DIR,
        )
        if dlg.ShowModal() == wx.ID_OK:
            self.logfile = dlg.GetPaths()[0]
            print(f"logfile:{self.logfile}")
            if platform.system() == "Darwin":  # macOS
                subprocess.call(("open", self.logfile))
            elif platform.system() == "Windows":  # Windows
                os.startfile(self.logfile)
            else:  # linux variants
                subprocess.call(("xdg-open", self.logfile))
        dlg.Destroy()

    def OnClose(self, event):
        self.Close()

# ---------------------------------------------------------------------------

class Window(wx.App):
    def OnInit(self):

        # Set Current directory to the  one containing this file
        os.chdir(working_directory)

        self.SetAppName("draw.io cable labeler")

        # Create the main Frame in Window
        frm = MainFrame()
        self.SetTopWindow(frm)  # bring the Window to visible front

        frm.Show()
        return True


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # working_directory is initialized in main
    # because of the different working_directories when
    # localy executed or installed from pkg or exe.
    # be aware that the working_directory is not the
    # same as the home_directory.
    # ! home is where we open the file choosing window after pressing the button
    # ! work is where we have the scripts, logs and binaries
    home_directory = os.path.expanduser("~")
    try:
        working_directory = sys._MEIPASS
    except AttributeError:
        working_directory = os.getcwd()

    # rename variables to match globallogger's argparse Namespace system
    args = Namespace(loggpath=working_directory + os.pathsep + "log", logglevel="INFO")
    logger = globallogger.setup_custom_logger(args, "scraper")
    logger.info(f"starting logger in window.py ...")
    logger.info(f"Running wxPython {wx.version()} on Python {sys.version}")

    app = Window()
    app.MainLoop()
