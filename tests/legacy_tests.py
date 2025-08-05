import os.path
import tempfile
import numpy as np
import basico as bsc
from PIL.Image import composite
from process_bigraph import Process, Composite, pf, Step, ProcessTypes

from bspil_basico.legacy.run_basic_simulation import Legacy_RunBasicSBMLTimeCourseSimulation


def test_Legacy_RunBasicSBMLTimeCourseSimulation():
    temp_dir = tempfile.TemporaryDirectory()
    # temp_dir_name = temp_dir.name
    temp_dir_name = os.path.expanduser("~/Development/Examination_Room/Room2")
    core = ProcessTypes()
    core.register_process("time_course", Legacy_RunBasicSBMLTimeCourseSimulation)

    schema = {
        'composition': {
            "sim_start_time": "float",
            "sim_duration": "float",
            "sim_num_data_points": "integer",
            'time_course': {
                "_type": "process",
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
        },
        'state': {
            "sim_start_time": 0.0,
            "sim_duration": 10.0,
            "sim_num_data_points": 51,
            'time_course': {
                '_type' : "process",
                'address': 'local:time_course',
                'config': {'sbml_file_path': f"{os.path.abspath('./fixtures/interesting.sbml')}", 'output_dir': f"{temp_dir_name}"},
                'interval': 1.0,
                'inputs': {
                    "starting_time": ["sim_start_time"],
                    "duration": ["sim_duration"],
                    "num_data_points": ["sim_num_data_points"]
                },
                'outputs': {}
            }
        }
    }

    legacy_comp = Composite(core=core, config=schema)
    print(f"\n{repr(legacy_comp.config)}")
    legacy_comp.run(2.0)
    print(f"\n{repr(legacy_comp.config)}")


    temp_dir.cleanup()
