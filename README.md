# StressFieldInput
A plugin for Abaqus CAE 2018 to apply arbitrary stress fields more easily

The latest version can be downloaded from the [Releases](https://github.com/smrg-uob/StressFieldInput/releases).

To install, copy all the .py files to your Abaqus plugin directory.
When done correctly, the plugin should appear in Abaqus CAE under the plugins item on the menu ribbon:

![Plugin](https://github.com/smrg-uob/StressFieldInput/blob/main/doc/plugin.png)


## Pre-Defined Fields
A pre-defined stress field can be applied to a model in Abaqus to take into account residual stresses.
Natively, Abaqus CAE supports two ways to implement pre-defined stress fields: either a global, uniform stress field, or the output from another simulation under the form of an ODB.

To define custom, arbitrary stress fields, the input files must be manipulated which can be a somewhat convoluted task.
This plugin aims to simplify this.

Of course, as residual stress fields must equilibrate with themselves and/or the boundary conditions, when running a simulation with the pre-defined stress field, the component will deform causing relaxation of the stresses, as well as other components of stress appearing.
To resolve this, one way is the scale the initial stress field by an arbitrary factor, and find the factor for which the resulting stress field, after equilibration, matches the target as closely as possible (needs citation).


## The plugin
When launching the plugin from the menu bar, the following dialog window will show up:

![User Interface](https://github.com/smrg-uob/StressFieldInput/blob/main/doc/gui_overview.png)

Its use is quite straightforward:
* Default Job: Requires the selection of a default job to which the stress fields will be added (this job will not be overriden or changed)
* Scale count: Defines the number of scale factors for which the stress field will be scaled, between the minimum and maximum scales defined below
* Scale min: Defines the minimum scale factor
* Scale max: Defines the maximum scale factor
* Stress script: Path to the stress script where the stress distribution is defined
* Run jobs: If checked, the plugin will also run the jobs after creating them

### The Stress Script
The arbitrary stress field is defined by a stress script which must be written and provided by the user.
This script must contain a function:
```
# Determines the stress at coordinates (x, y, z) in the given part
def calculate_stress(part, x, y, z):
  # This must return a tuple of size 6 containing the stress components [S11, S22, S33, S12, S13, S23]
  return [0, 0, 0, 0, 0, 0]
```

## How it works
In Abaqus input files, it is possible to define a predefined stress state for a set of elements, therefore, the plugin will identify all elements in the model's mesh , find its centre point, and create a set for each element.
Then, the user defined stress script is called for each centre point, defining the stress state for that element.

To apply these stresses, the plugin reads the input file of the default job, and injects these sets and their stress definitions into it.
One such input file is written for each stress scale factor defined in the plugin dialog box, and jobs are made from the input files.
If the run jobs option is checked, the plugin will also run these jobs in sequence.

The plugin does not make any modifications to the MDB, except for creating new jobs based on the default job.

## Acknowledgement
Simon McKendrey for the idea of applying scale factors to the initial stresses.
