import pandas as pd
import numpy as np


def prepare_data(df, col_select, scaler, mean_fill):
    """
    :param df: (DataFrame)
    :param col_select: (list) Columns to select from DataFrame
    :param scaler: (sklearn Scaler)
    :param mean_fill: (array) replace nans with these mean values. (These are required when using trained model)
    :returns: (array) features
    """
    data = df.copy()

    # Do something

    data['id'] = df['id']

    return data[['id'] + list(col_select)]