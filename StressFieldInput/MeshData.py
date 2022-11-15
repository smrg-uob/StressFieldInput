# coding=utf-8

import numpy as np
from StressSetDefinition import StressSetDefinition


class MeshData:
    def __init__(self, element_count):
        self.element_count = element_count

    def add_element(self, element, category=None):
        pass

    def define_stresses(self):
        pass

    def get_stress_set_count(self):
        pass

    def get_stress_sets(self):
        pass

    @staticmethod
    def create_mesh_data(elements, categorize):
        if categorize:
            return MeshDataCategorized(elements)
        else:
            return MeshDataByElement(elements)


class MeshDataByElement(MeshData):
    def __init__(self, element_count):
        MeshData.__init__(self, element_count)
        self.elements = np.empty(self.element_count, dtype=object)

    def add_element(self, element, category=None):
        # element labels start at 1, indices start at 0
        index = element.get_label() - 1
        self.elements[index] = element

    def get_stress_set_count(self):
        return len(self.elements)

    def get_stress_sets(self):
        return self.elements


class MeshDataCategorized(MeshData):
    def __init__(self, element_count):
        MeshData.__init__(self, element_count)
        self.categories = np.empty(self.element_count, dtype=object)
        self.category_indices_by_name = {}

    def add_element(self, element, category=None):
        # Ignore the element if the category is None
        if category is None:
            return
        # Add the category if necessary and fetch the category index
        category = str(category)
        if category in self.category_indices_by_name.keys():
            index = self.category_indices_by_name[category]
            self.categories[index].add_element(element)
        else:
            index = len(self.category_indices_by_name)
            self.category_indices_by_name[category] = index
            self.categories[index] = Category(element, self.element_count)

    def get_stress_set_count(self):
        return len(self.category_indices_by_name)

    def get_stress_sets(self):
        return self.categories[0:len(self.category_indices_by_name)]


class Category(StressSetDefinition):
    def __init__(self, name, element, element_count):
        StressSetDefinition.__init__(self)
        self.name = name
        self.elements = np.empty(element_count, dtype=object)
        # There will always be an element at index 0, so it is safe to fetch it in other methods
        self.elements[0] = element
        self.next_index = 1

    def get_name(self):
        return self.name

    def add_element(self, element):
        self.elements[self.next_index] = element
        self.next_index = self.next_index + 1

    def get_part_name(self):
        return self.elements[0].get_part_name()

    def get_instance_name(self):
        return self.elements[0].get_instance_name()

    def get_elements(self):
        return self.elements[0:self.next_index]

    def get_x(self):
        return self.elements[0].get_x()

    def get_y(self):
        return self.elements[0].get_y()

    def get_z(self):
        return self.elements[0].get_z()

    def get_set_name(self):
        return 'stress_field_group_' + self.get_name()

    def define_stress(self, stress):
        self.elements[0].define_stress(stress)

    def get_stress(self):
        return self.elements[0].get_stress()
