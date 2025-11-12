import os.path
import tempfile
from process_bigraph import Composite, ProcessTypes

from bspil_basico.legacy.basico import Legacy_RunBasicSBMLTimeCourseSimulation
from bspil_basico.legacy.sbml_file import Legacy_ApplyModelChangesToSBML


def test_Legacy_RunBasicSBMLTimeCourseSimulation():
    core = ProcessTypes()
    core.register_process("time_course", Legacy_RunBasicSBMLTimeCourseSimulation)
    path_to_sbml = os.path.abspath('./tests/fixtures/interesting.sbml')
    schema = {
        'global_time_precision': None,
        'composition': {
            "sim_start_time": "float",
            "sim_duration": "float",
            "sim_num_data_points": "integer",
            'time_course': {
                "_type": "step",
                "address": {"_type": "quote", "_default": "local:time_course"},
                "_config": {
                    'sbml_file_path': "string",
                    'output_dir': "string"
                },
                "_inputs": {
                    "starting_time": "float",
                    "duration": "float",
                    "num_data_points": "integer"
                },
                "_outputs": {},
            },
            'global_time': 'float'
        },
        'state': {
            'global_time': 0.0,
            "sim_start_time": 0.0,
            "sim_duration": 10.0,
            "sim_num_data_points": 51,
            'time_course': {
                '_type' : "step",
                'address': 'local:time_course',
                'config': {'sbml_file_path': "REPLACE_ME", 'output_dir': "REPLACE_ME"},
                'interval': 1.0,
                'inputs': {
                    "starting_time": ["sim_start_time"],
                    "duration": ["sim_duration"],
                    "num_data_points": ["sim_num_data_points"]
                },
                'outputs': {}
            }
        },
        'interface': {
            'inputs': {},
            'outputs': {}
        },
        'bridge': {
            'inputs': {},
            'outputs': {}
        }
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        schema['state']['time_course']['config']['sbml_file_path'] = path_to_sbml
        schema['state']['time_course']['config']['output_dir'] = tmpdir
        pre_pre_dir = os.listdir(tmpdir)
        pre_pre_repr = repr(schema)
        legacy_comp = Composite(core=core, config=schema)
        pre_dir = os.listdir(tmpdir)
        pre_repr = repr(legacy_comp.config)
        legacy_comp.run(2.0)
        post_dir = os.listdir(tmpdir)
        post_repr = repr(legacy_comp.config)

    assert pre_pre_dir != pre_dir
    assert pre_dir == post_dir
    assert pre_pre_repr == pre_repr == post_repr


def test_sbml_replacement():
    old_contents: str
    new_contents: str
    sbml_file_path = os.path.join(os.path.dirname(__file__), 'fixtures/interesting.sbml')
    with open(sbml_file_path) as sbml_file:
        old_contents = sbml_file.read().strip()

    changes = [
        ("sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='s1']/@initialConcentration","0.77"),
        ("sbml:sbml/sbml:model/sbml:listOfCompartments/sbml:compartment[@id='c0']/@size", "7E-11"),
        ("sbml:sbml/sbml:model/sbml:listOfParameters/sbml:parameter[@id='Kf_decomposition']/@value", "0.07")
    ]
    new_sbml_file_path = Legacy_ApplyModelChangesToSBML.apply_model_changes(sbml_file_path, changes)
    with open(new_sbml_file_path) as new_sbml_file:
        new_contents = new_sbml_file.read().strip()

    assert new_contents != old_contents

    assert 'name="s1" compartment="c0" initialConcentration="0.77"' in new_contents
    assert 'compartment id="c0" name="c0" spatialDimensions="3" size="7e-11"' in new_contents
    assert 'parameter id="Kf_decomposition" value="0.07"' in new_contents

