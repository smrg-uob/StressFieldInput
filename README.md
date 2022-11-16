# StressFieldInput
A plugin for Abaqus CAE 2018 to apply arbitrary stress fields more easily

The latest version can be downloaded from the [Releases](https://github.com/smrg-uob/StressFieldInput/releases).

To install, copy all the .py files to your Abaqus plugin directory.
When done correctly, the plugin should appear in Abaqus CAE under the plugins item on the menu ribbon:

![Plugin](https://github.com/smrg-uob/StressFieldInput/blob/main/doc/plugin.png)


## Pre-Defined Fields
A pre-defined stress field can be applied to a model in Abaqus to take into account residual stresses.
Natively, Abaqus CAE supports several ways to implement pre-defined stress fields. A first one is directly in CAE; which can then be defined as a global, uniform stress field, or the output from another simulation under the form of an ODB. More complicated stress fields have to be defined via the user subroutine [SIGINI](http://130.149.89.49:2080/v6.13/books/sub/ch01s01asb18.html), which allows more freedom.
A third and final way would be to manipulate the input files which can be a somewhat convoluted task.

Ultimately, as residual stress fields must equilibrate with themselves and/or the boundary conditions, when running a simulation with the pre-defined stress field, the component will deform causing relaxation of the stresses, as well as other components of stress appearing.
To resolve this, one way is the scale the initial stress field by an arbitrary factor, and find the factor for which the resulting stress field, after equilibration, matches the target as closely as possible (needs citation).
This plugin aims to make this process easier to execute.


## The plugin
When launching the plugin from the menu bar, the following dialog window will show up:

![User Interface](https://github.com/smrg-uob/StressFieldInput/blob/main/doc/gui_overview.png)

Its use is quite straightforward:
* Default Job: Requires the selection of a default job to which the stress fields will be added (this job will not be overriden or changed)
* Scale count: Defines the number of scale factors for which the stress field will be scaled, between the minimum and maximum scales defined below
* Scale min: Defines the minimum scale factor
* Scale max: Defines the maximum scale factor
* Stress script: Path to the stress script where the stress distribution is defined
* Error script: Path to the error script where the error calculation is defined (optional)
* Run jobs: If checked, the plugin will also run the jobs after creating them
* Iterate: Only available if an error script is defined. If checked, the plugin will automatically iterate to minimize the error

### The Stress Script
The arbitrary stress field is defined by a stress script which must be written and provided by the user.
This script must at minimum contain a function to calculate the stress for given coordinates in a part:
```
# Determines the stress at coordinates (x, y, z) in the assembly for the given part
def calculate_stress(part, x, y, z):
  # This must return a tuple of size 6 containing the stress components [S11, S22, S33, S12, S13, S23]
  return [0, 0, 0, 0, 0, 0]
  # Alternatively, 'None' can be returned to indicate no stress needs to be defined at this point:
  return None
```

By default, the plugin will create an element set for every single element in the input file, which can lead to rather large input files.
If multiple elements in the model would have an identical stress state, it is also possible to define categories of elements in the stress script.
To do this, a second, optional, function can be implemented:
```
# Determines the stress at coordinates (x, y, z) in the assembly for the given part
def get_category(part, x, y, z):
  # This return a unique identifier for the category the point (x, y, z) belongs to
  return <unique id>  # <unique id> can be an integer or string
  # Alternatively, 'None' can be returned to indicate no stress needs to be defined at this point:
  return None
```

If get_category is defined, the plugin will automatically divide the elements in separate element sets where each element set has the same stress state.
Subsequently, the function 'calculate_stress' will only be called for one element in each set instead of for every element.
As a result, the resulting input file can become significantly shorter, resulting in quicker input file processing times.


###  The Error Script
The error script is an optional script with the function to determine the error between the equilibrated quantities (stresses, strains, displacements, etc.) in the model and the user's desired input values.
For instance, if one would have a measured stress tensor in some points in the model, the error script could extract the resulting stresses in these points from the model and return the root mean square of the difference between the model and the experimental data.
This must be implemented in a function called `calculate_error`, which takes two arguments: a reference to an Abaqus [session](http://130.149.89.49:2080/v6.13/books/ker/pt01ch47pyo01.html), and an Abaqus [ODB](http://130.149.89.49:2080/v6.13/books/ker/pt01ch34pyo01.html):
```
# Calculates the error from an Abaqus session with output database (odb)
def calculate_error(session, odb):
  # Return a float characterizing the error of the results in the odb
  return <error>  # error should be a float  
```

The physical meaning of the error value does not matter for the plugin, the main restriction is that the error returned by this function must become smaller the closer the results in the odb approach the desired equilibrated state.
Once an error script has been defined, the 'Iterate' checkbox in the plugin's user interface will become active.


## How it works
In Abaqus input files, it is possible to define a predefined stress state for a set of elements, therefore, the plugin will identify all elements in the model's mesh , find its centre point, and create a set for each element.
Then, the user defined stress script is called for each centre point, defining the stress state for that element.

To apply these stresses, the plugin reads the input file of the default job, and injects these sets and their stress definitions into it.
One such input file is written for each stress scale factor defined in the plugin dialog box, and jobs are made from the input files.
If the run jobs option is checked, the plugin will also run these jobs in sequence.

The plugin does not make any modifications to the MDB, except for creating new jobs based on the default job.

### Iteration
Without iteration, the plugin will sweep stress scales evenly spaced between the defined minimum and maximum. For instance, if the minimum is set to 1.00, the maximum to 2.00, and the scale count to 5, the plugin will apply stress scales 1.00, 1.25, 1.50, 1.75, and 2.00.

On the other hand, if iteration is enabled (after an error script has been defined), the plugin will first calculate the error for the minimum and maximum stress scales. Then, for the third iteration, the sctress scale in the middle of these two will be calculated.
For every other iteration after that, the middle point between the last two minima will be calculated until the desired number of stress scales has been reached, as illustrated in the figure below:

![Iteration Scheme](https://github.com/smrg-uob/StressFieldInput/blob/main/doc/iteration_scheme.png)

Note that finding the minimum with this scheme is not guaranteed as it requires some knowledge of where the minimum is located beforehand, therefore it is advised to first perform a uniformly spaced sweep to get an idea of where the minimum is roughly located, followed by an iterative sweep focused around the minimum.


## Acknowledgement
Simon McKendrey for the idea of applying scale factors to the initial stresses.
