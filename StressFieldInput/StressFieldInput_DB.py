import abaqusGui
from kernelAccess import mdb


# Class for the plugin Dialog Box
class PluginDialog(abaqusGui.AFXDataDialog):

    # id values, useful for commands between widgets
    [
        ID_JOB
    ] = range(abaqusGui.AFXToolsetGui.ID_LAST, abaqusGui.AFXToolsetGui.ID_LAST+1)

    # constructor
    def __init__(self, form, step):
        # Call super constructor
        abaqusGui.AFXDataDialog.__init__(self, form, 'Stress Field Input',
                                         self.APPLY | self.CANCEL, abaqusGui.DIALOG_ACTIONS_SEPARATOR)
        # Store the form
        self.form = form
        # Define command map # Define command map
        abaqusGui.FXMAPFUNC(self, abaqusGui.SEL_COMMAND, self.ID_JOB, PluginDialog.on_message)
        # Configure apply button: run the code (issue commands)
        apply_btn = self.getActionButton(self.ID_CLICKED_APPLY)
        apply_btn.setText('Run')
        apply_btn.disable()
        # Configure cancel button: close window
        close_btn = self.getActionButton(self.ID_CLICKED_CANCEL)
        close_btn.setText('Close')
        # First horizontal frame
        frame_1 = abaqusGui.FXHorizontalFrame(p=self)
        # Child vertical frame 1
        frame_1_1 = abaqusGui.FXVerticalFrame(p=frame_1)
        # Aligner
        aligner = abaqusGui.AFXVerticalAligner(p=frame_1_1)
        # Define the width of the input widgets
        widget_width = 12
        # Add combo box to select the job and populate it with valid jobs
        job_names = mdb.jobs.keys()
        self.cbx_job = abaqusGui.AFXComboBox(p=aligner, ncols=widget_width, nvis=0, text='Default Job',
                                             tgt=self, sel=self.ID_JOB)
        index = 0
        for job_name in job_names:
            # Fetch the job
            job = mdb.jobs[job_name]
            if job is None:
                continue
            # Check if the job has a model
            if hasattr(job, 'model'):
                self.cbx_job.appendItem(text=job_name, sel=index)
                index = index + 1
        # Text box for the number of stress value scales
        self.txt_scale_counts = abaqusGui.AFXTextField(p=aligner, ncols=widget_width, labelText='Scale Count',
                                                       tgt=form.kw_scale_counts, sel=0,
                                                       opts=abaqusGui.AFXTEXTFIELD_INTEGER | abaqusGui.LAYOUT_CENTER_Y)
        self.txt_scale_counts.setText('1')
        # Text box for the minimum stress value scale
        self.txt_scale_min = abaqusGui.AFXTextField(p=aligner, ncols=widget_width, labelText='Scale Min',
                                                    tgt=form.kw_scale_min, sel=0,
                                                    opts=abaqusGui.AFXTEXTFIELD_FLOAT | abaqusGui.LAYOUT_CENTER_Y)
        self.txt_scale_min.setText('1')
        # Text box for the maximum stress value scale
        self.txt_scale_max = abaqusGui.AFXTextField(p=aligner, ncols=widget_width, labelText='Scale Max',
                                                    tgt=form.kw_scale_max, sel=0,
                                                    opts=abaqusGui.AFXTEXTFIELD_FLOAT | abaqusGui.LAYOUT_CENTER_Y)
        self.txt_scale_max.setText('1')
        # Widgets to load stress script
        self.lbl_stress_script = abaqusGui.FXLabel(p=frame_1_1, text='Stress Script')
        file_handler_stress = FileOpenDialog(form.kw_stress_script, '*.py')
        frame_file_text_1 = abaqusGui.FXHorizontalFrame(p=frame_1_1)
        frame_file_text_1.setSelector(99)
        self.txt_stress_script = abaqusGui.AFXTextField(p=frame_file_text_1, ncols=widget_width + 7, labelText='',
                                                        tgt=form.kw_stress_script, sel=0,
                                                        opts=abaqusGui.AFXTEXTFIELD_STRING | abaqusGui.LAYOUT_CENTER_Y)
        icon = abaqusGui.afxGetIcon('fileOpen', abaqusGui.AFX_ICON_SMALL)
        abaqusGui.FXButton(p=frame_file_text_1, text='	Select Stress Script\nFrom Dialog', ic=icon,
                           tgt=file_handler_stress, sel=abaqusGui.AFXMode.ID_ACTIVATE,
                           opts=abaqusGui.BUTTON_NORMAL | abaqusGui.LAYOUT_CENTER_Y,
                           x=0, y=0, w=0, h=0, pl=1, pr=1, pt=1, pb=1)
        # Widgets to load error script
        self.lbl_error_script = abaqusGui.FXLabel(p=frame_1_1, text='Error Script (optional)')
        file_handler_error = FileOpenDialog(form.kw_error_script, '*.py')
        frame_file_text_2 = abaqusGui.FXHorizontalFrame(p=frame_1_1)
        frame_file_text_2.setSelector(99)
        self.txt_error_script = abaqusGui.AFXTextField(p=frame_file_text_2, ncols=widget_width + 7, labelText='',
                                                       tgt=form.kw_error_script, sel=0,
                                                       opts=abaqusGui.AFXTEXTFIELD_STRING | abaqusGui.LAYOUT_CENTER_Y)
        icon = abaqusGui.afxGetIcon('fileOpen', abaqusGui.AFX_ICON_SMALL)
        abaqusGui.FXButton(p=frame_file_text_2, text='	Select Error Script\nFrom Dialog', ic=icon,
                           tgt=file_handler_error, sel=abaqusGui.AFXMode.ID_ACTIVATE,
                           opts=abaqusGui.BUTTON_NORMAL | abaqusGui.LAYOUT_CENTER_Y,
                           x=0, y=0, w=0, h=0, pl=1, pr=1, pt=1, pb=1)
        # Check box to run the jobs
        self.cbx_run_jobs = abaqusGui.FXCheckButton(p=frame_1_1, text='Run Jobs', tgt=form.kw_run_jobs, sel=0)
        # Check box to iterate with the error script
        self.cbx_iterate = abaqusGui.FXCheckButton(p=frame_1_1, text='Iterate', tgt=form.kw_iterate, sel=0)
        # Set currently selected items to their defaults (to force an update on first opening of the GUI)
        self.currentJob = -1
        self.currentStressScript = ''
        self.currentErrorScript = ''
        # Force initial updates
        self.on_job_selected()

    # general callback method for when a user performs an action on a widget,
    # routes the callback forward to the respective callback method for the widget
    def on_message(self, sender, sel, ptr):
        if abaqusGui.SELID(sel) == self.ID_JOB:
            self.on_job_selected()

    # callback method for when the user selects a new slave
    def on_job_selected(self):
        # If there are no jobs in the mdb, run default logic and return to avoid crashing
        if len(mdb.jobs.keys()) <= 0 or self.cbx_job.getNumItems() <= 0:
            self.currentJob = -1
            self.update_widget_states()
            return
        # Get the index of the currently selected job
        job_index = self.cbx_job.getItemData(self.cbx_job.getCurrentItem())
        # If a different model has been selected, the GUI needs to be updated
        if job_index != self.currentJob:
            # Update the selected job
            self.currentJob = job_index
            # Update the job keyword value
            job_name = self.cbx_job.getItemText(self.currentJob)
            self.form.kw_def_job.setValue(job_name)
            # Update action button state
            self.update_widget_states()

    # Method for when a stress script has been selected
    def on_stress_script_selected(self, stress_script):
        # Update the current script
        self.currentStressScript = stress_script
        # Update the action button state
        self.update_widget_states()

    # Method for when a stress script has been selected
    def on_error_script_selected(self, error_script):
        # Update the current script
        self.currentErrorScript = error_script
        # Update the action button state
        self.update_widget_states()

    # Method to update the state of the create button based on the current user inputs
    def update_widget_states(self):
        # Check that the job has been defined
        job_flag = self.currentJob < 0
        # Check that the stress script has been defined
        script_flag = self.currentStressScript == ''
        # Update action button state accordingly
        if job_flag or script_flag:
            self.getActionButton(self.ID_CLICKED_APPLY).disable()
        else:
            self.getActionButton(self.ID_CLICKED_APPLY).enable()
        # Check that the error script has been defined
        if self.currentErrorScript == '':
            self.form.kw_iterate.setValue(False)
            self.cbx_iterate.disable()
        else:
            self.cbx_iterate.enable()

    # Override from parent class
    def processUpdates(self):
        # Super call
        abaqusGui.AFXDataDialog.processUpdates(self)
        # Update action button state
        self.update_widget_states()


# Class for the file selection dialog
class FileOpenDialog(abaqusGui.FXObject):
    def __init__(self, file_name_keyword, patterns='*'):
        self.patterns = patterns
        self.pattern_target = abaqusGui.AFXIntTarget(0)
        self.file_name_keyword = file_name_keyword
        self.read_only_keyword = abaqusGui.AFXBoolKeyword(None, 'readOnly', abaqusGui.AFXBoolKeyword.TRUE_FALSE)
        abaqusGui.FXObject.__init__(self)
        abaqusGui.FXMAPFUNC(self, abaqusGui.SEL_COMMAND, abaqusGui.AFXMode.ID_ACTIVATE, FileOpenDialog.on_message)

    def on_message(self, sender, sel, ptr):
        file_dialog = abaqusGui.AFXFileSelectorDialog(abaqusGui.getAFXApp().getAFXMainWindow(), 'Select Stress Script',
                                                      self.file_name_keyword, self.read_only_keyword,
                                                      abaqusGui.AFXSELECTFILE_EXISTING,
                                                      self.patterns, self.pattern_target)
        file_dialog.setReadOnlyPatterns('*.odb')
        file_dialog.create()
        file_dialog.showModal()


# Utility method to print a message to the console
def debug_message(msg):
    abaqusGui.getAFXApp().getAFXMainWindow().writeToMessageArea(msg)
