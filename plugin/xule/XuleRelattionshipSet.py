"""XuleRelationshipSet

This is version of an Arelle ModelRelationshipSet, that allows multiple networks to be part of the relatioship set.

"""
import collections
from arelle.ModelRelationshipSet import ModelRelationshipSet
from typing import List

class XuleRelationshipSet:

    def __init__(self, model_xbrl, arelle_relationship_sets: List[ModelRelationshipSet]):

        self.modelXbrl = model_xbrl
        self._rel_sets = arelle_relationship_sets
        self._root_concepts = None
        self._relationships = None
        self._from_model_objects = None
        self._to_model_objects = None

        self.arcrole = None
        self.linkrole = None
        self.linkqname = None
        self.arcqname = None

    @property
    def rootConcepts(self):
        if self._root_concepts is None:
            self._root_concepts = self.fromModelObjects().keys() - self.toModelObjects().keys()

        return self._root_concepts

    @property
    def modelRelationships(self):
        if self._relationships is None:
            self._relationships = []
            for network in self._rel_sets:
                self._relationships.extend(network.modelRelationships)

        return self._relationships

    def fromModelObjects(self):
        if self._from_model_objects is None:
            self._from_model_objects = collections.defaultdict(list)
            for network in self._rel_sets:
                for key, val in network.fromModelObjects().items():
                    self._from_model_objects[key].extend(val)

        return self._from_model_objects
    
    def toModelObjects(self):
        if self._to_model_objects is None:
            self._to_model_objects = collections.defaultdict(list)
            for network in self._rel_sets:
                for key, val in network.toModelObjects().items():
                    self._to_model_objects[key].extend(val)

        return self._to_model_objects


    def fromModelObject(self, concept):
        results = []
        for network in self._rel_sets:
            results.extend(network.fromModelObject(concept))

        return results
   
    def toModelObject(self, concept):
        results = []
        for network in self._rel_sets:
            results.extend(network.toModelObject(concept))

        return results


