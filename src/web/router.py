from model import modelwrapper
from model.data import prepare_data
from wsgi import flask, app
import io
import pandas as pd
import json
import traceback


@app.route('/ping', methods=['GET'])
def ping():
    """Determine if the container is working and healthy. In this sample container, we declare
    it healthy if we can load the model successfully."""

    try:
        modelwrapper.model
        response = json.dumps('Everything working fine')
    except Exception as e:
        response = json.dumps(dict(response='Could not load model from aws',
                                   Exception=str(e),
                                   Trace=traceback.format_tb(e.__traceback__)))

    return flask.Response(response=response, status=200, mimetype='application/json')


@app.route('/invocations', methods=['POST'])
def transformation():
    """Do an inference on a single batch of data. In this sample server, we take data as CSV, convert
    it to a pandas data frame for internal use and then convert the predictions back to CSV (which really
    just means one prediction per line, since there's a single column.
    """
    # Convert from CSV to pandas
    if flask.request.content_type == 'text/csv':
        data = flask.request.data.decode('utf-8')
        s = io.StringIO(data)
        df = pd.read_csv(s)

    else:
        print('No csv, content type was: ', flask.request.content_type)
        try:
            print('Try parquet')
            b = io.BytesIO(flask.request.data)
            df = pd.read_parquet(b)
        except Exception as e:
            print('Exception: ', e)
            return flask.Response(response='This predictor only supports CSV or Parquet data',
                                  status=415, mimetype='text/plain')

    x = prepare_data(df, modelwrapper.columns, modelwrapper.scaler, modelwrapper.mean)
    print('Invoked with {} records'.format(x.shape[0]))

    # Do the prediction
    predictions = modelwrapper.predict(x)

    # Convert from numpy back to CSV
    out = io.StringIO()
    pd.DataFrame(predictions).to_csv(out, header=False, index=False)
    result = out.getvalue()

    return flask.Response(response=result, status=200, mimetype='text/csv')