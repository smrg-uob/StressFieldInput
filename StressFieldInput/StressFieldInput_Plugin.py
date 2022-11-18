import abaqusGui
import abaqusConstants
import os
import StressFieldInput_DB


# Class for the plugin, the code is implemented as a procedure running to different steps.
# The code is designed as such that the automatic issuing of commands by Abaqus is avoided.
# The procedure will only loop through the inner step sequence (see the Abaqus GUI Toolkit User Manual 7.2.1)
# Kernel commands are issued manually where necessary, and the procedure is exited when the user closes the GUI
class Plugin(abaqusGui.AFXForm):
    # Constants defining flags for the different steps
    STEP_MAIN = 0

    # An array holding the names of each step (useful for debugging)
    STEPS = ['MAIN']

    def __init__(self, owner):
        # Call super constructor
        abaqusGui.AFXForm.__init__(self, owner)
        # Define an integer for the current method
        self.method = 0
        # Define the run plugin command with scaling
        self.cmd_scaling = abaqusGui.AFXGuiCommand(mode=self, method='stress_field_input_scaling',
                                                   objectName='StressFieldInput_Kernel', registerQuery=True)
        # Define the run plugin command with substitution
        self.cmd_substitution = abaqusGui.AFXGuiCommand(mode=self, method='stress_field_input_substitution',
                                                        objectName='StressFieldInput_Kernel', registerQuery=True)
        # Dummy command for the common keywords
        self.cmd_dummy = abaqusGui.AFXGuiCommand(mode=self, method='', objectName='', registerQuery=False)
        # Store the methods
        self.methods = [
            self.cmd_scaling,
            self.cmd_substitution
        ]
        # Define the common keywords for the commands
        self.kw_def_job = CallBackStringKeyword(
            self.cmd_dummy, 'default_job', True, ''
        )
        self.kw_stress_script = CallBackStringKeyword(
            self.cmd_dummy, 'stress_script', True, ''
        )
        self.kw_error_script = CallBackStringKeyword(
            self.cmd_dummy, 'error_script', True, ''
        )
        # Define the keywords for the scaling command
        self.kw_def_job_scaling = abaqusGui.AFXStringKeyword(
            self.cmd_scaling, 'default_job', True, ''
        )
        self.kw_scale_counts = abaqusGui.AFXIntKeyword(
            self.cmd_scaling, 'stress_scale_counts', True, 1, False
        )
        self.kw_scale_min = abaqusGui.AFXFloatKeyword(
            self.cmd_scaling, 'stress_scale_min', True, 1.0
        )
        self.kw_scale_max = abaqusGui.AFXFloatKeyword(
            self.cmd_scaling, 'stress_scale_max', True, 1.0
        )
        self.kw_stress_script_scaling = abaqusGui.AFXStringKeyword(
            self.cmd_scaling, 'stress_script', True, ''
        )
        self.kw_error_script_scaling = abaqusGui.AFXStringKeyword(
            self.cmd_scaling, 'error_script', True, ''
        )
        self.kw_run_jobs = abaqusGui.AFXBoolKeyword(
            self.cmd_scaling, 'run_jobs', abaqusGui.AFXBoolKeyword.TRUE_FALSE, True, False
        )
        self.kw_iterate = abaqusGui.AFXBoolKeyword(
            self.cmd_scaling, 'iterate', abaqusGui.AFXBoolKeyword.TRUE_FALSE, True, False
        )
        # Define the keywords for the substitution command
        self.kw_def_job_substitution = abaqusGui.AFXStringKeyword(
            self.cmd_substitution, 'default_job', True, ''
        )
        self.kw_max_it = abaqusGui.AFXIntKeyword(
            self.cmd_substitution, 'max_it', True, 1, False
        )
        self.kw_dev = abaqusGui.AFXFloatKeyword(
            self.cmd_substitution, 'max_dev', True, 0.001
        )
        self.kw_err = abaqusGui.AFXFloatKeyword(
            self.cmd_substitution, 'max_err', True, 0.001
        )
        self.kw_stress_script_substitution = abaqusGui.AFXStringKeyword(
            self.cmd_substitution, 'stress_script', True, ''
        )
        self.kw_error_script_substitution = abaqusGui.AFXStringKeyword(
            self.cmd_substitution, 'error_script', True, ''
        )
        # Add callback to the job keyword
        self.kw_def_job.add_callback(self.update_default_job)

    def get_method(self):
        if 0 <= self.method < len(self.methods):
            return self.methods[self.method]
        return None

    def set_method(self, value):
        self.method = value

    def set_method_scaling(self):
        self.set_method(0)

    def set_method_substitution(self):
        self.set_method(1)

    def update_default_job(self, value):
        self.kw_def_job_scaling.setValue(value)
        self.kw_def_job_substitution.setValue(value)

    def update_stress_script(self, value):
        self.kw_stress_script_scaling.setValue(value)
        self.kw_stress_script_substitution.setValue(value)

    def update_error_script(self, value):
        self.kw_error_script_scaling.setValue(value)
        self.kw_error_script_substitution.setValue(value)

    # Getter for the next step
    def get_next_dialog(self):
        # reset script keyword callbacks (prevents memory leaks)
        self.kw_stress_script.clear_callbacks()
        self.kw_error_script.clear_callbacks()
        # create dialog
        dialog = StressFieldInput_DB.PluginDialog(self, self.STEP_MAIN)
        # register callback for the script keywords
        self.kw_stress_script.add_callback(dialog.on_stress_script_selected)
        self.kw_stress_script.add_callback(self.update_stress_script)
        self.kw_error_script.add_callback(dialog.on_error_script_selected)
        self.kw_error_script.add_callback(self.update_error_script)
        # return the dialog
        return dialog

    # Override from AFXForm to return the first dialog
    def getFirstDialog(self):
        # simply forward to the general dialog selection method
        return self.get_next_dialog()

    # Override from AFXForm to return the next dialog in the inner step loop
    def getNextDialog(self, prev):
        # simply forward to the general dialog selection method
        return self.get_next_dialog()

    # Override from AFXForm to return the next dialog in the outer step loop
    def getLoopDialog(self):
        # simply forward to the general dialog selection method
        return self.get_next_dialog()

    # Override from AFXForm to perform custom checks, return true to continue the code flow
    def doCustomChecks(self):
        # We will use this method to control what command is to be issued
        method = self.get_method()
        if method is not None:
            issue_command(method)
        return True

    # Override to verify the keyword values in the inner loop, return true to continue the code flow
    def verifyCurrentKeywordValues(self):
        # Return true to continue
        return True

    # Override to verify the keyword values in the outer loop, return true to continue the code flow
    def verifyKeywordValues(self):
        # Return true to continue
        return True

    # Override from AFXProcedure to perform custom tasks
    def doCustomTasks(self):
        pass

    # Override to prevent the automatic flow from issuing commands
    def issueCommands(self, writeToReplay, writeToJournal):
        pass

    # Method override
    def okToCancel(self):
        return False


# Wrapper class to provide callbacks for when the keyword changes
class CallBackStringKeyword(abaqusGui.AFXStringKeyword):
    def __init__(self, command, name, is_required, default_value, ):
        abaqusGui.AFXStringKeyword.__init__(self, command, name, is_required, default_value)
        self.callbacks = []

    def setValue(self, new_value):
        # Call super
        abaqusGui.AFXStringKeyword.setValue(self, new_value)
        # Run callbacks
        for callback in self.callbacks:
            callback(new_value)

    def add_callback(self, callback):
        # Add the callback
        self.callbacks.append(callback)
        # Call the callback with the current value
        callback(self.getValue())

    def clear_callbacks(self):
        self.callbacks = []


# Utility method to issues a command to the kernel
def issue_command(cmd):
    abaqusGui.sendCommand(cmd.getCommandString())


# Utility method to print a message to the console
def debug_message(msg):
    abaqusGui.getAFXApp().getAFXMainWindow().writeToMessageArea(msg)


# Code for the registration of the plug-in
thisPath = os.path.abspath(__file__)
thisDir = os.path.dirname(thisPath)
toolset = abaqusGui.getAFXApp().getAFXMainWindow().getPluginToolset()
toolset.registerGuiMenuButton(
    buttonText='Stress Field Input',
    object=Plugin(toolset),
    messageId=abaqusGui.AFXMode.ID_ACTIVATE,
    icon=None,
    kernelInitString='import StressFieldInput_Kernel',
    applicableModules=abaqusConstants.ALL,
    version='3.0',
    author='Xavier van Heule',
    description='A plugin to easily input arbitrary stress fields into Abaqus',
    helpUrl='https://github.com/smrg-uob/StressFieldInput/blob/master/README.md'
)
