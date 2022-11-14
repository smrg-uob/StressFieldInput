# coding=utf-8

import abaqus
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
        lines = self.default_input
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
            part_mesh_data = self.mesh_data[part_index]
            if part_mesh_data is None:
                continue
            # Iterate over the mesh element categories
            for category_key in part_mesh_data.keys():
                # fetch the category
                mesh_category = part_mesh_data[category_key]
                # Fetch the stress
                stress = mesh_category.get_stress()
                # Inject and scale in the input file
                line = mesh_category.get_instance_name() + '.' + mesh_category.get_set_name() + ','
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
                    part_element_categories = self.mesh_data[sets_to_inject[set_index]]
                    if part_element_categories is None or len(part_element_categories) <= 0:
                        # this part has no data to inject, remove it from the parts to inject index list
                        sets_to_inject = np.delete(sets_to_inject, set_index)
                    else:
                        # fetch a single category
                        part_element_category = part_element_categories[part_element_categories.keys()[0]]
                        # this part has data to inject, check if it is the current part in the input file
                        if part_element_category.get_part_name() == current_part:
                            # it is the current part in the input file, set as current part being injected
                            current_part_index = sets_to_inject[set_index]
                            print('--> Injecting sets for part ' + part_element_category.get_part_name())
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
                        part_element_categories = self.mesh_data[current_part_index]
                        # Decrement next line once
                        self.next_line = self.next_line - 1
                        # Do the actual injection
                        for category_key in part_element_categories.keys():
                            # Fetch the category
                            element_category = part_element_categories[category_key]
                            # Insert element set definition
                            self.default_input[self.next_line:self.next_line] = [
                                '*Elset, elset=' + element_category.get_set_name()
                            ]
                            self.next_line = self.next_line + 1
                            # Fetch the elements
                            elements = element_category.get_elements()
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
