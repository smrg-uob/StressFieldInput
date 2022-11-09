# StressFieldInput
A plugin for Abaqus CAE 2018 to apply arbitrary stress fields more easily

The latest version can be downloaded from the [Releases](https://github.com/smrg-uob/StressFieldInput/releases).

To install, copy all the .py files to your Abaqus plugin directory.
When done correctly, the plugin should appear in Abaqus CAE under the plugins item on the menu ribbon:

![Plugin](https://github.com/smrg-uob/StressFieldInput/blob/master/doc/plugin.png)


## Pre-Defined Fields
A pre-defined stress field can be applied to a model in Abaqus to take into account residual stresses.
Natively, Abaqus CAE supports two ways to implement pre-defined stress fields: either a global, uniform stress field, or the output from another simulation under the form of an ODB.

To define custom, arbitrary stress fields, the input files must be manipulated which can be a somewhat convoluted task.
This plugin aims to simplify this.

Of course, as residual stress fields must equilibrate with themselves and/or the boundary conditions, when running a simulation with the pre-defined stress field, the component will deform causing relaxation of the stresses, as well as other components of stress appearing.
To resolve this, one way is the scale the initial stress field by an arbitrary factor, and find the factor for which the resulting stress field, after equilibration, matches the target as closely as possible (needs citation).


## The plugin
When launching the plugin from the menu bar, the following dialog window will show up:

![User Interface](https://github.com/smrg-uob/StressFieldInput/blob/master/doc/gui_overview.png)

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
def calculate_stress(part, x, y, z):
  # Determines the stress at coordinates (x, y, z) in the given part
  # This must return a tuple of size 6 containing the stress components [S11, S22, S33, S12, S13, S23]
```
