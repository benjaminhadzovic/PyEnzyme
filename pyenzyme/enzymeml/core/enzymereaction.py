'''
File: enzymereaction.py
Project: core
Author: Jan Range
License: BSD-2 clause
-----
Last Modified: Wednesday June 23rd 2021 9:06:54 pm
Modified By: Jan Range (<jan.range@simtech.uni-stuttgart.de>)
-----
Copyright (c) 2021 Institute of Biochemistry and Technical Biochemistry Stuttgart
'''

import logging
import re

from typing import List, Optional, TYPE_CHECKING
from dataclasses import dataclass
from pydantic import (
    BaseModel,
    PositiveFloat,
    validate_arguments,
    Field,
    PrivateAttr
)

from pyenzyme.enzymeml.core.enzymemlbase import EnzymeMLBase
from pyenzyme.enzymeml.models.kineticmodel import KineticModel
from pyenzyme.enzymeml.core.ontology import SBOTerm
from pyenzyme.enzymeml.core.exceptions import (
    SpeciesNotFoundError,
)

from pyenzyme.utils.log import log_object
from pyenzyme.enzymeml.core.utils import (
    type_checking,
    deprecated_getter
)

if TYPE_CHECKING:  # pragma: no cover
    static_check_init_args = dataclass
else:
    static_check_init_args = type_checking

# Initialize the logger
logger = logging.getLogger("pyenzyme")


@static_check_init_args
class ReactionElement(BaseModel):
    """Describes an element of a chemical reaction."""

    species_id: str = Field(
        ...,
        description="Internal identifier to either a protein or reactant defined in the EnzymeMLDocument.",
    )

    stoichiometry: PositiveFloat = Field(
        ...,
        description="Positive float number representing the associated stoichiometry.",
    )

    constant: bool = Field(
        ...,
        description="Whether or not the concentration of this species remains constant.",
    )

    ontology: SBOTerm = Field(
        ...,
        description="Ontology defining the role of the given species.",
    )

    def get_id(self) -> str:
        """Internal usage to get IDs from objects without ID attribute"""

        if self.species_id:
            return self.species_id
        else:
            raise AttributeError("No species ID given.")


@static_check_init_args
class EnzymeReaction(EnzymeMLBase):
    """
        Describes an enzyme reaction by combining already defined
        reactants/proteins of an EnzymeML document. In addition,
        this class provides ways to integrate reaction conditions
        as well. It is also possible to add a kinetic law to this
        object by using the KineticModel class.
    """

    name: str = Field(
        ...,
        description="Name of the reaction.",
        template_alias="Name"
    )

    reversible: bool = Field(
        ...,
        description="Whether the reaction is reversible or irreversible",
        template_alias="Reversible"
    )

    temperature: Optional[float] = Field(
        None,
        description="Numeric value of the temperature of the reaction.",
        template_alias="Temperature value"
    )

    temperature_unit: Optional[str] = Field(
        None,
        description="Unit of the temperature of the reaction.",
        regex=r"kelvin|Kelvin|k|K|celsius|Celsius|C|c",
        template_alias="Temperature unit"
    )

    ph: Optional[float] = Field(
        None,
        description="PH value of the reaction.",
        template_alias="pH value",
        inclusiveMinimum=0,
        inclusiveMaximum=14
    )

    ontology: Optional[SBOTerm] = Field(
        SBOTerm.BIOCHEMICAL_REACTION,
        description="Ontology defining the role of the given species.",
    )

    id: Optional[str] = Field(
        None,
        description="Unique identifier of the reaction.",
        template_alias="ID",
        regex=r"r[\d]+"
    )

    meta_id: Optional[str] = Field(
        None,
        description="Unique meta identifier for the reaction.",
    )

    uri: Optional[str] = Field(
        None,
        description="URI of the reaction.",
    )

    creator_id: Optional[str] = Field(
        None,
        description="Unique identifier of the author.",
    )

    model: Optional[KineticModel] = Field(
        None,
        description="Kinetic model decribing the reaction.",
    )

    educts: List[ReactionElement] = Field(
        default_factory=list,
        description="List of educts containing ReactionElement objects.",
        template_alias="Educts"
    )

    products: List[ReactionElement] = Field(
        default_factory=list,
        description="List of products containing ReactionElement objects.",
        template_alias="Products"
    )

    modifiers: List[ReactionElement] = Field(
        default_factory=list,
        description="List of modifiers (Proteins, snhibitors, stimulators) containing ReactionElement objects.",
        template_alias="Modifiers"
    )

    # * Private attributes
    _temperature_unit_id: str = PrivateAttr(None)

    # ! Getters
    def getEduct(self, id: str) -> ReactionElement:
        """
        Returns a ReactionElement including information about the following properties:

            - Reactant/Protein Identifier
            - Stoichiometry of the element
            - Whether or not the element's concentration is constant

        Args:
            id (string): Reactant/Protein ID

        Raises:
            SpeciesNotFoundError: If species ID is unfindable

        Returns:
            ReactionElement: Object including species ID, stoichiometry, constant)
        """

        return self._getReactionElement(
            id=id, element_list=self.educts, element_type="Educts"
        )

    def getProduct(self, id: str) -> ReactionElement:
        """
        Returns a ReactionElement including information about the following properties:

            - Reactant/Protein Identifier
            - Stoichiometry of the element
            - Whether or not the element's concentration is constant

        Args:
            id (string): Reactant/Protein ID

        Raises:
            SpeciesNotFoundError: If species ID is unfindable

        Returns:
            ReactionElement: Object including species ID, stoichiometry, constant)
        """

        return self._getReactionElement(
            id=id, element_list=self.products, element_type="Products"
        )

    def getModifier(self, id: str) -> ReactionElement:
        """
        Returns a ReactionElement including information about the following properties:

            - Reactant/Protein Identifier
            - Stoichiometry of the element
            - Whether or not the element's concentration is constant

        Args:
            id (string): Reactant/Protein ID

        Raises:
            SpeciesNotFoundError: If species ID is unfindable

        Returns:
            ReactionElement: Object including species ID, stoichiometry, constant)
        """

        return self._getReactionElement(
            id=id, element_list=self.modifiers, element_type="Modifiers"
        )

    @validate_arguments
    def _getReactionElement(
        self,
        id: str,
        element_list: list[ReactionElement],
        element_type: str,
    ) -> ReactionElement:

        try:
            return next(filter(
                lambda element: element.species_id == id,
                element_list
            ))
        except StopIteration:
            raise SpeciesNotFoundError(
                species_id=id, enzymeml_part=element_type
            )

    # ! Adders
    @validate_arguments
    def addEduct(
        self,
        species_id: str,
        stoichiometry: PositiveFloat,
        enzmldoc,
        constant: bool = False,
        ontology: SBOTerm = SBOTerm.SUBSTRATE
    ) -> None:
        """
        Adds element to EnzymeReaction object. Replicates as well
        as initial concentrations are optional.

        Args:
            species_id: str (string): Reactant/Protein ID - Needs to be pre-defined!
            stoichiometry (float): Stoichiometric coefficient
            constant:  (bool): Whether constant or not
            enzmldoc (EnzymeMLDocument): Checks and adds IDs

        Raises:
            SpeciesNotFoundError: If Reactant/Protein hasnt been defined yet
        """

        self._addElement(
            species_id=species_id,
            stoichiometry=stoichiometry,
            constant=constant,
            element_list=self.educts,
            ontology=ontology,
            list_name="educts",
            enzmldoc=enzmldoc
        )

    @validate_arguments
    def addProduct(
        self,
        species_id: str,
        stoichiometry: PositiveFloat,
        enzmldoc,
        constant: bool = False,
        ontology: SBOTerm = SBOTerm.PRODUCT
    ) -> None:
        """
        Adds element to EnzymeReaction object. Replicates as well
        as initial concentrations are optional.

        Args:
            species_id: str (string): Reactant/Protein ID - Needs to be pre-defined!
            stoichiometry (float): Stoichiometric coefficient
            constant:  (bool): Whether constant or not
            enzmldoc (EnzymeMLDocument): Checks and adds IDs

        Raises:
            SpeciesNotFoundError: If Reactant/Protein hasnt been defined yet
        """

        self._addElement(
            species_id=species_id,
            stoichiometry=stoichiometry,
            constant=constant,
            element_list=self.products,
            ontology=ontology,
            list_name="products",
            enzmldoc=enzmldoc
        )

    @validate_arguments
    def addModifier(
        self,
        species_id: str,
        stoichiometry: PositiveFloat,
        constant: bool,
        enzmldoc,
        ontology: SBOTerm = SBOTerm.CATALYST
    ) -> None:
        """
        Adds element to EnzymeReaction object. Replicates as well
        as initial concentrations are optional.

        Args:
            species_id: str (string): Reactant/Protein ID - Needs to be pre-defined!
            stoichiometry (float): Stoichiometric coefficient
            constant:  (bool): Whether constant or not
            enzmldoc (EnzymeMLDocument): Checks and adds IDs

        Raises:
            SpeciesNotFoundError: If Reactant/Protein hasnt been defined yet
        """

        self._addElement(
            species_id=species_id,
            stoichiometry=stoichiometry,
            constant=constant,
            element_list=self.modifiers,
            ontology=ontology,
            list_name="modifiers",
            enzmldoc=enzmldoc
        )

    def _addElement(
        self,
        species_id: str,
        stoichiometry: PositiveFloat,
        constant: bool,
        element_list: list[ReactionElement],
        ontology: SBOTerm,
        list_name: str,
        enzmldoc
    ) -> None:

        # Check if species is part of document already
        all_species = [
            *list(enzmldoc.protein_dict.keys()),
            *list(enzmldoc.reactant_dict.keys()),
            *list(enzmldoc.complex_dict.keys())
        ]

        if species_id not in all_species:
            raise SpeciesNotFoundError(
                species_id=species_id, enzymeml_part="EnzymeMLDocument"
            )

        # Add element to the respecticve list
        element = ReactionElement(
            species_id=species_id,
            stoichiometry=stoichiometry,
            constant=constant,
            ontology=ontology
        )
        element_list.append(element)

        # Log the addition
        log_object(logger, element)
        logger.debug(
            f"Added {type(element).__name__} '{element.species_id}' to reaction '{self.name}' {list_name}"
        )

    def addFromEquation(self, reaction_equation: str, enzmldoc) -> None:
        """Parses a reaction equation string and adds it to the model.

        Args:
            reaction_equation (str): Strign representing th reaction equation, following the schem r''
            enzmldoc ([type]): [description]
        """

        # Split reaction is educts and products
        if "->" in reaction_equation:
            educts, products = reaction_equation.split(" -> ")
        elif "<=>" in reaction_equation:
            educts, products = reaction_equation.split(" <=> ")
        else:
            raise ValueError(
                "Neither '->' nor '<=>' were found in the reaction euqation, but are essential to distinguish educt from product side."
            )

        # Parse each side of the reaction
        self._parse_equation_side(educts, enzmldoc, self.addEduct)
        self._parse_equation_side(products, enzmldoc, self.addProduct)

    @staticmethod
    def _parse_equation_side(elements: str, enzmldoc, fun):
        """Parses a side from a reaction equation."""

        # Setup Regex
        regex = r"(^\d*[.,]\d*)?\s?(.*)"
        regex = re.compile(regex)

        for element in elements.split(" + "):
            stoichiometry, species = regex.findall(element)[0]

            if len(stoichiometry) == 0:
                stoichiometry = 1.0

            if re.match(r"^[p|s|c]\d*$", species):
                species_id = species
            else:
                species_id = enzmldoc.getAny(species, by_id=False).id

            # Add it to the reaction
            fun(
                species_id=species_id,
                stoichiometry=float(stoichiometry),
                enzmldoc=enzmldoc
            )

    def setModel(self, model: KineticModel, enzmldoc) -> None:
        """Sets the kinetic model of the reaction and in addition converts all units to UnitDefs.

        Args:
            model (KineticModel): Kinetic model that has been derived.
            enzmldoc (EnzymeMLDocument): The EnzymeMLDocument that holds the reaction.
        """

        # ID consistency
        enzmldoc._check_kinetic_model_ids(
            equation=model.equation,
            species_ids=enzmldoc.getSpeciesIDs()
        )

        # Unit conversion
        enzmldoc._convert_kinetic_model_units(
            model.parameters,
            enzmldoc=enzmldoc
        )

        self.model = model

    # ! Utilities
    def get_reaction_scheme(self, by_name: bool = False, enzmldoc=None):

        if by_name and enzmldoc is None:
            raise ValueError(
                "Please provide an EnzymeMLDocument if the reaction schem should include names")

        educts = self._summarize_elements(self.educts, by_name, enzmldoc)
        products = self._summarize_elements(self.products, by_name, enzmldoc)
        modifiers = self._summarize_elements(
            self.modifiers, by_name, enzmldoc).replace(" + ", ", ")

        if modifiers:
            return f"{self.name}:\n{educts} -> {products}\nModifiers: {modifiers}\n"
        else:
            return f"{self.name}:\n{educts} -> {products}\n"

    def _summarize_elements(self, elements: list, by_name, enzmldoc) -> str:
        """Parses all reaction elements of a list to a string"""

        if by_name is False:
            return " + ".join([
                f"{element.stoichiometry} {element.species_id}"
                for element in elements
            ])
        else:
            return " + ".join([
                f"{element.stoichiometry} {enzmldoc.getAny(element.species_id).name}"
                for element in elements
            ])

    # ! Initializers
    @classmethod
    def fromEquation(cls, equation: str, name: str, enzmldoc):
        """Creates an EnzymeReaction object from a reaction equation.

        Please make sure that the equation follows either of the following patterns:

            '1.0 Substrate -> 1.0 Product' (for irreversible)

            or

            '1.0 Substrate <=> 1.0 Product' (for reversible)

        Args:
            equation (str): Reaction equation with educt and product sides.
            name (str): Name of the reaction.
            reversible (bool): If the reaction is reversible or not. Defaults
            enzmldoc ([type]): Used to validate species IDs.
        """

        if "<=>" in equation:
            reversible = True
        elif "->" in equation:
            reversible = False
        else:
            raise ValueError(
                "Neither '->' nor '<=>' were found in the reaction euqation, but are essential to distinguish educt from product side."
            )

        # Initialize reaction object
        reaction = cls(name=name, reversible=reversible)

        # Parse the reaction equation
        reaction.addFromEquation(equation, enzmldoc)

        return reaction

    # ! Getters (old)

    def getTemperature(self) -> float:
        raise NotImplementedError(
            "Temperature is now part of measurements."
        )

    def getTempunit(self) -> str:
        raise NotImplementedError(
            "Temperature unit is now part of measurements."
        )

    def getPh(self) -> PositiveFloat:
        raise NotImplementedError(
            "Ph is now part of measurements."
        )

    @ deprecated_getter("name instead")
    def getName(self) -> str:
        return self.name

    @ deprecated_getter("reveserible")
    def getReversible(self) -> bool:
        return self.reversible

    @ deprecated_getter("id")
    def getId(self) -> Optional[str]:
        return self.id

    @ deprecated_getter("meta_id")
    def getMetaid(self) -> Optional[str]:
        return self.meta_id

    @ deprecated_getter("model")
    def getModel(self) -> Optional[KineticModel]:
        return self.model

    @ deprecated_getter("educts")
    def getEducts(self):
        return self.educts

    @ deprecated_getter("products")
    def getProducts(self):
        return self.products

    @ deprecated_getter("modifier")
    def getModifiers(self):
        return self.modifiers
