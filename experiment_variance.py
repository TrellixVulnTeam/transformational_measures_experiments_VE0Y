## Calculate the variance of each activation in a model.
## NOTE:
## You should run "experiment_rotation.py" before this script to generate and train the models for
## a given dataset/model combination

import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams['image.cmap'] = 'gray'

from pytorch import models
import datasets
import torch
import pytorch.experiment.utils as utils

if __name__ == "__main__":
    model_name,dataset_name,transformation_names=utils.parse_model_and_dataset("Experiment: accuracy of model for rotated vs unrotated dataset.")
else:
    dataset_name="cifar10"
    model_name=models.AllConvolutional.__name__


print(f"### Loading dataset {dataset_name} and model {model_name}....")
verbose=True

use_cuda=torch.cuda.is_available()

dataset = datasets.get(dataset_name)
if verbose:
    print(dataset.summary())

from pytorch.experiment import rotation
unrotated_model, rotated_model, scores, config=rotation.load_models(dataset, model_name, use_cuda)

if verbose:
    print("### ", unrotated_model)
    print("### ", rotated_model)
    print("### Scores obtained:")
    rotation.print_scores(scores)

from variance_measure.measures import variance
from variance_measure import transformations as tf
from variance_measure import PytorchActivationsIterator

import numpy as np
from pytorch.numpy_dataset import NumpyDataset

sample_skip=2
if sample_skip>1:
    dataset.x_test= dataset.x_test[::sample_skip, ]
    dataset.y_test= dataset.y_test[::sample_skip]


n_rotations=16
rotations = np.linspace(-np.pi, np.pi, n_rotations, endpoint=False)

transformations_parameters={"rotation":rotations,"scale":[(1, 1)],"translation":[(0,0)]}

transformations_parameters_combinations=tf.generate_transformation_parameter_combinations(transformations_parameters)

transformations=tf.generate_transformations(transformations_parameters_combinations,dataset.input_shape[0:2])

def experiment(model,dataset,transformations,base_measure,options):
    numpy_dataset = NumpyDataset(dataset.x_test, dataset.y_test)
    iterator = PytorchActivationsIterator(model,numpy_dataset,transformations,batch_size=256)
    measure_result=base_measure(iterator,options).eval()

    stratified_numpy_datasets = NumpyDataset.stratify_dataset(dataset.y_test,dataset.x_test)
    stratified_iterators = [PytorchActivationsIterator(model,numpy_dataset,transformations,batch_size=256) for numpy_dataset in stratified_numpy_datasets]

    variance_measure = lambda iterator: base_measure(iterator,options).eval()
    stratified_measure = variance.StratifiedMeasure(stratified_iterators, variance_measure)
    stratified_measure_result,measure_per_class = stratified_measure.eval()

    measures=dict([(m.source,m) for m in [measure_result,stratified_measure_result]])
    for i,m in enumerate(measure_per_class):
        measures[f"{m.source}"] = m
    return measures

from experiment import variance_result


measures={"MeanNormalizedMeasure":variance.MeanNormalizedMeasure,
          "NormalizedMeasure":variance.NormalizedMeasure}

options={"measure":"MeanNormalizedMeasure",
         "conv_aggregation_function": variance.ConvAggregation.sum,
         "var_or_std": "std",
         "sample_skip":sample_skip}

options_str="-".join([str(v) for v in options.values()])
print(f"Experimenting with {options_str}")

measure_id=options["measure"]
measure_class=measures[measure_id]
unrotated_measures_results=experiment(unrotated_model, dataset, transformations, measure_class, options)
rotated_measures_results=experiment(rotated_model, dataset, transformations, measure_class, options)
result=variance_result.VarianceExperimentResult(unrotated_model.name, dataset.name, unrotated_model.activation_names(), dataset.labels, transformations, options, rotated_measures_results, unrotated_measures_results)
variance_result.save_results(result)


