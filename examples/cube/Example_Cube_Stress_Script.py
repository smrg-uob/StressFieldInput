# import numpy
import numpy as npy


# In this example, a linearly varying stress state with Z is applied
# The slopes of the linear variation are read from a file
# Since the ABAQUS plugin will run this script in its entirety once, all code outside of the "calculate_stress" method
# will be ran, this, for instance can be used to read values from a file

# Define the function to read the desired values from a file
def readValuesFromFile(file_name):
    # read data from file
    fid = open(file_name, 'r')
    txt = fid.read().strip()
    fid.close()
    # remove all spaces
    txt = txt.replace(" ", "")
    # extract x slope
    val_x = extractValue(txt, "slope_x")
    # extract y slope
    val_y = extractValue(txt, "slope_y")
    # return the values
    return val_x, val_y


# Utility function to extract the target value
def extractValue(txt, target):
    i1 = txt.find(target) + len(target) + 1
    i2 = txt.find("\n", i1)
    if i2 < 0:
        i2 = len(txt)
    return float(txt[i1:i2])


# Here we initialize the values that will be used inside the "calculate_stress" method
values = readValuesFromFile('Example_Cube_Value_File.txt')
slope_x = 1E6*values[0]
slope_y = 1E6*values[1]


# The "calculate_stress" method, which is what the ABAQUS plugin will call to determine the desired stress in the model
def calculate_stress(part, x, y, z, prev_stress):
    # First, calculate the desired stress components at the given coordinates
    s_xx = slope_x*z
    s_yy = slope_y*z
    # Then, return the stress tensor (a tuple of size 6 containing the stress components [S11, S22, S33, S12, S13, S23])
    # since equilibration in previous iterations might have resulted in non-zero stresses for the other components,
    # we return all previous stress components, overwriting the target stress components we do care about
    return [s_xx, s_yy, prev_stress[2], prev_stress[3], prev_stress[4], prev_stress[5]]
