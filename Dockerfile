FROM python:3.6

# first layers should be dependency installs so changes
# in code won't cause the build to start from scratch.
COPY requirements.txt /opt/program/requirements.txt

RUN pip3 install --no-cache-dir -r /opt/program/requirements.txt

# Set some environment variables
ENV PYTHONUNBUFFERED=TRUE
ENV PYTHONDONTWRITEBYTECODE=TRUE
ENV PATH="/opt/program:${PATH}"

# Set up the program in the image
COPY src /opt/program
COPY serverless/batch-transform/serverless.yml /opt/program/serverless.yml
WORKDIR /opt/program

CMD python batch_transform.py

