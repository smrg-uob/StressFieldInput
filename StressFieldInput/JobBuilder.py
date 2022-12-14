# coding=utf-8

import abaqus
from abaqusConstants import *
import numpy as np


# Class with the single task of building stress input jobs from the default job
class JobBuilder:
    def __init__(self, default_job, mesh_data):
        # Define fields
        self.default_job = default_job
        self.mesh_data = mesh_data
        self.valid = mesh_data is not None
        self.default_input = []
        self.next_line = -1
        self.predefined = False
        # Initialize
        self.__on_init()

    # Checks if the job builder is valid
    def is_valid(self):
        return self.valid

    # Creates a job for a given strength scale
    def create_job(self, job_name_index, stress_scale):
        # Create a copy of the default input
        lines = self.default_input[:]
        # Define injection index starting at the current next line
        inject_index = self.next_line
        # Put in the header for the predefined field
        if not self.predefined:
            lines[inject_index:inject_index] = ['** ']
            inject_index = inject_index + 1
            lines[inject_index:inject_index] = ['** PREDEFINED FIELDS']
            inject_index = inject_index + 1
            lines[inject_index:inject_index] = ['** ']
            inject_index = inject_index + 1
        lines[inject_index:inject_index] = ['*Initial Conditions, type=STRESS']
        inject_index = inject_index + 1
        # Iterate over part instances
        for part_index in np.arange(0, len(self.mesh_data)):
            mesh_data_part = self.mesh_data[part_index]
            if mesh_data_part is None:
                continue
            # Iterate over the stress sets
            for stress_set in mesh_data_part.get_stress_sets():
                # Fetch the stress
                stress = stress_set.get_stress()
                if stress is None:
                    continue
                # Inject and scale in the input file
                line = stress_set.get_instance_name() + '.' + stress_set.get_set_name() + ','
                for stress_index in np.arange(0, len(stress)):
                    line = line + str(stress_scale*stress[stress_index]) + ','
                lines[inject_index:inject_index] = [line]
        # Write the input file
        input_file_name = self.default_job + '_Stress_Input_Scale_' + str(job_name_index) + '.inp'
        out = open(input_file_name, 'w')
        for line_index in np.arange(0, len(lines)):
            out.write(lines[line_index] + '\n')
        out.close()
        # Create job from the input file
        job_name = self.default_job + '_Stress_Input_Scale_' + str(job_name_index)
        return abaqus.mdb.JobFromInputFile(job_name, input_file_name)

    def update_stress_from_odb(self, odb):
        # Fetch general stress field output at the centre of the elements
        step = odb.steps[odb.steps.keys()[len(odb.steps.keys()) - 1]]
        frame = step.frames[len(step.frames) - 1]
        stress_output = frame.fieldOutputs['S'].getSubset(position=CENTROID)
        # Define maximum deviation
        max_dev = 0
        # Iterate over part instances
        for part_index in np.arange(0, len(self.mesh_data)):
            mesh_data_part = self.mesh_data[part_index]
            if mesh_data_part is None:
                continue
            # Iterate over all stress sets
            for stress_set in mesh_data_part.get_stress_sets():
                # Fetch element data
                instance_name = stress_set.get_instance_name().upper()  # In the ODB instance names are upper case
                element_label = stress_set.get_label()
                # Extract stress values for the element
                mesh_element = odb.rootAssembly.instances[instance_name].elements[element_label - 1]
                stress_values = stress_output.getSubset(region=mesh_element).values
                if len(stress_values) != 1:
                    print('Invalid stress state for element ' + instance_name + '.' + str(element_label))
                    continue
                # Fetch the old and new stress values
                old_stress = stress_set.get_stress()
                new_stress = stress_values[0].data
                # Update the stress
                stress_set.define_stress(
                    [new_stress[0], new_stress[1], new_stress[2], new_stress[3], new_stress[4], new_stress[5]])
                # Calculate and update deviation
                dev = np.sqrt(
                    (old_stress[0] - new_stress[0])*(old_stress[0] - new_stress[0])
                    + (old_stress[1] - new_stress[1]) * (old_stress[1] - new_stress[1])
                    + (old_stress[2] - new_stress[2]) * (old_stress[2] - new_stress[2])
                    + (old_stress[3] - new_stress[3]) * (old_stress[3] - new_stress[3])
                    + (old_stress[4] - new_stress[4]) * (old_stress[4] - new_stress[4])
                    + (old_stress[5] - new_stress[5]) * (old_stress[5] - new_stress[5])
                )/6
                if dev > max_dev:
                    max_dev = dev
        # return the deviation
        return max_dev

    # Internal method called on initialization
    def __on_init(self):
        # Fetch the job
        job = abaqus.mdb.jobs[self.default_job]
        # Write the default input file
        print('-> Writing default input file')
        job.writeInput()
        # Read the default input from the input file
        self.default_input = read_lines_from_file(job.name + '.inp')
        # Read the default input and inject the element sets
        self.__inject_element_sets()
        # Find the line at which to inject stress fields
        self.__find_stress_injection_line()

    # Internal method to inject element set definitions into an existing input file
    def __inject_element_sets(self):
        self.next_line = 0
        sets_to_inject = np.arange(0, len(self.mesh_data))
        current_part_index = -1
        while True:
            # fetch the current line
            line = self.default_input[self.next_line]
            # increment line index
            self.next_line = self.next_line + 1
            # check if the current mode is set injection or part scanning
            if current_part_index < 0:
                # check if the line starts a part definition
                if line[:12] == '*Part, name=':
                    current_part = line[12:]
                else:
                    continue
                # part definition reached, iterate over the remaining parts to inject
                print('-> Found input file part definition for ' + current_part)
                set_index = 0
                while set_index < len(sets_to_inject):
                    mesh_data_part = self.mesh_data[sets_to_inject[set_index]]
                    if mesh_data_part is None or mesh_data_part.get_stress_set_count() <= 0:
                        # this part has no data to inject, remove it from the parts to inject index list
                        sets_to_inject = np.delete(sets_to_inject, set_index)
                        continue
                    # fetch a single stress set
                    stress_set = mesh_data_part.get_stress_sets()[0]
                    # this part has data to inject, check if it is the current part in the input file
                    if stress_set.get_part_name() == current_part:
                        # it is the current part in the input file, set as current part being injected
                        current_part_index = sets_to_inject[set_index]
                        print('--> Injecting sets for part ' + stress_set.get_part_name())
                        # also remove it from the parts to inject index list
                        sets_to_inject = np.delete(sets_to_inject, set_index)
                        # increment the current line as it will be '*Node'
                        self.next_line = self.next_line + 1
                        break
                    else:
                        # this is a different part, leave it in the list and move to the next index
                        set_index = set_index + 1
                if current_part_index < 0:
                    print('--> Skipping ' + current_part)
            # current mode is set injection
            else:
                # if the line starts with a space, continue
                if line[0] == ' ':
                    continue
                # if the line starts with an asterisk, a new section is found
                if line[0] == '*':
                    # the next section is an element definition section
                    if line[:15] == '*Element, type=':
                        continue
                    # set injection point has been reached
                    else:
                        # Inject the element sets
                        print('--> Element set injection starts at line: ' + str(self.next_line))
                        mesh_data_part = self.mesh_data[current_part_index]
                        # Decrement next line once
                        self.next_line = self.next_line - 1
                        # Do the actual injection
                        for stress_set in mesh_data_part.get_stress_sets():
                            # Insert element set definition
                            self.default_input[self.next_line:self.next_line] = [
                                '*Elset, elset=' + stress_set.get_set_name()
                            ]
                            self.next_line = self.next_line + 1
                            # Fetch the elements
                            elements = stress_set.get_elements()
                            # Write the elements
                            line = ''
                            element_counter = 0
                            element_limit = 8
                            for i in np.arange(0, len(elements)):
                                # Fetch next element
                                element = elements[i]
                                # Add the element to the line
                                line = line + str(element.get_label()) + ','
                                element_counter = element_counter + 1
                                if element_counter == element_limit or i >= (len(elements) - 1):
                                    # Write the line
                                    self.default_input[self.next_line:self.next_line] = [line]
                                    self.next_line = self.next_line + 1
                                    # Reset the line and counter
                                    line = ''
                                    element_counter = 0
                                else:
                                    line = line + ' '
                        # Reset the current part index
                        current_part_index = -1
                        # Re-increment the next line
                        self.next_line = self.next_line + 1
                # if the line does not start with a space or asterisk, it is element definition and to be skipped
                else:
                    continue
            # check if set injection is complete
            if len(sets_to_inject) <= 0:
                # only break from the while loop if the last part is actually injected
                if current_part_index < 0:
                    break

    # Internal method to find the line at which to inject stresses
    def __find_stress_injection_line(self):
        bc_section_index = -1
        inject_index = -1
        while True:
            # fetch the current line
            line = self.default_input[self.next_line]
            # Increment the line index
            self.next_line = self.next_line + 1
            # If the BC section has not yet been found, check for it
            if bc_section_index < 0:
                if line == '** BOUNDARY CONDITIONS':
                    bc_section_index = self.next_line - 1
            # If the BC section has been found, find where it ends
            else:
                if line == '** PREDEFINED FIELDS':
                    self.predefined = True
                    continue
                if line[0:4] == '** -':
                    inject_index = self.next_line - 1
                    break
        print('--> Stress field injection starts at line: ' + str(inject_index + 1))
        self.next_line = inject_index


# utility method to read lines from file
def read_lines_from_file(file_name):
    # read the file contents
    fid = open(file_name, 'r')
    raw = fid.read().strip()
    fid.close()
    return raw.split('\n')
