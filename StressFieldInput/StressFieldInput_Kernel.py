import abaqus
import numpy as np
import traceback
from JobBuilder import JobBuilder
from MeshElementCategory import MeshElementCategory
from MeshElementData import MeshElementData


# Main method which runs the code
def run_plugin(default_job, stress_scale_counts, stress_scale_min, stress_scale_max,
               stress_script, error_script, run_jobs, iterate):
    # Feedback message
    print('=== STRESS INPUT START ===')
    # Run checks
    if run_checks(
            default_job, stress_scale_counts, stress_scale_min, stress_scale_max, stress_script, run_jobs, iterate):
        # Characterize the mesh
        mesh_data = characterize_mesh(default_job, stress_script)
        # Do not continue if there is no mesh
        if mesh_data is None:
            print_exit_message()
            return
        # Calculate the stresses
        mesh_data = define_stresses(mesh_data, stress_script)
        if mesh_data is None:
            print_exit_message()
            return
        # Create a job builder:
        print('> Creating job definition')
        job_builder = JobBuilder(default_job, mesh_data)
        # Run the logic
        print('> Running job logic')
        stress_scales, errors = run_logic(job_builder, stress_scale_counts, stress_scale_min, stress_scale_max,
                                          run_jobs, error_script, iterate)
        print('-> Job logic completed')
        # Output the results
        output_scales_and_error(stress_scales, errors)
    # Feedback message
    print_exit_message()


# Prints the end feedback message
def print_exit_message():
    print('=== STRESS INPUT FINISHED ===')


# Method checking if all prerequisites are met before running the code
def run_checks(default_job, stress_scale_counts, stress_scale_min, stress_scale_max, stress_script, run_jobs, iterate):
    # Feedback message
    print('> Performing checks')
    print('-> Checking inputs and MDB')
    # Check for the number of stress scales
    if stress_scale_counts < 1:
        print('-> Number of stress scales should be larger than 0')
        return False
    # Check for the stress scale bounds
    if stress_scale_max < stress_scale_min:
        print('-> Minimum stress scale should be smaller or equal to the maximum stress scale')
        return False
    # Check for weird stress scale definitions
    if (stress_scale_max > stress_scale_min) and stress_scale_counts == 1:
        print('-> Unclear stress scale definition, only one count for different min and max')
        return False
    if (stress_scale_max == stress_scale_min) and stress_scale_counts > 1:
        print('-> Unclear stress scale definition, multiple counts for equal min and max')
        return False
    # Check if run_jobs is defined if iterate is defined
    if iterate and not run_jobs:
        print('-> Can not iterate without running jobs, set "Run Jobs" must be set to true')
        return False
    # Check if there are sufficient scales defined for iterating
    if iterate and stress_scale_counts < 3:
        print('-> At least 2 scale counts are needed to start iterating')
        return False
    # Check if there is an active model
    if len(abaqus.mdb.models.keys()) <= 0:
        print('-> No active model')
        return False
    # Check if there is a default job
    if default_job == '':
        print('-> No default job')
        return False
    # Check if the default job has a model
    job = abaqus.mdb.jobs[default_job]
    if not hasattr(job, 'model'):
        print('-> Invalid job, job does not have an associated model')
        return False
    # Check if the default job is valid
    if default_job not in abaqus.mdb.jobs.keys():
        print('-> Invalid default job')
        return False
    # Attempt to run the stress script
    if not check_stress_script(stress_script):
        print('-> Stress script invalid')
        return False
    # All checks passed
    print('-> Checks passed')
    return True


# Method to check if the stress script has been properly defined
def check_stress_script(stress_script):
    # Feedback message
    print('-> Checking stress script')
    # Try to run the script
    try:
        execfile(stress_script, globals())
    except Exception:
        # If it fails, return
        print('--> Stress script threw an error')
        print(traceback.format_exc())
        return False
    # Check now if the stress calculation method exists
    if 'calculate_stress' not in globals().keys():
        print('--> Function "calculate_stress" not defined in stress script')
        return False
    # Check if the method is callable
    func = globals()['calculate_stress']
    if not callable(func):
        print('--> Function "calculate_stress" not callable in stress script')
        return False
    # Check the method arguments
    import inspect
    args = inspect.getargspec(func)
    if len(args) != 4:
        print('--> Invalid arguments for "calculate_stress"; should have precisely 4: "part", "x", "y", and "z".')
    return True


# Method to characterize the mesh
def characterize_mesh(default_job, stress_script):
    # Feedback message
    print("> Characterizing mesh")
    # Run the stress script to enable access to the get_category() method at the current level
    categorize = True
    try:
        execfile(stress_script, globals())  # Pass in globals() to load the script's contents to the global dictionary
    except Exception:
        # If it fails, don't categorize
        categorize = False
    # Check if the categorization function is implemented
    if categorize:
        categorize = 'get_category' in globals().keys()
        if categorize:
            func = globals()['get_category']
            categorize = callable(func)
            if categorize:
                print('-> Function "get_category" detected in stress script')
    # Fetch the job
    job = abaqus.mdb.jobs[default_job]
    # Fetch the model from the job
    model = job.model
    if isinstance(model, basestring) or isinstance(model, str):
        # Note that according to the documentation, model can be a Model object or a String with the model name
        model = abaqus.mdb.models[model]
    # Fetch the instances in the assembly
    instances = model.rootAssembly.allInstances
    instance_count = len(instances.keys())
    # Log element data for each of the instances
    mesh_data = np.empty(instance_count, dtype=object)
    no_mesh = True
    # Iterate over the part instances
    for instance_index in np.arange(0, instance_count):
        # Fetch instance properties
        instance_key = instances.keys()[instance_index]
        instance = instances[instance_key]
        part_name = instance.part.name
        elements = instance.elements
        element_count = len(elements)
        if element_count > 0:
            # Toggle the flag
            no_mesh = False
            # Create mesh categories
            part_mesh_data = {}
            for element_index in np.arange(0, element_count):
                # Fetch the element
                element = elements[element_index]
                # fetch the label
                label = element.label
                # fetch the centre coordinates
                x = 0
                y = 0
                z = 0
                node_count = len(element.getNodes())
                for node in element.getNodes():
                    coordinates = node.coordinates
                    x = x + coordinates[0]
                    y = y + coordinates[1]
                    z = z + coordinates[2]
                x = (x + 0.0) / node_count
                y = (y + 0.0) / node_count
                z = (z + 0.0) / node_count
                # create a new mesh element data object
                element_data = MeshElementData(instance_key, part_name, label, x, y, z)
                # Identify the category
                if categorize:
                    try:
                        category = get_category(part_name, x, y, z)
                    except Exception:
                        # If categorization script fails, cancel
                        print('-> Function "get_category" failed for element ' + element.get_label() + ', aborting')
                        print(traceback.format_exc())
                        return None
                else:
                    category = element_data.get_label()
                # Store the mesh element
                if category in part_mesh_data.keys():
                    part_mesh_data[category].add_element(element_data)
                else:
                    part_mesh_data[category] = MeshElementCategory(category, element_data)
            # Store the categories
            mesh_data[instance_index] = part_mesh_data
        else:
            # Store None
            mesh_data[instance_index] = None
    if no_mesh:
        print('-> No mesh present, aborting')
        return None
    return mesh_data


# Method to define the stress data
def define_stresses(mesh_data, stress_script):
    # Run the script to enable access to the calculate_stress() method at the current level
    try:
        execfile(stress_script, globals())  # Pass in globals() to load the script's contents to the global dictionary
    except Exception:
        # If it fails, return None
        print('---> Stress script threw an error')
        print(traceback.format_exc())
        return None
    # Iterate over part instances
    for part_index in np.arange(0, len(mesh_data)):
        part_mesh_data = mesh_data[part_index]
        if part_mesh_data is None:
            continue
        # Iterate over mesh element categories
        for category_key in part_mesh_data.keys():
            # Fetch the category
            mesh_category = part_mesh_data[category_key]
            # Fetch the element
            element = mesh_category.get_first_element()
            # Calculate the stress (method will be available from the stress script)
            try:
                stress = calculate_stress(element.get_part_name(), element.get_x(), element.get_y(), element.get_z())
            except Exception:
                # If stress script fails, default to zero
                print('---> Stress script threw an error during calculation for element ' + mesh_category.get_id())
                print(traceback.format_exc())
                stress = [0, 0, 0, 0, 0, 0]
            # Define the stress
            mesh_category.define_stress(stress)
    return mesh_data


# Run plugin logic
def run_logic(job_builder, stress_scale_counts, stress_scale_min, stress_scale_max, run_jobs, error_script, iterate):
    # Initialize empty arrays for the jobs, stress scales and errors
    jobs = [None] * stress_scale_counts
    stress_scales = np.zeros(stress_scale_counts)
    errors = np.zeros(stress_scale_counts)
    # Check if error calculation is required
    run_errors = run_jobs and (error_script is not None) and (error_script != '')
    # If error calculation is required run the error script
    if run_errors:
        try:
            execfile(error_script, globals())  # Pass in globals() to load the script's contents to the global dict
        except Exception:
            # If it fails, turn off error calculation
            print('-> Error script threw an error')
            print(traceback.format_exc())
            run_errors = False
    # Split logic if error iteration is required
    if iterate:
        # Feedback message
        print('-> Iterating for minimum error')
        # Check if errors can be evaluated
        if not run_errors:
            print('--> Can not iterate without properly defined error script')
        # Define tracking variables
        current_min_index = -1
        previous_index = -1
        # Iterate
        for i in np.arange(0, stress_scale_counts):
            # Determine stress scale
            if i == 0:
                # Do the first iteration at the minimum scale factor
                stress_scales[i] = stress_scale_min
            elif i == 1:
                # Do the second iteration at the minimum scale factor
                stress_scales[i] = stress_scale_max
            else:
                # Do the third iteration at the average of the current minimum and the previous scale factors
                stress_scales[i] = (stress_scales[current_min_index] + stress_scales[previous_index])/2
            # Generate the job
            print('--> Creating job for stress factor ' + str(stress_scales[i]))
            jobs[i] = job_builder.create_job(i + 1, stress_scales[i])
            # Run the job
            print('--> Running job ' + str(i + 1) + ' of ' + str(len(jobs)))
            jobs[i].submit()
            jobs[i].waitForCompletion()
            # Calculate the errors
            print('--> Calculating error for job ' + str(i + 1) + ' of ' + str(len(jobs)))
            # open the ODB
            odb = abaqus.session.openOdb(jobs[i].name + ".odb", readOnly=True)
            # Calculate the error (method will be available from the error script)
            try:
                errors[i] = calculate_error(abaqus.session, odb)
            except Exception:
                # If an error script fails, abort
                print('---> Error script threw an error during calculation, aborting')
                print(traceback.format_exc())
                return None, None
            print('--> Error = ' + str(errors[i]))
            # Update tracking parameters
            if i == 0:
                # First iteration is straightforward
                current_min_index = 0
            elif i == 1:
                # After second iteration an initial update is needed
                if errors[i] < errors[current_min_index]:
                    current_min_index = 1
                    previous_index = 0
                else:
                    previous_index = 1
            else:
                # For further iterations keep updating
                if errors[i] < errors[current_min_index]:
                    previous_index = current_min_index
                    current_min_index = i
                else:
                    previous_index = i
    else:
        # Feedback message
        print('-> Sweeping stress scale factors')
        # Simply iterate over the scales which are evenly spaced
        for i in np.arange(0, stress_scale_counts):
            if stress_scale_counts == 1:
                stress_scale = stress_scale_min
            else:
                stress_scale = stress_scale_min + (i + 0.0) * (stress_scale_max - stress_scale_min) / (
                            stress_scale_counts - 1)
            # Generate the job
            print('--> Creating job for stress factor ' + str(stress_scale))
            jobs[i] = job_builder.create_job(i + 1, stress_scale)
            # Store the stress scale factor
            stress_scales[i] = stress_scale
        # If jobs must be ran, run the jobs:
        if run_jobs:
            print('-> Running jobs')
            for i in np.arange(0, stress_scale_counts):
                print('--> Running job ' + str(i + 1) + ' of ' + str(len(jobs)))
                jobs[i].submit()
                jobs[i].waitForCompletion()
        # If errors must be calculated, calculate the errors:
        if run_errors:
            print('-> Calculating errors')
            for i in np.arange(0, stress_scale_counts):
                # Feedback message
                print('--> Calculating error for job ' + str(i + 1) + ' of ' + str(len(jobs)))
                # open the ODB
                odb = abaqus.session.openOdb(jobs[i].name + ".odb", readOnly=True)
                # Calculate the error (method will be available from the error script)
                try:
                    errors[i] = calculate_error(abaqus.session, odb)
                except Exception:
                    # If an error script fails, set the error to -1
                    print('---> Error script threw an error during calculation')
                    print(traceback.format_exc())
                    errors[i] = -1
    if run_errors:
        return stress_scales, errors


# Writes stress scales and errors to file
def output_scales_and_error(stress_scales, errors):
    if errors is not None:
        # Print to console
        print('--> Stress scales:')
        print(stress_scales)
        print('--> Errors:')
        print(errors)
        # Compile data to write to file
        line_1 = 'Stress scale'
        line_2 = 'Errors'
        for i in np.arange(0, len(stress_scales)):
            line_1 = line_1 + ', ' + str(stress_scales[i])
            line_2 = line_2 + ', ' + str(errors[i])
        # Write to file
        f = open('stress_input_errors.txt', 'w')
        f.write(line_1 + '\n' + line_2)
        f.close()
        print('--> Scales and errors written to \"stress_input_errors.txt\"')


# Utility method to inspect an object and print its attributes and methods to the console
def inspect_object(obj):
    import inspect
    members = inspect.getmembers(obj)
    for member in members:
        print('---------------------')
        print(str(member))
    print('---------------------')
