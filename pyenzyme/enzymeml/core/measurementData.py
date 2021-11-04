import json

from pyenzyme.enzymeml.core.replicate import Replicate
from pyenzyme.enzymeml.core.functionalities import TypeChecker


class MeasurementData(object):
    """Helper class to organize elements"""

    def __init__(
        self,
        initConc,
        unit,
        reactantID=None,
        proteinID=None,
        replicates=list()
    ):
        # Check species --> Reactant overrides protein
        if reactantID:
            self.setReactantID(reactantID)
        elif proteinID:
            self.setProteinID(proteinID)
        else:
            raise ValueError(
                "Please enter a reactant or protein ID to add measurement data"
            )

        self.setInitConc(initConc)
        self.setUnit(unit)
        self.setReplicates(replicates)

    def toJSON(self, d=True, enzmldoc=None):

        jsonObject = {
            'initConc': self.__initConc,
            'replicates': [
                replicate.toJSON(d=True, enzmldoc=enzmldoc)
                for replicate in self.__replicates
            ],
        }

        if enzmldoc:
            jsonObject['unit'] = enzmldoc.getUnitString(self.__unit)
        else:
            jsonObject['unit'] = self.__unit

        if d:
            return jsonObject
        else:
            return json.dumps(jsonObject, sort_keys=True, indent=4)

    def setReactantID(self, reactantID):
        self.__reactantID = TypeChecker(reactantID, str)

    def getReactantID(self):
        return self.__reactantID

    def delReactantID(self):
        del self.__reactantID

    def setProteinID(self, proteinID):
        self.__proteinID = TypeChecker(proteinID, str)

    def getProteinID(self):
        return self.__proteinID

    def delProteinID(self):
        del self.__proteinID

    def setInitConc(self, initConc):
        self.__initConc = TypeChecker(initConc, float)

    def getInitConc(self):
        return self.__initConc

    def delInitConc(self):
        del self.__initConc

    def setUnit(self, unit):
        self.__unit = TypeChecker(unit, str)

    def getUnit(self):
        return self.__unit

    def delUnit(self):
        del self.__unit

    def setReplicates(self, replicates):

        if isinstance(replicates, Replicate):
            replicates = [replicates]

        self.__replicates = [
            TypeChecker(repl, Replicate)
            for repl in replicates
        ]

    def getReplicates(self):
        return self.__replicates

    def delReplicates(self):
        del self.__replicates

    def setMeasurementIDs(self, ID):
        for replicate in self.__replicates:
            replicate.setMeasurement(ID)

    def addReplicate(self, replicate):
        self.__replicates.append(
            TypeChecker(replicate, Replicate)
        )
