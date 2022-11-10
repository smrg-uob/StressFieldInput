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
        # Define the run plugin command
        self.cmd = abaqusGui.AFXGuiCommand(mode=self, method='run_plugin', objectName='StressFieldInput_Kernel',
                                           registerQuery=False)
        # Define the keywords for the command
        self.kw_def_job = abaqusGui.AFXStringKeyword(self.cmd, 'default_job', True, '')
        self.kw_scale_counts = abaqusGui.AFXIntKeyword(self.cmd, 'stress_scale_counts', True, 1, False)
        self.kw_scale_min = abaqusGui.AFXIntKeyword(self.cmd, 'stress_scale_min', True, 1, False)
        self.kw_scale_max = abaqusGui.AFXIntKeyword(self.cmd, 'stress_scale_max', True, 1, False)
        self.kw_stress_script = CallBackStringKeyword(self.cmd, 'stress_script', True, '')
        self.kw_error_script = CallBackStringKeyword(self.cmd, 'error_script', True, '')
        self.kw_run_jobs = abaqusGui.AFXBoolKeyword(self.cmd, 'run_jobs', abaqusGui.AFXBoolKeyword.TRUE_FALSE, True, True)

    # Getter for the next step
    def get_next_dialog(self):
        # reset stress script keyword callbacks (prevents memory leaks)
        self.kw_stress_script.clear_callbacks()
        # create dialog
        dialog = StressFieldInput_DB.PluginDialog(self, self.STEP_MAIN)
        # register callback for the stress script keyword
        self.kw_stress_script.add_callback(dialog.on_stress_script_selected)
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


# Wrapper class to provide callbacks for when the keyword changes
class CallBackStringKeyword(abaqusGui.AFXStringKeyword):
    def __init__(self, command, name, isRequired, defaultValue,):
        abaqusGui.AFXStringKeyword.__init__(self, command, name, isRequired, defaultValue)
        self.callbacks = []

    def setValue(self, newValue):
        # Call super
        abaqusGui.AFXStringKeyword.setValue(self, newValue)
        # Run callbacks
        for callback in self.callbacks:
            callback(newValue)

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
    version='1.1',
    author='Xavier van Heule',
    description='A plugin to easily input arbitrary stress fields into Abaqus',
    helpUrl='https://github.com/smrg-uob/StressFieldInput/blob/master/README.md'
)
