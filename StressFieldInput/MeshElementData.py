# coding=utf-8


# Class to track mesh element data
class MeshElementData:
    def __init__(self, instance, part, label, x, y, z):
        self.instance = instance
        self.part = part
        self.label = label
        self.x = x
        self.y = y
        self.z = z

    def get_instance_name(self):
        return self.instance

    def get_part_name(self):
        return self.part

    def get_label(self):
        return self.label

    def get_x(self):
        return self.x

    def get_y(self):
        return self.y

    def get_z(self):
        return self.z

    def get_set_name(self):
        return 'stress_field_el_' + str(self.get_label())
