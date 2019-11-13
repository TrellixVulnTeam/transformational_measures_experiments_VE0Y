from transformation_measure.measure.stats_running import RunningMeanAndVariance
from enum import Enum
import numpy as np
class MeasureFunction(Enum):
    var = "var"
    std = "std"
    mean = "mean"

    def apply_running(self,rm:RunningMeanAndVariance):
        if self == MeasureFunction.var:
            return rm.var()
        elif self == MeasureFunction.std:
            return rm.std()
        elif self == MeasureFunction.mean:
            return rm.mean()
        else:
            raise ValueError(f"Unsupported measure function {self.measure_function}")

    def apply(self, activations):
        functions = {
            MeasureFunction.var: lambda x: np.var(x, axis=0,ddof=1)
            , MeasureFunction.std: lambda x: np.std(x, axis=0,ddof=1)
            , MeasureFunction.mean: lambda x: np.mean(x, axis=0)
        }
        function = functions[self]
        return function(activations)


