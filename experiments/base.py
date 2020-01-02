import os
from pathlib import Path
from datetime import datetime
from experiment import variance, training, utils_runner
import config

import abc


class Experiment(abc.ABC):

    def __init__(self):
        self.plot_folderpath = config.plots_base_folder() / self.id()
        self.plot_folderpath.mkdir(exist_ok=True, parents=True)
        with open(self.plot_folderpath / "description.txt", "w") as f:
            f.write(self.description())
        self.venv = Path(".")

    def id(self):
        return self.__class__.__name__

    def set_venv(self, venv: Path):
        self.venv = venv

    def __call__(self, force=False, venv=".", *args, **kwargs):
        stars = "*" * 15
        strf_format = "%Y/%m/%d %H:%M:%S"
        dt_started = datetime.now()
        dt_started_string = dt_started.strftime(strf_format)
        if not self.has_finished() or force:
            self.mark_as_unfinished()
            print(f"[{dt_started_string}] {stars} Running experiment {self.id()}  {stars}")
            self.run()

            # time elapsed and finished
            dt_finished= datetime.now()
            dt_finished_string =dt_finished.strftime(strf_format)
            elapsed = dt_finished - dt_started
            print(f"[{dt_finished_string }] {stars} Finished experiment {self.id()}  ({elapsed} elapsed) {stars}")
            self.mark_as_finished()
        else:
            print(f"[{dt_started_string}] {stars}Experiment {self.id()} already finished, skipping. {stars}")

    def has_finished(self):
        return self.finished_filepath().exists()

    def finished_filepath(self):
        return self.plot_folderpath / "finished"

    def mark_as_finished(self):
        self.finished_filepath().touch(exist_ok=True)

    def mark_as_unfinished(self):
        f = self.finished_filepath()
        if f.exists():
            f.unlink()

    @abc.abstractmethod
    def run(self):
        pass

    @abc.abstractmethod
    def description(self) -> str:
        pass

    def experiment_finished(self, p: training.Parameters):
        model_path = config.model_path(p)
        if model_path.exists():
            if p.savepoints == []:
                return True
            else:
                savepoint_missing = [sp for sp in p.savepoints if not config.model_path(p, sp).exists()]
                return savepoint_missing == []
        else:
            return False

    def experiment_training(self, p: training.Parameters, min_accuracy=None):
        if not min_accuracy:
            min_accuracy = config.min_accuracy(p.model, p.dataset)
        if self.experiment_finished(p):
            return
        if len(p.suffix) > 0:
            suffix = f'-suffix "{p.suffix}"'
        else:
            suffix = ""

        savepoints = ",".join([str(sp) for sp in p.savepoints])
        python_command = f'train.py -model "{p.model}" -dataset "{p.dataset}" -transformation "{p.transformations.id()}" -epochs {p.epochs}  -num_workers 4 -min_accuracy {min_accuracy} -max_restarts 5 -savepoints "{savepoints}" {suffix}'
        utils_runner.run_python(self.venv, python_command)

    def experiment_variance(self, p: variance.Parameters, model_path: Path, batch_size: int = 64, num_workers: int = 0,
                            adapt_dataset=False):

        results_path = config.results_path(p)
        if os.path.exists(results_path):
            return
        if p.stratified:
            stratified = "-stratified"
        else:
            stratified = ""

        python_command = f'measure.py -mo "{model_path}" -me "{p.measure.id()}" -d "{p.dataset.id()}" -t "{p.transformations.id()}" -verbose False -batchsize {batch_size} -num_workers {num_workers} {stratified}'

        if adapt_dataset:
            python_command = f"{python_command} -adapt_dataset True"

        utils_runner.run_python(self.venv, python_command)
