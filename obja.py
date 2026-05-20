#!/usr/bin/env python3

import sys
import numpy as np
import random
from enum import Enum

class State(Enum):
    Free = 1
    Conquered = 2
    To_be_removed = 3

"""
obja model for python.
"""

class Face:
    """
    The class that holds a, b, and c, the indices of the vertices of the face.
    """

    def __init__(self, a, b, c, visible=True,state = State.Free):
        self.a = a
        self.b = b
        self.c = c
        self.visible = visible
        self.state = state   # ajout du state pour les faces

    def from_array(array):
        """
        Initializes a face from an array of strings representing vertex indices (starting at 1)
        """
        face = Face(0, 0, 0)
        face.set(array)
        face.visible = True
        return face
    
    def from_array_num(array):
        face = Face(array[0],array[1],array[2])
        face.visible = True
        return face

    def set(self, array):
        """
        Sets a face from an array of strings representing vertex indices (starting at 1)
        """
        self.a = int(array[0].split('/')[0]) - 1
        self.b = int(array[1].split('/')[0]) - 1
        self.c = int(array[2].split('/')[0]) - 1
        return self

    def clone(self):
        """
        Clones a face from another face
        """
        return Face(self.a, self.b, self.c, self.visible, self.state)

    def copy(self, other):
        """
        Sets a face from another face
        """
        self.a = other.a
        self.b = other.b
        self.c = other.c
        self.visible = other.visible
        self.state = other.state
        return self

    def test(self, vertices, line="unknown"):
        """
        Tests if a face references only vertices that exist when the face is declared.
        """
        if self.a >= len(vertices):
            raise VertexError(self.a + 1, line)
        if self.b >= len(vertices):
            raise VertexError(self.b + 1, line)
        if self.c >= len(vertices):
            raise VertexError(self.c + 1, line)

    def __str__(self):
        return "Face({}, {}, {})".format(self.a, self.b, self.c)

    def __repr__(self):
        return str(self)
    def equality_content(self,other):
        return (self.a == other.a and self.b == other.b and self.c == other.c) or (self.a == other.b and self.b == other.c and self.c == other.a) or (self.a == other.c and self.b == other.a and self.c == other.b)

class VertexError(Exception):
    """
    An operation references a vertex that does not exist.
    """

    def __init__(self, index, line):
        """
        Creates the error from index of the referenced vertex and the line where the error occured.
        """
        self.line = line
        self.index = index
        super().__init__()

    def __str__(self):
        """
        Pretty prints the error.
        """
        return f"There is no vertex {self.index} (line {self.line})"


class FaceError(Exception):
    """
    An operation references a face that does not exist.
    """

    def __init__(self, index, line):
        """
        Creates the error from index of the referenced face and the line where the error occurred.
        """
        self.line = line
        self.index = index
        super().__init__()

    def __str__(self):
        """
        Pretty prints the error.
        """
        return f'There is no face {self.index} (line {self.line})'


class FaceVertexError(Exception):
    """
    An operation references a face vertex that does not exist.
    """

    def __init__(self, index, line):
        """
        Creates the error from index of the referenced face vertex and the line where the error occured.
        """
        self.line = line
        self.index = index
        super().__init__()

    def __str__(self):
        """
        Pretty prints the error.
        """
        return f'Face has no vertex {self.index} (line {self.line})'


class UnknownInstruction(Exception):
    """
    An instruction is unknown.
    """

    def __init__(self, instruction, line):
        """
        Creates the error from instruction and the line where the error occured.
        """
        self.line = line
        self.instruction = instruction
        super().__init__()

    def __str__(self):
        """
        Pretty prints the error.
        """
        return f'Instruction {self.instruction} unknown (line {self.line})'
class FindGateLooping(Exception):
    def __init__(self):
        super().__init__()

    def __str__(self):
        """
        Pretty prints the error.
        """
        return f"Find gate looping"

class NotGate2Face(Exception):
    def __init__(self, gate1, gate2, model):
        self.gate1 = gate1
        self.gate2 = gate2
        self.model = model
        super().__init__()
    def __str__(self):
        """
        Pretty prints the error.
        """
        self.model.print_single_vertex(self.gate1)
        self.model.print_single_vertex(self.gate2)
        print("Common faces:")
        for index_face in self.model.vertices[self.gate1].faces:
            if index_face in self.model.vertices[self.gate2].faces:
                self.model.print_single_face(index_face)
        self.model.save_f_by_f("Exception_NotGate2Face.obj")
        return "The two vertex given (index {} and {}) doesn't correspond to a gate.".format(self.gate1,
                                                                                   self.gate2)
class Vertex:
    def __init__(self,index,coordinates,face = [],state=State.Free,retriangulation_type=0,visible=True,color=None):
        self.index = index
        self.coordinates = coordinates
        self.faces = face.copy()
        self.state = state                               # see class State
        self.retriangulation_type = retriangulation_type # +1 => + and -1 => - and 0 => nothing...
        self.visible = visible
        self.color = color

    def clone(self):

        return Vertex( self.index, self.coordinates, self.faces, self.state, self.retriangulation_type, self.visible, self.color)
        

    def coloring_vertex(self,color):
        if len(color) != 3:
            raise Exception("Wrong input for coloring")
        elif self.color:
            self.color[0] = color[0]
            self.color[1] = color[1]
            self.color[2] = color[2]
        else:
            self.color = [color[0],color[1],color[2]]
    
    def equality(self,other):
        return self.index == other.index
    def equality_content(self,other):
        return np.array_equal(self.coordinates, other.coordinates) and len(self.faces) == len(other.faces) #and self.state == other.state and self.retriangulation_type == other.retriangulation_type
        

class Model:
    """
    The OBJA model.
    """

    def __init__(self):
        """
        Initializes an empty model.
        """
        self.vertices = []
        self.faces = []
        self.line = 0


    def memorize_face(self,face):
        self.faces.append(face)
        index_face = len(self.faces) - 1
        self.vertices[face.a].faces.append(index_face)
        self.vertices[face.b].faces.append(index_face)
        self.vertices[face.c].faces.append(index_face)
        return index_face
        
    
    def set_everything_to_free(self):
        for face in self.faces:
            face.state = State.Free
        for vertex in self.vertices:            
            vertex.state = State.Free
            
    def set_everything_to_zeros(self):
        for vertex in self.vertices:
            vertex.retriangulation_type = 0   
        

    def get_vertex_from_string(self, string):
        """
        Gets a vertex from a string representing the index of the vertex, starting at 1.

        To get the vertex from its index, simply use model.vertices[i].
        """
        index = int(string) - 1
        if index >= len(self.vertices):
            raise FaceError(index + 1, self.line)
        return self.vertices[index].coordinates

    def get_face_from_string(self, string):
        """
        Gets a face from a string representing the index of the face, starting at 1.

        To get the face from its index, simply use model.faces[i].
        """
        index = int(string) - 1
        if index >= len(self.faces):
            raise FaceError(index + 1, self.line)
        print(index)
        print(self.faces[index])
        return self.faces[index]
    
    def remove_face(self,index):
        if index >= len(self.faces):
            raise FaceError(index + 1, self.line)
        face = self.faces[index]
        self.vertices[face.a].faces.remove(index)
        self.vertices[face.b].faces.remove(index)
        self.vertices[face.c].faces.remove(index)
        self.faces[index].visible = False       #Removing the face completly will modify the indexation of the faces and maybe will create a shift between faces and rest

    def parse_file(self, path):
        """
        Parses an OBJA file.
        """
        with open(path, "r") as file:
            for line in file.readlines():
                self.parse_line(line)

    def parse_line(self, line):
        """
        Parses a line of obja file.
        """
        self.line += 1

        split = line.split()

        if len(split) == 0:
            return

        if split[0] == "v":

            self.vertices.append(Vertex(len(self.vertices),np.array(split[1:], np.double)))
            # Maybe modify the +2... => need to remove the +2
        elif split[0] == "ev":
            self.get_vertex_from_string(split[1]).set(split[2:])

        elif split[0] == "tv":
            self.get_vertex_from_string(split[1]).translate(split[2:])

        elif split[0] == "f" or split[0] == "tf":
            for i in range(1, len(split) - 2):
                face = Face.from_array(split[i:i + 3])
                face.test(self.vertices, self.line)
                self.memorize_face(face)

        elif split[0] == "ts":
            for i in range(1, len(split) - 2):
                if i % 2 == 1:
                    face = Face.from_array([split[i], split[i + 1], split[i + 2]])
                else:
                    face = Face.from_array([split[i], split[i + 2], split[i + 1]])
                face.test(self.vertices, self.line)
                self.memorize_face(face)

        elif split[0] == "ef":
            self.get_face_from_string(split[1]).set(split[2:])

        elif split[0] == "efv":
            face = self.get_face_from_string(split[1])
            vertex = int(split[2])
            new_index = int(split[3]) - 1
            if vertex == 1:
                self.vertices[face.a].faces.remove(split[1])
                face.a = new_index
                self.vertices[face.a].faces.append(split[1])
            elif vertex == 2:
                self.vertices[face.b].faces.remove(split[1])
                face.b = new_index
                self.vertices[face.b].faces.append(split[1])
            elif vertex == 3:
                self.vertices[face.c].faces.remove(split[1])
                face.c = new_index
                self.vertices[face.c].faces.append(split[1])
            else:
                raise FaceVertexError(vertex, self.line)

        elif split[0] == "df":
            self.get_face_from_string(split[1]).visible = False

        elif split[0] == "#":
            return

        else:
            return

    """
    Utility functions:
    """

    def clone(self):
        Clone = Model()
        for vertex in self.vertices:
            Clone.vertices.append(vertex.clone())
        for face in self.faces:
            Clone.faces.append(face.clone())
        return Clone
    
    def copy(self,other):
        self.line = other.line
        self.vertices = []
        self.faces = []
        for vertex in other.vertices:
            self.vertices.append(vertex.clone())
        for face in other.faces:
            self.faces.append(face.clone())
        return self
    
    def equal(self,other):
        # if self.line != other.line:
        #    return False
        for vertex_self in self.vertices:
            match_pass = False
            if len(vertex_self.faces) > 0:
                for vertex_other in other.vertices:
                    match_pass = match_pass or vertex_self.equality_content(vertex_other)
                if not(match_pass):
                    return False
        for face_self in self.faces:
            match_pass = False
            if face_self.visible:
                for face_other in other.faces:
                    if face_other.visible:
                        match_pass = match_pass or face_self.equality_content(face_other)
                if not(match_pass):
                    return False
        return True
        

    def presence_of_valence_of(self,valency):
        for vertex in self.vertices:
            if len(vertex.faces)==valency:
                return True
        return False

    def face_same_vertex_2_times(self):
        for face in self.faces:
            if face.visible:
                if face.a == face.b or face.a == face.c or face.b == face.c:
                    return True
        return False


    # Function to save the model into a obja file by doing faces by faces
    def save_f_by_f(self, output_name):
        # Open the output file
        with open(output_name, 'w') as output:
            # Create obja object
            output_model = Output(output, random_color=False)
            # First put all vertex present
            index_vertex_created = []
            for index_face in range(len(self.faces)):
                face = self.faces[index_face]
                if not(face.visible):
                    continue
                if not(face.a in index_vertex_created):
                    if self.vertices[face.a].color:
                        output_model.add_colored_vertex(face.a, self.vertices[face.a].coordinates, self.vertices[face.a].color)
                    else:
                        output_model.add_vertex(face.a, self.vertices[face.a].coordinates)
                    index_vertex_created.append(face.a)
                if not(face.b in index_vertex_created):
                    if self.vertices[face.b].color:
                        output_model.add_colored_vertex(face.b, self.vertices[face.b].coordinates, self.vertices[face.b].color)
                    else:
                        output_model.add_vertex(face.b, self.vertices[face.b].coordinates)
                    index_vertex_created.append(face.b)
                if not(face.c in index_vertex_created):
                    if self.vertices[face.c].color:
                        output_model.add_colored_vertex(face.c, self.vertices[face.c].coordinates, self.vertices[face.c].color)
                    else:
                        output_model.add_vertex(face.c, self.vertices[face.c].coordinates)
                    index_vertex_created.append(face.c)
                output_model.add_face(index_face, face)

        # Function to save the model into a obja file by doing faces by faces
    def save_v_and_f(self, output_name):
        # Open the output file
        with open(output_name, 'w') as output:
            # Create obja object
            output_model = Output(output, random_color=False)
            # First put all vertex present
            index_vertex_created = []
            for index_vertex in range(len(self.vertices)):
                vertex = self.vertices[index_vertex]
                if vertex.color:
                    output_model.add_colored_vertex(index_vertex, vertex.coordinates,
                                                    vertex.color)
                else:
                    output_model.add_vertex(index_vertex, vertex.coordinates)
                index_vertex_created.append(index_vertex)


            for index_face in range(len(self.faces)):
                face = self.faces[index_face]
                if not (face.visible):
                    continue
                if not (face.a in index_vertex_created):
                    raise Exception("Vertex {} not created".format(face.a))
                elif not (face.b in index_vertex_created):
                    raise Exception("Vertex {} not created".format(face.b))
                elif not (face.c in index_vertex_created):
                    raise Exception("Vertex {} not created".format(face.c))
                else:
                    output_model.add_face(index_face, face)

    def save_selected_f(self,output_name,list_index_f):
        # Open the output file
        with open(output_name, 'w') as output:
            # Create obja object
            output_model = Output(output, random_color=False)
            # First put all vertex present
            index_vertex_created = []
            for index_face in list_index_f:
                face = self.faces[index_face]
                if not (face.visible):
                    continue
                if not (face.a in index_vertex_created):
                    if self.vertices[face.a].color:
                        output_model.add_colored_vertex(face.a, self.vertices[face.a].coordinates,
                                                        self.vertices[face.a].color)
                    else:
                        output_model.add_vertex(face.a, self.vertices[face.a].coordinates)
                    index_vertex_created.append(face.a)
                if not (face.b in index_vertex_created):
                    if self.vertices[face.b].color:
                        output_model.add_colored_vertex(face.b, self.vertices[face.b].coordinates,
                                                        self.vertices[face.b].color)
                    else:
                        output_model.add_vertex(face.b, self.vertices[face.b].coordinates)
                    index_vertex_created.append(face.b)
                if not (face.c in index_vertex_created):
                    if self.vertices[face.c].color:
                        output_model.add_colored_vertex(face.c, self.vertices[face.c].coordinates,
                                                        self.vertices[face.c].color)
                    else:
                        output_model.add_vertex(face.c, self.vertices[face.c].coordinates)
                    index_vertex_created.append(face.c)
                output_model.add_face(index_face, face)
    def print_faces(self):
        for index_face in range(len(self.faces)):
            face = self.faces[index_face]
            print("Face of index {}, composed of:\n\t- a: {} of valence {}\n\t- b: {} of valence {}\n\t- c: {} of valence {}\n\t- visibility: {}\n\t- state: {}".format(index_face,face.a,len(self.vertices[face.a].faces),face.b,len(self.vertices[face.b].faces),face.c,len(self.vertices[face.c].faces),face.visible,face.state))
            
    def print_vertices(self):
        for index_vertex in range(len(self.vertices)):
            vertex = self.vertices[index_vertex]
            print("Vertex :\n\t- index in model: {}\n\t- index in vertex: {}\n\t- coordinates: {}\n\t- faces: {}\n\t- state: {}\n\t- retriangulation type: {}\n\t- visibility: {}\n\t- color: {}".format(index_vertex,vertex.index,vertex.coordinates,vertex.faces,vertex.state,vertex.retriangulation_type,vertex.visible,vertex.color))

    def print_single_face(self,index):
        face = self.faces[index]
        print("Face of index {}, composed of:\n\t- a: {}\n\t- b: {}\n\t- c: {}\n\t- visibility: {}\n\t- state: {}".format(index,face.a,face.b,face.c,face.visible,face.state))
    
    def print_single_vertex(self,index):
        vertex = self.vertices[index]
        print("Vertex :\n\t- index in model: {}\n\t- index in vertex: {}\n\t- coordinates: {}\n\t- faces: {}\n\t- state: {}\n\t- retriangulation type: {}\n\t- visibility: {}\n\t- color: {}".format(index,vertex.index,vertex.coordinates,vertex.faces,vertex.state,vertex.retriangulation_type,vertex.visible,vertex.color))

    def print_count_valencies(self,Specify=None):
        counts = []
        for vertex in self.vertices:
            while len(counts) <= len(vertex.faces):
                counts.append(0)
            counts[len(vertex.faces)] += 1
        if Specify:
            print("Count of vertex for valence {}: {}".format(Specify,counts[Specify]))
        else:
            print("Count of vertex per valencies:")
            for valence in range(len(counts)):
                print("\t- {}: {}".format(valence,counts[valence]))
        

    def coloring_vertex_based_type_retriang(self):
        colors = [(0,0,1),(0,1,0),(1,0,0)] # type_retriangulation + 1 = index => [-,0,+]
        for vertex in self.vertices:
            vertex.coloring_vertex(colors[vertex.retriangulation_type+1])

    def coloring_vertex_based_valencies(self):
        import color_generator
        # Code maybe not optimized but reuse already done code
        counts = []
        for vertex in self.vertices:
            while len(counts) <= len(vertex.faces):
                counts.append(0)
            counts[len(vertex.faces)] += 1
        colors = color_generator.generate_N_RGB_colors(len(counts))
        for vertex in self.vertices:
            vertex.coloring_vertex(colors[len(vertex.faces)])
    def coloring_list_vertices(self,list_index,color):
        for index in list_index:
            self.vertices[index].coloring_vertex(color)

    def coloring_vertex_all_similar(self,color):
        for vertex in self.vertices:
            vertex.coloring_vertex(color)

    def triangulation_null_patch(self,index0,index1,index_front_vertex):
        if (self.vertices[index0].retriangulation_type==1) and (self.vertices[index1].retriangulation_type==-1):
            self.vertices[index_front_vertex].retriangulation_type=1
        elif (self.vertices[index0].retriangulation_type==-1) and (self.vertices[index1].retriangulation_type==1):
            self.vertices[index_front_vertex].retriangulation_type=1
        elif (self.vertices[index0].retriangulation_type==1) and (self.vertices[index1].retriangulation_type==1):
            self.vertices[index_front_vertex].retriangulation_type=-1
        elif (self.vertices[index0].retriangulation_type==-1) and (self.vertices[index1].retriangulation_type==-1):
            self.vertices[index_front_vertex].retriangulation_type=1
        else : 
            raise Exception("Unexpected retriangulation_type for null_patch")  

         

    def find_the_gate_index(self, vertice_center,current_gate, init_gate = None ,count = 0):
        """
        Recursive function to find gates when the front vertex is to be removed.

        Parameters:
        - vertice_center: The front vertex of the current gate.
        - current_gate: The current gate being explored.
        - init_gate: The initial gate used as a reference to stop the recursion.

        """
        count += 1
        # Set the initial gate
        if init_gate is None:
            init_gate = [current_gate[1],current_gate[0]] 
            # inverse in the self.gate all gate orientation as well as the init 
            # => except of the first gate (init), all gate need to point in the future outside of the batch
            current_gate = init_gate
        
        # find the next_gate
        gate_face = self.gate_to_face(vertice_center, current_gate[0])
        new_gate = [gate_face[3],gate_face[2]] # Inversing the gate orientation

        # Check if the vertices of the new gate have state 2 and if it is different from the initial gate
        if not(new_gate[0].state == State.Conquered  and new_gate[1].state == State.Conquered)  and init_gate != new_gate : 
            new_gate[0].state = State.Conquered  
            new_gate[1].state = State.Conquered 
            n_gate = [new_gate[0].index,new_gate[1].index]
            self.gate.append(n_gate)

        # Check if the new gate is different from the initial gate to avoid infinite recursion
        if not(init_gate[0].equality(new_gate[0]) and init_gate[1].equality(new_gate[1])) and count<20 :
            self.find_the_gate_index(vertice_center,new_gate, init_gate,count)
        if count>=20:
            #_f_by_f('Results_tests/problem_find_gate.obj')
            raise Exception("ça tourne en boucle")
        
        
    def gate_to_face(self, gate_vertex1, gate_vertex2):
        # Visit all faces from the 1st vertex to see if any face is shared in the right order with the 2nd vertex
        # Return the face index and the three vertices of the face that have the gate, and a value indicating the position of the third vertex (1 for a, 2 for b and 3 for c)
        return_component = []
        counting = 0
        for index_face in gate_vertex1.faces:
            if self.faces[index_face].a == gate_vertex1.index and self.faces[index_face].b == gate_vertex2.index:
                return_component = [index_face,gate_vertex1,gate_vertex2,self.vertices[self.faces[index_face].c],3]
                counting += 1
            elif self.faces[index_face].b == gate_vertex1.index and self.faces[index_face].c == gate_vertex2.index:
                return_component = [index_face,gate_vertex1,gate_vertex2,self.vertices[self.faces[index_face].a],1]
                counting += 1
            elif self.faces[index_face].c == gate_vertex1.index and self.faces[index_face].a == gate_vertex2.index:
                return_component = [index_face,gate_vertex1,gate_vertex2,self.vertices[self.faces[index_face].b],2]
                counting += 1
        if counting == 1:
            return return_component
        else:
            raise NotGate2Face(gate_vertex1.index,gate_vertex2.index,self)
    
    def create_face(self,indices):
        face = Face.from_array_num(indices)
        face.state = State.Conquered
        face.test(self.vertices, self.line)
        index_face = self.memorize_face(face)
        return index_face


def parse_file(path):
    """
    Parses a file and returns the model.
    """
    model = Model()
    model.parse_file(path)
    return model


class Output:
    """
    The type for a model that outputs as 
    """

    def __init__(self, output, random_color=False):
        """
        Initializes the index mapping dictionaries.
        """
        self.vertex_mapping = dict()
        self.face_mapping = dict()
        self.output = output
        self.random_color = random_color

    def add_vertex(self, index, vertex):
        """
        Adds a new vertex to the model with the specified index.
        """
        self.vertex_mapping[index] = len(self.vertex_mapping)
        print('v {} {} {}'.format(vertex[0], vertex[1], vertex[2]), file=self.output)

    def add_colored_vertex(self,index,vertex,color):
        """
        Adds a new colored vertex to the model with the specified index.
        """
        self.vertex_mapping[index] = len(self.vertex_mapping)
        print('v {} {} {} {} {} {}'.format(vertex[0], vertex[1], vertex[2], color[0], color[1], color[2]), file=self.output)

    def edit_vertex(self, index, vertex):
        """
        Changes the coordinates of a vertex.
        """
        if len(self.vertex_mapping) == 0:
            print('ev {} {} {} {}'.format(index, vertex[0], vertex[1], vertex[2]), file=self.output)
        else:
            print('ev {} {} {} {}'.format(self.vertex_mapping[index] + 1, vertex[0], vertex[1], vertex[2]),
                  file=self.output)

    def add_face(self, index, face):
        """
        Adds a face to the model.
        """
        self.face_mapping[index] = len(self.face_mapping)
        print('f {} {} {}'.format(
            self.vertex_mapping[face.a] + 1,
            self.vertex_mapping[face.b] + 1,
            self.vertex_mapping[face.c] + 1,
        ),
            file=self.output
        )

        if self.random_color:
            print('fc {} {} {} {}'.format(
                len(self.face_mapping),
                random.uniform(0, 1),
                random.uniform(0, 1),
                random.uniform(0, 1)),
                file=self.output
            )
    def color_face(self,index,color):
        print('fc {} {} {} {}'.format(
                self.face_mapping[index] + 1,
                color[0],
                color[1],
                color[2]),
                file=self.output
            )
    def edit_face(self, index, face):
        """
        Changes the indices of the vertices of the specified face.
        """
        print('ef {} {} {} {}'.format(
            self.face_mapping[index] + 1,
            self.vertex_mapping[face.a] + 1,
            self.vertex_mapping[face.b] + 1,
            self.vertex_mapping[face.c] + 1
        ),
            file=self.output
        )

    def edit_face_one_vertex(self, index, position, index_vertex):
        """
        Changes the indices of a specific vertex (position in {1,2,3}) of the specified face.
        """
        print('efv {} {} {}'.format(
            self.face_mapping[index] + 1,
            position,
            self.vertex_mapping[index_vertex] + 1
        ),
            file=self.output
        )
    def remove_face(self,index):
        print('df {} '.format(
            self.face_mapping[index] + 1
        ),
            file=self.output
        )


def main():
    if len(sys.argv) == 1:
        print("obja needs a path to an obja file")
        return

    model = parse_file(sys.argv[1])
    model.complete_model()

    print(model.vertices)
    print(model.faces)
    print(model.fov)
    print(model.state_flags)
    print(model.retirangulation_tags)



if __name__ == "__main__":
    main()
    
