# Cube Example
This example illustrates how to use the plugin to enforce a sinusoidally varying stress field into a cube.

Once the CAE file has been loaded in ABAQUS, select the stress script in the plugin and run it
![figure_1](https://github.com/smrg-uob/StressFieldInput/blob/main/examples/cube/Fig_Ex_Cube_1.png?raw=true)

Then, after running the plugin and opening the results, before the first increment of the equilibration step, the desired stress state has indeed been applied:
![figure_2](https://github.com/smrg-uob/StressFieldInput/blob/main/examples/cube/Fig_Ex_Cube_2.png?raw=true)

At the end of the equilibration step, the stresses that remain can be observed
