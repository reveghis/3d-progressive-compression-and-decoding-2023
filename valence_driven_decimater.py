import obja
import numpy as np
import sys
import random
from collections import deque, Counter
from reconstruction import Reconstructer
from utility import limit_value
import copy
import os

class Vertex_removed():
    def __init__(self,index,valence,coordinates,index_vertex1_of_gate,index_vertex2_of_gate):
        self.index = index
        self.valence = valence
        self.coordinates = coordinates
        self.gate = [index_vertex1_of_gate,index_vertex2_of_gate]
    def __init__(self,vertex,gate):
        self.index = vertex.index
        self.valence = len(vertex.faces)
        self.coordinates = vertex.coordinates
        self.gate = [gate[0].index,gate[1].index]
    
class Decimating_output():
    def __init__(self,num_iteration,init_gate_decimating,init_gate_cleaning,output_val_A,output_val_B):
        self.num_iteration = num_iteration
        self.init_gate_decimating = init_gate_decimating
        self.init_gate_cleaning = init_gate_cleaning
        self.output_val_A = output_val_A
        self.output_val_B = output_val_B
        

class None_respect_cond(Exception):
    """
    An operation references a face vertex that does not exist.
    """

    def __init__(self, case):
        """
        Creates the error from index of the referenced face vertex and the line where the error occured.
        """
        self.case = case
        super().__init__()

    def __str__(self):
        """
        Pretty prints the error.
        """
        return f'No faces respect conditions for {self.case}'
        
class Decimater(obja.Model):
    """

    """
    def __init__(self,random_seed=0):
        super().__init__()
        self.deleted_faces = set()
        self.gate = deque()
        self.list_removed = []
        self.random_seed = random_seed
        self.count = 0
        self.nb_decimate = 0
        self.ind_4_inds_f = -1

    def print_gate_index(self):
        print("List index vertices on gates: ", end="")
        for gate in self.gate:
            print("({},{}) ".format(gate[0].index,gate[1].index),end="")
        print()

    def increase_rd_seed(self):        
        self.random_seed += 1
        random.seed(self.random_seed)
    
    
    def cleaning_conquest(self):

    #Cleaning Conquest function for removing redundant vertices and faces in a triangle mesh.

    # Cleaning Conquest is a series of operations performed after removing redundant vertices in a triangle mesh.
    #Its main goal is to ensure that the simplified mesh maintains validity and reasonable topological structure.

    #Parameters:
    #- self: Decimater object containing the triangle mesh model and related data.

    #Returns:

  
        index_c_gate = self.gate.popleft()

        c_gate = [self.vertices[index_c_gate[0]],self.vertices[index_c_gate[1]]]
            
        # Find information about the front face
        front_face_information = self.gate_to_face(c_gate[0], c_gate[1])
        #self.print_single_face(front_face_information[0])
        front_vertex = front_face_information[3]
        front_face = self.faces[front_face_information[0]]
        
        self.coloring_vertex_all_similar([0.5,0.5,0.5])
        c_gate[0].coloring_vertex([0,1,0])
        c_gate[1].coloring_vertex([0,0,1])
        front_face_information[3].coloring_vertex([1,0,0]) 
        self.count += 1       
        
        # if its front face is tagged conquered or to be removed
        if front_face.state == obja.State.Conquered or front_face.state == obja.State.To_be_removed:
            return None


        elif len(front_vertex.faces) == 3 and front_vertex.state == obja.State.Free   :

            # Mark the front face for removal
            front_face.state = obja.State.To_be_removed
            
            # find the edge of the patch
            face_up_right = self.gate_to_face(front_vertex,c_gate[1])
            face_up_left = self.gate_to_face(front_vertex, face_up_right[3])

            # Mark the other face for removal
            self.faces[face_up_right[0]].state = obja.State.To_be_removed
            self.faces[face_up_left[0]].state = obja.State.To_be_removed

            # Create two intermediare gates
            intermediaire_gates = [ [face_up_right[3], c_gate[1]] , [face_up_left[3], face_up_right[3]] ]
            # find the other gates 
            for gate in intermediaire_gates:
                gate[0].state = obja.State.Conquered
                gate[1].state = obja.State.Conquered
                f = self.gate_to_face(gate[0],gate[1])

                # Create the two new gates
                new_gates = [[f[3].index,f[2].index], [f[1].index, f[3].index]]

                # Add the new gates to the queue
                
             
                for gate in new_gates:
                    self.vertices[gate[0]].state = obja.State.Conquered 
                    self.vertices[gate[1]].state = obja.State.Conquered
                    self.gate.append(gate)
                self.faces[f[0]].state = obja.State.Conquered

                
            
            front_vertex.state = obja.State.To_be_removed
            return Vertex_removed(front_vertex,c_gate)

        elif front_vertex.state == obja.State.Free or front_vertex.state == obja.State.Conquered :
            # Mark the front face as conquered
            front_face.state = obja.State.Conquered

            # creates the 2 new gate 
            new_gates = [[front_face_information[3].index,front_face_information[2].index],[front_face_information[1].index,front_face_information[3].index]]
            # add the gates to the fifo
            for gate in new_gates:
                self.vertices[gate[0]].state = obja.State.Conquered 
                self.vertices[gate[1]].state = obja.State.Conquered
                self.gate.append(gate)

            return "Null_patch"



    def retriangulation_4_cleaning_conquest(self,vertex_to_be_removed):
        border_patch = vertex_to_be_removed.gate.copy() # List of all vertices around the vertex to be removed
        vertex_infos = self.vertices[vertex_to_be_removed.index]    # A variable to access directly info to avoid too much code
        while vertex_infos.faces:   # While there is faces to be removed from the "vertex to be removed", we search them
            for index_face in vertex_infos.faces:   # Visit all faces of the vertex to be removed to see if any face correspond to the next in the chain around
                # Normally with the order of face to be removed should be in the counterclock order, starting with the face next to the gate face
                # The gate face should be the last one to be removed
                # If any face having the center following by the last adding into the chain as a "gate", then this is the next face, and so the third vertex the next vertex in the chain
                # Knowing the chain order is required because removing faces will loose the patch organization information and so we need to memorize it for the retriangulation
                # When found, added the vertex and remove the face, we break the for loop to research again if required
                if self.faces[index_face].a == vertex_to_be_removed.index and self.faces[index_face].b == border_patch[-1]:
                    border_patch.append(self.faces[index_face].c)
                    self.remove_face(index_face)
                    break 
                elif self.faces[index_face].b == vertex_to_be_removed.index and self.faces[index_face].c == border_patch[-1]:
                    border_patch.append(self.faces[index_face].a)
                    self.remove_face(index_face)
                    break
                elif self.faces[index_face].c == vertex_to_be_removed.index and self.faces[index_face].a == border_patch[-1]:
                    border_patch.append(self.faces[index_face].b)
                    self.remove_face(index_face)
                    break
            
            #raise Exception("Not found next vertex in the chain around")
        if len(border_patch) != vertex_to_be_removed.valence + 2:   
            # Through this process, since the gate face will be the last processed, the two vertices of the gates will be added in the chain and so being two time in it
            # (Once added when the left face of the gate face will be removed for the left gate vertex, and once the gate face is removed for the right gate vertex)
            # Therefore, the border_patch is required to have two more
            raise Exception("Unexpected valence or border_patch size (!=)")
        else:
            border_patch.pop() # remove the right gate vertex last adding
            border_patch.pop() # remove the left gate vertex last adding


        # Creating faces
        self.create_face([self.vertices[border_patch[0]].index,self.vertices[border_patch[1]].index,self.vertices[border_patch[2]].index])
        vertex_infos.visible = False
        return border_patch

           
 
    def retriangulation(self,vertex_to_be_removed):

        border_patch = vertex_to_be_removed.gate.copy() # List of all vertices around the vertex to be removed
        vertex_infos = self.vertices[vertex_to_be_removed.index]    # A variable to access directly info to avoid too much code
        while vertex_infos.faces:   # While there is faces to be removed from the "vertex to be removed", we search them
            not_breaking = True
            for index_face in vertex_infos.faces:   # Visit all faces of the vertex to be removed to see if any face correspond to the next in the chain around
                # Normally with the order of face to be removed should be in the counterclock order, starting with the face next to the gate face
                # The gate face should be the last one to be removed
                # If any face having the center following by the last adding into the chain as a "gate", then this is the next face, and so the third vertex the next vertex in the chain
                # Knowing the chain order is required because removing faces will loose the patch organization information and so we need to memorize it for the retriangulation
                # When found, added the vertex and remove the face, we break the for loop to research again if required

                if self.faces[index_face].a == vertex_to_be_removed.index and self.faces[index_face].b == border_patch[-1]:
                    border_patch.append(self.faces[index_face].c)
                    
                    self.remove_face(index_face)
                    not_breaking = False
                    break 
                elif self.faces[index_face].b == vertex_to_be_removed.index and self.faces[index_face].c == border_patch[-1]:
                    border_patch.append(self.faces[index_face].a)
                    
                    self.remove_face(index_face)
                    not_breaking = False
                    break
                elif self.faces[index_face].c == vertex_to_be_removed.index and self.faces[index_face].a == border_patch[-1]:
                    border_patch.append(self.faces[index_face].b)
                    
                    self.remove_face(index_face)
                    not_breaking = False
                    break
            if not_breaking:
                self.coloring_vertex_all_similar([0.5,0.5,0.5])
                self.coloring_list_vertices(border_patch,[1,0,0])
                raise Exception("Not found next vertex in the chain around")
                
        if len(border_patch) != vertex_to_be_removed.valence + 2:   
            # Through this process, since the gate face will be the last processed, the two vertices of the gates will be added in the chain and so being two time in it
            # (Once added when the left face of the gate face will be removed for the left gate vertex, and once the gate face is removed for the right gate vertex)
            # Therefore, the border_patch is required to have two more
            raise Exception("Unexpected valence or border_patch size (!=)")
        else:
            border_patch.pop() # remove the right gate vertex last adding
            border_patch.pop() # remove the left gate vertex last adding
       
        if vertex_to_be_removed.valence == 3:
            # Assigning retriangulation types
            if (self.vertices[border_patch[0]].retriangulation_type==1) and (self.vertices[border_patch[1]].retriangulation_type==-1):
                self.vertices[border_patch[2]].retriangulation_type=1
            elif (self.vertices[border_patch[0]].retriangulation_type==-1) and (self.vertices[border_patch[1]].retriangulation_type==1):
                self.vertices[border_patch[2]].retriangulation_type=1
            elif (self.vertices[border_patch[0]].retriangulation_type==1) and (self.vertices[border_patch[1]].retriangulation_type==1):
                self.vertices[border_patch[2]].retriangulation_type=-1
            elif (self.vertices[border_patch[0]].retriangulation_type==-1) and (self.vertices[border_patch[1]].retriangulation_type==-1):
                self.vertices[border_patch[2]].retriangulation_type=1
            else : 
                raise Exception("Unexpected retriangulation_type for gate vertices")  
            # Creating faces
            self.create_face([self.vertices[border_patch[0]].index,self.vertices[border_patch[1]].index,self.vertices[border_patch[2]].index])
            
        elif vertex_to_be_removed.valence == 4:
            if (self.vertices[border_patch[0]].retriangulation_type==1) and (self.vertices[border_patch[1]].retriangulation_type==-1):
                self.vertices[border_patch[2]].retriangulation_type=1
                self.vertices[border_patch[3]].retriangulation_type=-1
                # Create faces
                self.create_face([self.vertices[border_patch[0]].index,self.vertices[border_patch[1]].index,self.vertices[border_patch[2]].index])
                self.create_face([self.vertices[border_patch[0]].index,self.vertices[border_patch[2]].index,self.vertices[border_patch[3]].index])

            elif (self.vertices[border_patch[0]].retriangulation_type==-1) and (self.vertices[border_patch[1]].retriangulation_type==1):
                self.vertices[border_patch[2]].retriangulation_type=-1
                self.vertices[border_patch[3]].retriangulation_type=1
                #Create faces
                self.create_face([self.vertices[border_patch[0]].index,self.vertices[border_patch[1]].index,self.vertices[border_patch[3]].index])
                self.create_face([self.vertices[border_patch[1]].index,self.vertices[border_patch[2]].index,self.vertices[border_patch[3]].index])            

            elif (self.vertices[border_patch[0]].retriangulation_type==1) and (self.vertices[border_patch[1]].retriangulation_type==1):
                self.vertices[border_patch[2]].retriangulation_type=-1
                self.vertices[border_patch[3]].retriangulation_type=1
                #Create faces
                self.create_face([self.vertices[border_patch[0]].index,self.vertices[border_patch[1]].index,self.vertices[border_patch[3]].index])
                self.create_face([self.vertices[border_patch[1]].index,self.vertices[border_patch[2]].index,self.vertices[border_patch[3]].index])
                
            elif (self.vertices[border_patch[0]].retriangulation_type==-1) and (self.vertices[border_patch[1]].retriangulation_type==-1):
                self.vertices[border_patch[2]].retriangulation_type=1
                self.vertices[border_patch[3]].retriangulation_type=-1
                # Create faces
                self.create_face([self.vertices[border_patch[0]].index,self.vertices[border_patch[1]].index,self.vertices[border_patch[2]].index])
                self.create_face([self.vertices[border_patch[0]].index,self.vertices[border_patch[2]].index,self.vertices[border_patch[3]].index])
                
            else : raise Exception("Unexpected retriangulation_type for gate vertices")    

        elif vertex_to_be_removed.valence == 5:
            if (self.vertices[border_patch[0]].retriangulation_type==1) and (self.vertices[border_patch[1]].retriangulation_type==-1):
                self.vertices[border_patch[2]].retriangulation_type=1
                self.vertices[border_patch[3]].retriangulation_type=-1
                self.vertices[border_patch[4]].retriangulation_type=1
                # Create faces
                self.create_face([self.vertices[border_patch[0]].index,self.vertices[border_patch[1]].index,self.vertices[border_patch[2]].index])
                self.create_face([self.vertices[border_patch[0]].index,self.vertices[border_patch[2]].index,self.vertices[border_patch[4]].index])
                self.create_face([self.vertices[border_patch[2]].index,self.vertices[border_patch[3]].index,self.vertices[border_patch[4]].index])

            elif (self.vertices[border_patch[0]].retriangulation_type==-1) and (self.vertices[border_patch[1]].retriangulation_type==1):
                self.vertices[border_patch[2]].retriangulation_type=1
                self.vertices[border_patch[3]].retriangulation_type=-1
                self.vertices[border_patch[4]].retriangulation_type=1
                # Create faces
                self.create_face([self.vertices[border_patch[0]].index,self.vertices[border_patch[1]].index,self.vertices[border_patch[4]].index])                   
                self.create_face([self.vertices[border_patch[1]].index,self.vertices[border_patch[2]].index,self.vertices[border_patch[4]].index])
                self.create_face([self.vertices[border_patch[2]].index,self.vertices[border_patch[3]].index,self.vertices[border_patch[4]].index])

            elif (self.vertices[border_patch[0]].retriangulation_type==1) and (self.vertices[border_patch[1]].retriangulation_type==1):
                self.vertices[border_patch[2]].retriangulation_type=-1
                self.vertices[border_patch[3]].retriangulation_type=1
                self.vertices[border_patch[4]].retriangulation_type=-1
                # Create faces
                self.create_face([self.vertices[border_patch[0]].index,self.vertices[border_patch[1]].index,self.vertices[border_patch[3]].index])                 
                self.create_face([self.vertices[border_patch[1]].index,self.vertices[border_patch[2]].index,self.vertices[border_patch[3]].index])
                self.create_face([self.vertices[border_patch[3]].index,self.vertices[border_patch[4]].index,self.vertices[border_patch[0]].index])
                
            elif (self.vertices[border_patch[0]].retriangulation_type==-1) and (self.vertices[border_patch[1]].retriangulation_type==-1):
                self.vertices[border_patch[2]].retriangulation_type=1
                self.vertices[border_patch[3]].retriangulation_type=-1
                self.vertices[border_patch[4]].retriangulation_type=1
                # Create faces
                self.create_face([self.vertices[border_patch[0]].index,self.vertices[border_patch[1]].index,self.vertices[border_patch[2]].index])
                self.create_face([self.vertices[border_patch[0]].index,self.vertices[border_patch[2]].index,self.vertices[border_patch[4]].index])
                self.create_face([self.vertices[border_patch[2]].index,self.vertices[border_patch[3]].index,self.vertices[border_patch[4]].index])

            else : 
                raise Exception("Unexpected retriangulation_type for gate vertices") 
            
        elif vertex_to_be_removed.valence == 6:
            if (self.vertices[border_patch[0]].retriangulation_type==1) and (self.vertices[border_patch[1]].retriangulation_type==-1):
                self.vertices[border_patch[2]].retriangulation_type=1
                self.vertices[border_patch[3]].retriangulation_type=-1
                self.vertices[border_patch[4]].retriangulation_type=1
                self.vertices[border_patch[5]].retriangulation_type=-1
                
                # Create faces
                self.create_face([self.vertices[border_patch[0]].index,self.vertices[border_patch[1]].index,self.vertices[border_patch[2]].index])
                self.create_face([self.vertices[border_patch[0]].index,self.vertices[border_patch[2]].index,self.vertices[border_patch[4]].index])
                self.create_face([self.vertices[border_patch[0]].index,self.vertices[border_patch[4]].index,self.vertices[border_patch[5]].index])
                self.create_face([self.vertices[border_patch[2]].index,self.vertices[border_patch[3]].index,self.vertices[border_patch[4]].index])
            elif (self.vertices[border_patch[0]].retriangulation_type==-1) and (self.vertices[border_patch[1]].retriangulation_type==1):
                self.vertices[border_patch[2]].retriangulation_type=-1
                self.vertices[border_patch[3]].retriangulation_type=1
                self.vertices[border_patch[4]].retriangulation_type=-1
                self.vertices[border_patch[5]].retriangulation_type=1
                # Create faces
                self.create_face([self.vertices[border_patch[0]].index,self.vertices[border_patch[1]].index,self.vertices[border_patch[5]].index])
                self.create_face([self.vertices[border_patch[1]].index,self.vertices[border_patch[2]].index,self.vertices[border_patch[3]].index])
                self.create_face([self.vertices[border_patch[1]].index,self.vertices[border_patch[3]].index,self.vertices[border_patch[5]].index])
                self.create_face([self.vertices[border_patch[3]].index,self.vertices[border_patch[4]].index,self.vertices[border_patch[5]].index])
            elif (self.vertices[border_patch[0]].retriangulation_type==1) and (self.vertices[border_patch[1]].retriangulation_type==1):
                self.vertices[border_patch[2]].retriangulation_type=-1
                self.vertices[border_patch[3]].retriangulation_type=1
                self.vertices[border_patch[4]].retriangulation_type=-1
                self.vertices[border_patch[5]].retriangulation_type=1
                # Create faces
                self.create_face([self.vertices[border_patch[0]].index,self.vertices[border_patch[1]].index,self.vertices[border_patch[5]].index])
                self.create_face([self.vertices[border_patch[1]].index,self.vertices[border_patch[2]].index,self.vertices[border_patch[3]].index])
                self.create_face([self.vertices[border_patch[1]].index,self.vertices[border_patch[3]].index,self.vertices[border_patch[5]].index])
                self.create_face([self.vertices[border_patch[3]].index,self.vertices[border_patch[4]].index,self.vertices[border_patch[5]].index])
            elif (self.vertices[border_patch[0]].retriangulation_type==-1) and (self.vertices[border_patch[1]].retriangulation_type==-1):
                self.vertices[border_patch[2]].retriangulation_type=1
                self.vertices[border_patch[3]].retriangulation_type=-1
                self.vertices[border_patch[4]].retriangulation_type=1
                self.vertices[border_patch[5]].retriangulation_type=-1
                # Create faces
                self.create_face([self.vertices[border_patch[0]].index,self.vertices[border_patch[1]].index,self.vertices[border_patch[2]].index])
                self.create_face([self.vertices[border_patch[0]].index,self.vertices[border_patch[2]].index,self.vertices[border_patch[4]].index])
                self.create_face([self.vertices[border_patch[0]].index,self.vertices[border_patch[4]].index,self.vertices[border_patch[5]].index])
                self.create_face([self.vertices[border_patch[2]].index,self.vertices[border_patch[3]].index,self.vertices[border_patch[4]].index])
            else : raise Exception("Unexpected retriangulation_type for gate vertices")
        else:
            raise Exception("Unexpected valence: {} (<3 or >6)".format(vertex_to_be_removed.valence))  
        
        vertex_infos.visible = False
        return border_patch


    def manifold(self,border_patch):
        try :
            for i in range(0,len(border_patch)-1):
                self.gate_to_face(self.vertices[border_patch[i]], self.vertices[border_patch[i+1]])
                self.gate_to_face(self.vertices[border_patch[i+1]], self.vertices[border_patch[i]])
            return True
        except obja.NotGate2Face :
            return False
        
    def manifold2(self,border_patch):
        try :
            self.coloring_vertex_all_similar([0.5,0.5,0.5])
            liste_face = np.array([])
            for i in range(0,len(border_patch)):
                liste_face = np.append(liste_face,self.vertices[border_patch[i]].faces)
            
            valeurs, occurrences = np.unique(liste_face,return_counts=True)
            liste_face_select = valeurs[occurrences>=3]
            list_arrete = []
            if len(liste_face_select) == len(border_patch) - 2:
                for i in liste_face_select:
                    if self.faces[int(i)].visible:
                        face = self.faces[int(i)]
                        self.vertices[face.a].coloring_vertex([0,1,0])
                        self.vertices[face.a].coloring_vertex([0,1,0])
                        self.vertices[face.a].coloring_vertex([0,1,0])
                        if [face.a,face.c] not in list_arrete:
                            self.gate_to_face(self.vertices[face.a], self.vertices[face.c])
                            list_arrete.append([face.a,face.c])
                        if [face.c,face.b] not in list_arrete:
                            self.gate_to_face(self.vertices[face.c], self.vertices[face.b])
                            list_arrete.append([face.c,face.b])
                        if [face.b,face.a] not in list_arrete:
                            self.gate_to_face(self.vertices[face.b], self.vertices[face.a])
                            list_arrete.append([face.b,face.a])
                        if [face.a,face.b] not in list_arrete:
                            self.gate_to_face(self.vertices[face.a], self.vertices[face.b])
                            list_arrete.append([face.a,face.b])
                        if [face.b,face.c] not in list_arrete:
                            self.gate_to_face(self.vertices[face.b], self.vertices[face.c])
                            list_arrete.append([face.b,face.c])
                        if [face.c,face.a] not in list_arrete:
                            self.gate_to_face(self.vertices[face.c], self.vertices[face.a])
                            list_arrete.append([face.c,face.a])

                return True
            else:
                return False
        except obja.NotGate2Face :
            
            return False
        
    def allmanifold(self):
        try :
            list_arrete = []
            for i in range(0,len(self.faces)):
                if self.faces[i].visible:
                    face = self.faces[i]
                    if [face.a,face.c] not in list_arrete:
                        self.gate_to_face(self.vertices[face.a], self.vertices[face.c])
                        list_arrete.append([face.a,face.c])
                    if [face.c,face.b] not in list_arrete:
                        self.gate_to_face(self.vertices[face.c], self.vertices[face.b])
                        list_arrete.append([face.c,face.b])
                    if [face.b,face.a] not in list_arrete:
                        self.gate_to_face(self.vertices[face.b], self.vertices[face.a])
                        list_arrete.append([face.b,face.a])
            return True
        except obja.NotGate2Face:
            return False
        
        
    def protocol_null_patch(self,output_val_A,c_gate):
        front_face_information = self.gate_to_face(c_gate[0], c_gate[1])
        front_face = self.faces[front_face_information[0]]
        self.triangulation_null_patch(c_gate[0].index,c_gate[1].index, front_face_information[3].index)

        # The front face is flagged conquered
        front_face.state = obja.State.Conquered

        # creates the 2 new gate 
        new_gates = [[front_face_information[3].index,front_face_information[2].index],[front_face_information[1].index,front_face_information[3].index]]

        # add the gates to the fifo
        for gate in new_gates:
            self.vertices[gate[0]].state = obja.State.Conquered 
            self.vertices[gate[1]].state = obja.State.Conquered
            self.gate.append(gate)


        output_val_A.append("Null_patch")
        return output_val_A

    def decimating_conquest(self):
        self.count = 0
        output_val_A = []

        while len(self.gate) > 0 :
            index_c_gate = self.gate.popleft()

            c_gate = [self.vertices[index_c_gate[0]],self.vertices[index_c_gate[1]]]
            # search for the front face information
            front_face_information = self.gate_to_face(c_gate[0], c_gate[1])
            front_vertex = front_face_information[3]
            front_face = self.faces[front_face_information[0]]
            self.count += 1
            

            if front_face.state == obja.State.Conquered or front_face.state == obja.State.To_be_removed:
                pass


            #elif the front vertex is free and has a valence <= 6
            elif front_vertex.state == obja.State.Free and len(front_vertex.faces)<=6:
                save_model = self.clone()
                save_gate = self.gate.copy()
                # The front vertex is flagged to be removed and its incident faces are flagged to be removed.
                front_vertex.state = obja.State.To_be_removed
                for i in front_vertex.faces:
                    self.faces[i].state = obja.State.To_be_removed
                

                # search for the gates and the front vertex neighboring vertices are flagged conquered

                self.find_the_gate_index(front_vertex,c_gate)
                vertex_remove = Vertex_removed(front_vertex,c_gate)
                
                border_patch = self.retriangulation(vertex_remove)

                #if self.presence_of_valence_of(2) or not(self.manifold2(border_patch)):
                if not(self.manifold2(border_patch)):
                    self.copy(save_model)
                    self.gate = save_gate.copy()
                    c_gate = [self.vertices[c_gate[0].index], self.vertices[c_gate[1].index]]
                    output_val_A = self.protocol_null_patch(output_val_A,c_gate)
                else:
                    output_val_A.append([vertex_remove.valence,vertex_remove.index]) 
                
            
            # else, (if its front vertex is free and has a valence > 6) or (if its front vertex is tagged conquered)
            elif (front_vertex.state == obja.State.Free and len(front_vertex.faces)>6) or front_vertex.state == obja.State.Conquered :
                self.protocol_null_patch(output_val_A,c_gate)
            else:
                raise Exception("Error in the decimating conquest")
            
        print(self.count)
        return output_val_A
    


    def decimateAB(self):
        # inititialisation 
        
        inds_g = [1,2,3]
        self.increase_rd_seed()
        self.ind_4_inds_f = -1   # Index to choose in list of index of faces
        inds_f = random.sample(range(0,len(self.faces)),len(self.faces))   # List of index of faces, generated randomly (random.shuffle doesn't work on range object so use a sample)
        prepare_gate_decimating = True
        ind_4_inds_g = 0 # Index to choose in list of random integer that determind the gate choosen
        while prepare_gate_decimating:
            output_val_A = [] 
            cond = ind_4_inds_g != 0 # Condition to find a new face: the index for the gate has made a loop (from 0 to 2)
            while not cond:     #on cherche une face qui est visible
                self.ind_4_inds_f += 1 # Increasing the index for choosing random index of face
                self.increase_rd_seed() # Modify seed to ensure different shuffle
                random.shuffle(inds_g)  # Shuffling order of gates
                if self.ind_4_inds_f >= len(self.faces): # If too big, all face index has been tested
                    raise None_respect_cond("decimating")
                ind_f = inds_f[self.ind_4_inds_f]  # Choosing the index of face
                faces_init = self.faces[ind_f] # Take the face
                cond = faces_init.visible           # Condition for decimating: a face that is visible, be present in the model
            ind_g = inds_g[ind_4_inds_g]    # Choose index gate
            if ind_g == 1 and self.vertices[faces_init.a].visible and self.vertices[faces_init.b].visible: # gate will be a and b            
                self.vertices[faces_init.a].retriangulation_type = -1
                self.vertices[faces_init.b].retriangulation_type = 1
                init_gate_decimating = [faces_init.a,faces_init.b] # creation of the first gate
                prepare_gate_decimating = False
            elif ind_g == 2 and self.vertices[faces_init.b].visible and self.vertices[faces_init.c].visible: # gate will be b and c
                self.vertices[faces_init.b].retriangulation_type = -1
                self.vertices[faces_init.c].retriangulation_type = 1
                init_gate_decimating = [faces_init.b,faces_init.c] # creation of the first gate
                prepare_gate_decimating = False
            elif ind_g == 3 and self.vertices[faces_init.c].visible and self.vertices[faces_init.a].visible: # gate will be c and a                
                self.vertices[faces_init.c].retriangulation_type = -1
                self.vertices[faces_init.a].retriangulation_type = 1
                init_gate_decimating = [faces_init.c,faces_init.a] # creation of the first gate
                prepare_gate_decimating = False
        
        print(f"Decimating {self.nb_decimate}, try {self.ind_4_inds_f}/{len(self.faces)}, gate {ind_4_inds_g}")
        self.vertices[init_gate_decimating[0]].retriangulation_type = -1
        self.vertices[init_gate_decimating[1]].retriangulation_type = 1

        self.gate.append(init_gate_decimating)
        output_val_A = self.decimating_conquest()
 

        self.set_everything_to_free()
        self.set_everything_to_zeros()
        try:
            
            save_model = self.clone()          
            cond_do_cleaning = True
            self.random_seed += 1
            random.seed(self.random_seed)
            self.ind_4_inds_f = -1
            ind_4_inds_g = 0
            inds_f = random.sample(range(0,len(self.faces)),len(self.faces))
            while cond_do_cleaning:
                self.set_everything_to_free()
                self.set_everything_to_zeros()  
                ismanifold = True
                output_val_B = []
                self.copy(save_model)
                cond = False
                while not cond:  # on cherche une face qui est visible
                    if ind_4_inds_g == 0:
                        self.ind_4_inds_f += 1
                        if self.ind_4_inds_f >= len(self.faces):
                            raise None_respect_cond("decimating")
                    
                    ind_f = inds_f[self.ind_4_inds_f]
                    faces_init = self.faces[ind_f]
                    ind_g = inds_g[ind_4_inds_g] 
                    if ind_g == 1: # gate will be a and b            
                        init_gate_cleaning = [faces_init.a,faces_init.b] # creation of the first gate
                    elif ind_g == 2: # gate will be b and c
                        init_gate_cleaning = [faces_init.b,faces_init.c] # creation of the first gate
                    elif ind_g == 3: # gate will be c and a                
                        init_gate_cleaning = [faces_init.c,faces_init.a] # creation of the first gate
                    else:
                        raise Exception("Unexpected value for ind_g {}".format(ind_g))
                    
                    ind_4_inds_g = limit_value(ind_4_inds_g+1,0,2)
                    if faces_init.visible and not(len(self.vertices[init_gate_cleaning[0]].faces) == 3 or len(self.vertices[init_gate_cleaning[1]].faces) == 3):
                        cond = True
                print(f"Cleaning {self.nb_decimate}, try {self.ind_4_inds_f}/{len(self.faces)}, gate {limit_value(ind_4_inds_g-1,0,2)}") 
                self.gate.append(init_gate_cleaning)

                    
                self.count = 0 
                while len(self.gate) > 0 :
                    
                    vertex_remove = self.cleaning_conquest()
                    if vertex_remove == "Null_patch":
                        output_val_B.append("Null_patch")
                        
                    elif vertex_remove :
                        output_val_B.append([vertex_remove.valence,vertex_remove.index])
                        border_patch = self.retriangulation_4_cleaning_conquest(vertex_remove)
                        ismanifold = self.manifold2(border_patch)
                        if not(ismanifold):
                           break

                print("\nind_f: {}".format(ind_f))
                cond_do_cleaning =  not(ismanifold)
        except None_respect_cond:
            output_val_B = []
            # Maybe change this output, but the idea is to retry a decimating even if the cleaning doesn't work: a decimating can occur without cleaning after, but a cleaning can't without decimating change
        if not(self.allmanifold()):
            raise Exception(f"manifold cassé au cleaning {self.nb_decimate}")
        else :
            print("manifold respecté")
        self.print_count_valencies()
        decimating_output = Decimating_output(self.nb_decimate,init_gate_decimating,init_gate_cleaning,output_val_A,output_val_B)
        return decimating_output
    

    def count_point(self):
        count = 0
        for vertex in self.vertices:
            if vertex.visible:
                count += 1
        return count
        

    def decimate(self,nb_point_end = 15, nb_max_iteration=2):
        count_point = self.count_point()
        print("Number of verticies: {}".format(count_point))
        decimating_output = []
        
        while count_point>nb_point_end and self.nb_decimate<nb_max_iteration :
            self.nb_decimate += 1

            print(f"{self.nb_decimate}ieme decimation")
            output = self.decimateAB()
            decimating_output.append(output)
            self.set_everything_to_free()
            self.set_everything_to_zeros()
            count_point = self.count_point()
            print("Number of verticies: {}".format(count_point))


        return decimating_output
    def del_result(self):
        

        dossier = "./Results_tests"

        # Vérifier si le dossier existe
        if os.path.exists(dossier):
            # Liste tous les fichiers du dossier
            fichiers = os.listdir(dossier)

            # Parcours la liste et supprime chaque fichier
            for fichier in fichiers:
                if len(fichier) > 11 and fichier[0:11] == 'DecimateAB_':
                    pass
                else:
                    chemin_fichier = os.path.join(dossier, fichier)
                    try:
                        if os.path.isfile(chemin_fichier):
                            
                            os.remove(chemin_fichier)
                            print(f"Fichier supprimé : {fichier}")
                    except Exception as e:
                        print(f"Erreur lors de la suppression de {fichier}: {e}")
        else:
            print(f"Le dossier {dossier} n'existe pas.")

