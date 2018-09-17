from cloudhelper import open_s3_file
import pandas as pd
import os
import yaml
import pickle


class ModelWrap:
    def __init__(self):
        if os.path.exists('../serverless/batch-transform/serverless.yml'):
            p = '../serverless/batch-transform/serverless.yml'
        else:
            p = 'serverless.yml'

        with open(p) as f:
            self.config = yaml.load(f)['custom']['dockerAvailable']

        self._model = None

    @property
    def model(self):
        """Get the model object for this instance, loading it if it's not already loaded."""
        if self._model is None:
            f = open_s3_file(self.config['BUCKET'], self.config['MODEL_PKL'])
            self._model = pickle.load(f)
        return self._model

    def predict(self, x):
        """For the input, do the predictions and return them.

        Args:
            input (a pandas dataframe): The data on which to do the predictions. There will be
                one prediction per row in the dataframe"""
        id = x.iloc[:, 0]
        x = x.iloc[:, 1:]
        p = self.model.predict_proba(x)[:, 1]
        return pd.DataFrame({'id': id, 'activation': p})


modelwrapper = ModelWrap()