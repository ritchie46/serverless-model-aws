# Model Endpoint and Serverless Batch Transform Job on AWS

This repo is a basis template for deploying a model as a batch transform job or as a server endpoint on AWS Elastic Container Service.

* A **server endpoint will** remain running and can be used as an API to do inference.
* A **batch transform job** will be deployed as a serverless application and will do inference on new data dropped in AWS S3. The moment new data is put on an S3 Bucket, a lambda function is triggered. The lambda will put the meta data of the fresh data on an AWS SQS Queue. A container will be deployed in AWS ECS, finish the jobs on the SQS Queue and finally will shut down.

## Requirements
* Make sure you've got the [aws cli installed](https://aws.amazon.com/cli/).
* Set your `aws_access_key_id` and `aws_secret_access_key` in _~/.aws/credentials_
* Install [Docker](https://docs.docker.com/install/)
* Install [Serverless](https://serverless.com/framework/docs/providers/aws/guide/installation/)
* Add extra requirements for you model in _requirements.txt_
* If you want to do local (unit) tests, install the _requirements.txt_ to your virtual/ Anaconda environment

## Your custom model and data preparation
This template is just a setup and needs your own model to run. When the container is spun up, the container will fetch data from the SQS Queue. You probably want to modify the data before calling the model for inference. In the current template the model as well as the scaler are Scikit-Learn objects, that need to be loaded from S3 once the container is running. The model can thus be updated by updating the files in S3.

### Model artifacts
In _src/model/\_\_init\_\_.py_ The model, scalers and numpy arrays with mean values (in order to replace missing values) are loaded into memory. Finally the **ModelWrap** object also defines a **predict** method that is called during inference. This file must be adapted to match your needs. Currently the template only accepts ***.parquet files**. If you want to accept more file types, you'll need to adapt _src/web/router.py_ (the **transformation** function)

``` python
class ModelWrap:
    def __init__(self):
        self._model = None
        self._scaler = None
        self._mean = None
        self._columns = None

    @property
    def model(self):
        """Get the model object for this instance, loading it if it's not already loaded."""
        if self._model is None:
            f = open_s3_file(app.config['BUCKET'], app.config['MODEL_PKL'])
            self._model = pickle.load(f)
        return self._model

    @property
    def scaler(self):
        if self._scaler is None:
            f = open_s3_file(app.config['BUCKET'], app.config['SCALER_PKL'])
            self._scaler = pickle.load(f)
        return self._scaler

    @property
    def mean(self):
        if self._mean is None:
            f = open_s3_file(app.config['BUCKET'], app.config['MEAN_PKL'])
            self._mean = pickle.load(f)
        return self._mean

    @property
    def columns(self):
        if self._columns is None:
            f = open_s3_file(app.config['BUCKET'], app.config['COLUMNS_PKL'])
            self._columns = pickle.load(f)
        return self._columns

    def predict(self, x):
        """For the input, do the predictions and return them.

        Args:
            input (a pandas dataframe): The data on which to do the predictions. There will be
                one prediction per row in the dataframe"""
        id = x.iloc[:, 0]
        x = x.iloc[:, 1:]
        p = self.model.predict_proba(x)[:, 1]
        return pd.DataFrame({'id': id, 'activation': p})
```

### Data preparation
Change the **prepare_data** function in _src/model/data.py_ so that you don't have any missing values, your outliers are removed etc.
The following files can be modified for your specific model/ data needs.

## Settings File
All the settings for the Docker image (such as the S3 URI's for the model and scaler) and all the settings for the Serverless application are defined the _serverless/batch-transform/serverless.yml_ under the **custom** key.

``` yaml
# Custom are the variables for this template.
custom:
  flask:
    # These setting will be exposed for the model in the docker image
    BUCKET: <bucket> containing the model artifacts.
    MODEL_PKL: <key> for the above defined bucket
    SCALER_PKL: <key> for the above defined bucket
    MEAN_PKL: <key> for the above defined bucket
    COLUMNS_PKL: <key> for the above defined bucket
    TEST_DATA: <key> for the above defined bucket
    AWS_REGION: eu-west-1

  # Docker image that will be deployed
  image: <repository url>
  desiredTaskCount: 1

  # Settings for the naming of new AWS resources
  prefix: <str> Resources made in AWS will have this prefix
  usecase: <str> Resoures made in AWS will have this name
  model: <str> Name of the model. Name will be given to the Resources in AWS

  # Bucket & key to where the results are written
  outputBucket: <bucket>
  outputKey: <key>

  # Bucket that will be generated for this stack. New data should be deployed here.
  bucket: ${self:custom.prefix}-${self:custom.usecase}-new-data

  # File type that should trigger the Lambda
  triggerExtension: .parquet

  # Subnet and security group names in which the AWS Task should run.
  subnet:  <subnet name>
  securityGroup: <security group name>

  # ARN of the Role that will be assigned to the Task. It needs SQS, S3 and ECS access
  ecsTaskExecutionRole: <arn of role with the needed permissions>
```

## Local Tests
Make sure you've installed the _requirements.txt_, modified your code to work with your model and added your model to S3 along with some test data. If needed modify some of the unit tests in _src/tests.py_.

`$ cd src && python -m unittest tests.py`

## Deploy
If your tests worked out fine you'll need to deploy the docker image to an AWS ECR repository.

`$ .build_and_push.sh <tag>`

will build your Dockerfile and push the ECR. If the tag doesn't yet exist, a new repository will be made. Copy the URI of the repository and add that the settings file in  _serverless/batch-transform/serverless.yml_ under **custom.image**

Finally you can deploy the whole Serverless stack with:

`$ cd serverless/batch-transform && sls deploy`

This command has created an AWS Cloudformation stack.
