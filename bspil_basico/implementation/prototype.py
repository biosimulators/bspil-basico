import os.path
import tempfile
import numpy as np
import basico as bsc
from process_bigraph import Process, Composite, pf, Step, ProcessTypes



class performTimeCourseFromSBML(Step):
    def initialize(self, config):
        pass

    def inputs(self):
        return {
            "timeCourseSettings" : {

            }
        }

    def outputs(self):
        return {}

    def update(self, state):
        return {

        }