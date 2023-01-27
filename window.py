import os
import pathlib
import wx
from wx.lib import inspection as insp
import subprocess

wildcard =  "Drawings (*.drawio,*.xml)|*.drawio;*.xml" #"All files (*.*) | *.*"
wxEVT_SINGLEFILE_DROPPED = wx.NewEventType()
EVT_SINGLEFILE_DROPPED = wx.PyEventBinder(wxEVT_SINGLEFILE_DROPPED, 1)

#---------------------------------------------------------------------------

class FileDropEvent(wx.PyCommandEvent):
    def __init__(self, evtType):
        wx.PyCommandEvent.__init__(self, evtType)
        self._items = []

    def SetSingleItem(self, item):
        self._items = [item]

    def GetSingleItem(self):
        if not self._items:
            return ''
        return self._items[0]

    def AddItem(self, item):
        self._items.append(item)

#---------------------------------------------------------------------------

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

#---------------------------------------------------------------------------

class MyFrame(wx.Frame):
    def __init__(self):
        self.renumber = False
        self.exportCablelist = False
        self.exportCablelistFiletype = 'csv'
        self.output = False
        #insp.InspectionTool().Show()
        wx.Frame.__init__(self, None, title=wx.GetApp().GetAppName())

        self._createControls()

        self._connectControls()

        self.home_directory = pathlib.Path.home()

    def _createControls(self):
        # A Statusbar in the bottom of the window
        self.CreateStatusBar(1)
        sMsg = 'Draw.io cable list v.0.0.1'
        self.SetStatusText(sMsg)

        # Add a panel to the frame (needed under Windows to have a nice background)
        pnl = wx.Panel(self, wx.ID_ANY)

        szrMain = wx.BoxSizer(wx.VERTICAL)
        szrMain.AddSpacer(5)

        stbSzr = wx.StaticBoxSizer(wx.VERTICAL, pnl, 'Select the File:')
        stBox = stbSzr.GetStaticBox()
        label = wx.StaticText(stBox, wx.ID_STATIC, 'Drop any uncompressd draw.io file from the files manager')
        stbSzr.Add(label, 0, wx.LEFT|wx.RIGHT|wx.TOP, 5)
        stbSzr.AddSpacer(5)
        label = wx.StaticText(stBox, wx.ID_STATIC, 'to the field below or')
        stbSzr.Add(label, 0, wx.LEFT|wx.RIGHT, 5)
        stbSzr.AddSpacer(5)
        openFileDlgBtn = wx.Button(stBox, label="choose a File")
        openFileDlgBtn.Bind(wx.EVT_BUTTON, self._onOpenFileSource)
        stbSzr.Add(openFileDlgBtn, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM, 5)
        stbSzr.AddSpacer(5)
        label = wx.StaticText(stBox, wx.ID_STATIC, 'the path of the chosen File is:')
        stbSzr.Add(label, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM, 5)
        stbSzr.AddSpacer(5)
        self._txtSourceFile = wx.TextCtrl(stBox, -1, wx.EmptyString)
        dt = SingleFileDropTarget(self)
        self._txtSourceFile.SetDropTarget(dt)
        stbSzr.Add(self._txtSourceFile, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        szrMain.Add(stbSzr, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        
        stbSzr = wx.StaticBoxSizer(wx.VERTICAL, pnl, 'choose option:')
        stBox = stbSzr.GetStaticBox()
        stbSzr.AddSpacer(2)
        self.cb1 = wx.CheckBox(stBox,id=1,label = 'renumber all cables with "Source" & "Target" Tags',pos = (15,15))
        self.Bind(wx.EVT_CHECKBOX,self._onCheckedRenumber,id=1) 
        stbSzr.Add(self.cb1, 0, wx.LEFT|wx.RIGHT|wx.TOP, 5)
        stbSzr.AddSpacer(15)
        self.cb2 = wx.CheckBox(stBox, id=2, label = 'Export Cable list as:',pos = (15,15))
        self.Bind(wx.EVT_CHECKBOX,self._onCheckedCablelist,id=2) 
        stbSzr.Add(self.cb2, 0, wx.LEFT|wx.RIGHT|wx.TOP, 5)
        stbSzr.AddSpacer(5)
        lblList = ['csv', 'json']     
        self.rbox = wx.RadioBox(stBox, 
                                pos = (180,-5), choices = lblList ,
                                majorDimension = 1, 
                                style = wx.RA_SPECIFY_ROWS)
        self.rbox.Bind(wx.EVT_RADIOBOX,self.onRadioBox)    

        szrMain.Add(stbSzr, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM, 5)
        
        stbSzr = wx.StaticBoxSizer(wx.VERTICAL, pnl, 'output Path:')
        stBox = stbSzr.GetStaticBox()
        stbSzr.AddSpacer(2)
        label = wx.StaticText(stBox, wx.ID_STATIC, 'The generated files will be placed here:')
        stbSzr.Add(label, 0, wx.LEFT|wx.RIGHT, 5)
        stbSzr.AddSpacer(5)
        self._txtOutputFile = wx.TextCtrl(stBox, -1, wx.EmptyString, style=wx.TE_PROCESS_ENTER)
        self._txtOutputFile.Bind(wx.EVT_TEXT_ENTER,self.OnEnterTxtOutputFile) 
        stbSzr.Add(self._txtOutputFile, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
        openOutputDlgBtn = wx.Button(stBox, label="choose a different output Path")
        stbSzr.Add(openOutputDlgBtn, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM, 5)
        openOutputDlgBtn.Bind(wx.EVT_BUTTON, self._onOpenFileDestination)
        stbSzr.AddSpacer(2)
        szrMain.Add(stbSzr, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)

        stbSzr = wx.StaticBoxSizer(wx.HORIZONTAL, pnl, 'execute:')
        stBox = stbSzr.GetStaticBox()
        stbSzr.AddSpacer(2)
        executeOkDlgBtn = wx.Button(stBox, label="OK")
        executeCancelDlgBtn = wx.Button(stBox, label="CANCEL")
        executeOkDlgBtn.Bind(wx.EVT_BUTTON, self._executeCommands)
        executeCancelDlgBtn.Bind(wx.EVT_BUTTON, self._executeCommands)
        stbSzr.Add(executeOkDlgBtn, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM, 5)
        stbSzr.Add(executeCancelDlgBtn, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM, 5)
        szrMain.Add(stbSzr, 1, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)

        self.txtresults = wx.TextCtrl(stBox, 
                                      size=(420,200), 
                                      style = wx.TE_MULTILINE|wx.TE_READONLY|wx.HSCROLL)
        stbSzr.Add(self.txtresults, 1, flag=wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, border=5)

        szrMain.AddSpacer(10)

        pnl.SetSizer(szrMain)
        szrMain.SetSizeHints(self)
        
    def _onCheckedRenumber(self, e): 
        cb = e.GetEventObject()
        self.renumber = cb.GetValue()
        print(f'renumber: {self.renumber}')

    def _onCheckedCablelist(self, e):
        cb = e.GetEventObject()
        self.exportCablelist = cb.GetValue()
        print(f'export Cablelist {self.exportCablelist}')

    def onRadioBox(self,e):
        self.exportCablelistFiletype = self.rbox.GetStringSelection()
        print(f'{self.rbox.GetStringSelection()} is clicked from filetype')

    def _connectControls(self):
        self.Bind(EVT_SINGLEFILE_DROPPED, self._onSourceFileDropped)

    def _onSourceFileDropped(self, evt):
        self._txtSourceFile.ChangeValue(evt.GetSingleItem())

    def _onOpenFileSource(self, event):
        """
        Create and show the Open FileDialog
        """
        dlg = wx.FileDialog(
            self, message="Choose a file",
            defaultDir=str(self.home_directory), 
            defaultFile="",
            wildcard=wildcard,
            style=wx.FD_OPEN | wx.FD_MULTIPLE | wx.FD_CHANGE_DIR
            )
        if dlg.ShowModal() == wx.ID_OK:
            self.paths = dlg.GetPaths()
            self._txtSourceFile.ChangeValue(self.paths[0])
            self.sourceFilePath = self.paths[0]
            if self.output == False:
                self._txtOutputFile.ChangeValue(self.paths[0])
                self.outputPath = os.path.dirname(self.paths[0])
                self.filename = os.path.basename(self.paths[0])
        dlg.Destroy()  
      
    def _onOpenFileDestination(self, event):
        """
        Create and show the Open DirectoryDialog
        """
        dlg = wx.DirDialog(
            self, message="Choose a path",
            defaultPath=self.paths[0], 
            style=wx.FD_OPEN | wx.FD_MULTIPLE | wx.FD_CHANGE_DIR
            )
        if dlg.ShowModal() == wx.ID_OK:
            self.outputPath = dlg.GetPath()
            self.filename = os.path.basename(self.filename)
            self.pathSeparator = os.path.sep
            self.outputFilepath = self.outputPath + self.pathSeparator + self.filename
            self._txtOutputFile.ChangeValue(self.outputFilepath)
            self.output = True
        dlg.Destroy()   

    def OnEnterTxtOutputFile(self, event):
        self.outputFilepath = self._txtOutputFile.GetValue()
        self.outputPath = os.path.dirname(self.outputFilepath)
        self.filename = os.path.basename(self.outputFilepath)
        self.pathSeparator = os.path.sep
        self.outputFilepath = self.outputPath + self.pathSeparator + self.filename
        self._txtOutputFile.ChangeValue(self.outputFilepath)
        self.output = True
        print(f'filepath: {self.outputFilepath}, filename:{self.filename}')

    def _executeCommands(self, event):
        eo = event.GetEventObject()
        if eo.GetLabel() == 'CANCEL':
            print(f'CANCEL')
            self.Close(True) 
        if eo.GetLabel() == 'OK':
            if self.sourceFilePath:
                self.exec = 'python3 main.py'
                if self.exportCablelist == True:
                    self.exec =  self.exec + ' -c ' + self.exportCablelistFiletype
                if self.renumber == True:
                    self.exec = self.exec + ' -nr True'
                if self.output == True:
                    self.exec = self.exec + ' -o ' + self.outputPath + self.pathSeparator + ' -n ' + self.filename
                if self.exportCablelist == False & self.renumber == False:
                    print(f'nothing to do. dryrun with logs will be made, please choose a option...')
                self.exec = self.exec + ' -log INFO ' + self.sourceFilePath
                print(f'exec {self.exec}')
                proc = subprocess.Popen(self.exec, 
                                        shell=True, 
                                        stdout=subprocess.PIPE, 
                                        stderr=subprocess.STDOUT,
                                        text=True) 
                while True:
                    line = proc.stdout.readline()                        
                    #wx.Yield()
                    if line.strip() == "":
                        print('line empty')
                        pass
                    else:
                        self.txtresults.AppendText(line.strip())
                        self.txtresults.AppendText('\n')
                    if not line: 
                        print('break')
                        break
                proc.wait()
        else:
            print(f'exec incomplete: {self.exec}')

#---------------------------------------------------------------------------

class MyApp(wx.App):
    def OnInit(self):
        print('Running wxPython ' + wx.version())
        # Set Current directory to the  one containing this file
        os.chdir(os.path.dirname(os.path.abspath(__file__)))

        self.SetAppName('draw.io cable labeler')

        # Create the main window
        frm = MyFrame()
        self.SetTopWindow(frm)

        frm.Show()
        return True

#---------------------------------------------------------------------------

if __name__ == '__main__':
    app = MyApp()
    app.MainLoop()
    