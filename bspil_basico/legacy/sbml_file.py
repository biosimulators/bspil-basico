import os.path
from tempfile import NamedTemporaryFile

import libsbml
from process_bigraph import Step
import re

class Legacy_ApplyModelChangesToSBML(Step):
    config_schema = {
        'sbml_file_path': {
            '_type': 'string',
            '_default': ''
        }
    }

    def __init__(self, config, core):
        super().__init__(config, core)
        self.sbml_file_path: str = ""

    def initialize(self, config):
        self.sbml_file_path = self.config['sbml_file_path']
        if self.sbml_file_path is None or self.sbml_file_path  == '':
            raise ValueError("config setting `sbml_file_path` cannot be None nor an empty string.")
        if not os.path.exists(self.sbml_file_path):
            raise FileNotFoundError(f"provided path to `sbml_file_path` ({self.sbml_file_path}) does not exist.")
        if not os.path.isfile(self.sbml_file_path):
            raise ValueError(f"provided path to `sbml_file_path` ({self.sbml_file_path}) does not point to a file.")

    def update(self, state):
        requested_changes: list[tuple[str,str]] = state['requested_changes']
        starting_sbml_file_path = self.sbml_file_path
        Legacy_ApplyModelChangesToSBML.apply_model_changes(starting_sbml_file_path, requested_changes)


    def inputs(self):
        return {
            "requested_changes" : "list[tuple[string, string]]"
        }

    def outputs(self):
        return {
            "new_sbml_file_path" : "string"
        }

    @staticmethod
    def apply_model_changes(sbml_file_path: str, requested_changes: list[tuple[str,str]],
                            generate_new_temp_file: bool = True) -> str:
        reader: libsbml.SBMLReader = libsbml.SBMLReader()
        document: libsbml.SBMLDocument = reader.readSBML(sbml_file_path)
        Legacy_ApplyModelChangesToSBML._check_for_sbml_errors(document)
        model: libsbml.Model = document.getModel()
        if model is None:
            raise RuntimeError(f"could not load model from sbml document at `{sbml_file_path}`")
        if document.getNumErrors() > 0:
            raise RuntimeError("SBML document has errors; cannot continue.")

        for target, new_value in requested_changes:
            namespaces: set[str] = set()
            path_id_pieces: list[str] = []
            for path_part in [elem.strip() for elem in target.split('/')]:
                namespace, part_id = ("sbml", path_part[1:]) if '@' == path_part[0] else path_part.split(':')
                namespaces.add(namespace)
                path_id_pieces.append(part_id)

            if 1 != len(namespaces) or list(namespaces)[0] != "sbml":
                raise NotImplementedError("Unable to handle non `sbml` namespaces.")
            if 5 != len(path_id_pieces):
                raise RuntimeError(f"Path `{target}` is not parsable.")

            end_element = path_id_pieces[-2]
            end_attribute = path_id_pieces[-1]  # get everything but the starting '@'
            # regex => if `species[@id="name"]`, we want to get out `species` and `name`
            re_exp = r"([A-Za-z]\w*)\s*\[\s*@id='(\w+)'\s*]"
            matches = re.findall(re_exp, end_element)  # gives us `[ ("species", "name") ]` (ideally)
            if 1 != len(matches) or 2 != len(matches[0]):
                raise RuntimeError(f"Unexpected number ({len(matches)}x{(len(matches[0]))} rather than 1x2) of "
                                   f"matches for string \"{end_element}\": `{matches}`.")
            element_type, element_id = matches[0]
            Legacy_ApplyModelChangesToSBML._perform_change(model, end_attribute, element_type, element_id, new_value)

        # write out to file
        writer = libsbml.SBMLWriter()
        file_name = os.path.basename(sbml_file_path[:sbml_file_path.rfind('.')])
        suffix = f"{file_name.replace('.', '_')}.xml"
        output_file_path = NamedTemporaryFile(suffix=suffix, delete=False).name if generate_new_temp_file else sbml_file_path
        if not writer.writeSBML(document, output_file_path):
            raise RuntimeError(f"Unable to write SBML to file at `{output_file_path}`.")
        return output_file_path

    @staticmethod
    def _check_for_sbml_errors(document: libsbml.SBMLDocument):
        error_messages: list[str] = []
        for error_num in range(document.getNumErrors()):
            error = document.getError(error_num)
            severity = error.getSeverity()
            if severity == libsbml.LIBSBML_SEV_FATAL:
                error_messages.append(f"{error_num})\tFATAL:\t" + error.getMessage())
            if severity == libsbml.LIBSBML_SEV_ERROR:
                error_messages.append(f"{error_num})\tERROR:\t" + error.getMessage())
        if len(error_messages) > 0:
            error_messages_as_str = "Unrecoverable SBML Errors Encountered:\n\t" + "\n\t".join(error_messages)
            raise RuntimeError(error_messages_as_str)

    @staticmethod
    def _perform_change(model: libsbml.Model, end_attribute: str, element_type: str, element_id: str, new_value: str):
        if "species" == element_type:
            species = model.getSpecies(element_id)
            if species is None:
                raise RuntimeError(f"Could not find species with id `{element_id}`.")
            try:
                coerced_number = float(new_value)
            except ValueError as e:
                raise RuntimeError(f"Provided change to species `{element_id}` is not a float: `{new_value}`", e)
            if "initialAmount" == end_attribute:
                result = species.setInitialAmount(coerced_number)
                if 0 != result:
                    raise RuntimeError(f"Unable to assign new initial amount "
                                       f"`{new_value}` to species `{element_id}`.")
            elif "initialConcentration" == end_attribute:
                result = species.setInitialConcentration(coerced_number)
                if 0 != result:
                    raise RuntimeError(f"Unable to assign new initial concentration "
                                       f"`{new_value}` to species `{element_id}`.")
            else:
                raise RuntimeError(f"Unknown change `{element_type}` to apply to species `{element_id}`.")
        elif "compartment" == element_type:
            compartment = model.getCompartment(element_id)
            if compartment is None:
                raise RuntimeError(f"Could not find compartment with id `{element_id}`.")
            if "size" == end_attribute:
                try:
                    coerced_size = float(new_value)
                except ValueError as e:
                    raise RuntimeError(f"Provided compartment size is not a float: `{new_value}`", e)
                result = compartment.setSize(coerced_size)
                if 0 != result:
                    raise RuntimeError(f"Unable to assign new size `{new_value}` to compartment `{element_id}`.")
            else:
                raise RuntimeError(f"Unknown change `{element_type}` to apply to compartment `{element_id}`.")
        elif "parameter" == element_type:
            parameter = model.getParameter(element_id)
            if parameter is None:
                raise RuntimeError(f"Could not find parameter with id `{element_id}`.")
            if "value" == end_attribute:
                try:
                    coerced_number = float(new_value)
                except ValueError as e:
                    raise RuntimeError(f"Provided change to parameter `{element_id}` is not "
                                       f"a float: `{new_value}`", e)
                result = parameter.setValue(coerced_number)
                if 0 != result:
                    raise RuntimeError(f"Unable to assign new value "f"`{new_value}` to parameter `{element_id}`.")
            else:
                raise RuntimeError(f"Unknown attribute `{end_attribute}` to apply to parameter ")
        else:
            raise NotImplementedError(f"No instruction to perform `{end_attribute}`({element_id}) assignment to "
                                      f"element `{element_type}`")
