# coding=utf-8


# Class to categorize mesh elements data
class MeshElementCategory:
    def __init__(self, id, element_data):
        self.id = id
        self.elements = [element_data]
        self.stress = [0, 0, 0, 0, 0, 0]

    def get_id(self):
        return self.id

    def get_instance_name(self):
        return self.get_first_element().get_instance_name()

    def get_part_name(self):
        return self.get_first_element().get_part_name()

    def add_element(self, element_data):
        self.elements.append(element_data)

    def get_elements(self):
        return self.elements

    def get_first_element(self):
        return self.elements[0]

    def get_set_name(self):
        return 'stress_field_group_' + str(self.get_id())

    def define_stress(self, stress):
        self.stress = stress

    def get_stress(self):
        return self.stress
