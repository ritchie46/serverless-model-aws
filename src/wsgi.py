import flask
import yaml
import os

app = flask.Flask(__name__)
if os.path.exists('../serverless/batch-transform/serverless.yml'):
    p = '../serverless/batch-transform/serverless.yml'
else:
    p = 'serverless.yml'

with open(p) as f:
    y = yaml.load(f)

app.config.update(y['custom']['flask'])

from web.router import app