import os.path

import matplotlib.pyplot as plt
import pandas as pd
import tellurium as te
from process_bigraph import Step
from roadrunner.roadrunner import RoadRunner


class TelluriumTimeCourseStep(Step):
    runner: RoadRunner
    output_dir: str

    def __init__(self, config, core):
        super().__init__(config, core)

    def initialize(self, config):
        sbml_file_path: str = os.path.abspath(os.path.expanduser(config['sbml_file_path']))
        if not os.path.exists(sbml_file_path):
            raise FileNotFoundError(sbml_file_path)

        if config['output_dir'] is None:
            raise ValueError('`output_dir` cannot be None')
        output_dir = os.path.abspath(os.path.expanduser(config['output_dir']))
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        self.output_dir = output_dir

        self.runner = te.loadSBMLModel(sbml_file_path)
        return

    def update(self, state):
        num_data_points: int = state["num_data_points"]
        starting_time: float = state["starting_time"]
        end_time: float = state["end_time"]
        results: pd.DataFrame = self.runner.simulate(start=starting_time, end=end_time, points=num_data_points)
        results.plot()
        plt.savefig(os.path.join(self.output_dir, "plot.pdf"))
        results.to_csv(os.path.join(self.output_dir, "report.csv"))
        return {}

    def inputs(self):
        return {
            "num_data_points": "integer",
            "starting_time": "float",
            "end_time": "float",
        }

    def outputs(self):
        return {}
