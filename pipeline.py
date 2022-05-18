import os
from datetime import datetime

PROJECT = ""
BUCKET = PROJECT
REGION = "us-central1"
TIMESTAMP = datetime.now().strftime("%Y%m%d%H%M%S")
PIPELINE_ROOT = f"gs://{BUCKET}/pipeline_root"

# Output directory and job_name
OUTDIR = f"gs://{BUCKET}/taxifare/trained_model_{TIMESTAMP}"
MODEL_DISPLAY_NAME = f"taxifare_{TIMESTAMP}"
PYTHON_PACKAGE_URIS = f"gs://{BUCKET}/taxifare/taxifare_trainer-0.1.tar.gz"
MACHINE_TYPE = "n1-standard-16"
REPLICA_COUNT = 1
PYTHON_PACKAGE_EXECUTOR_IMAGE_URI = (
    "us-docker.pkg.dev/vertex-ai/training/tf-cpu.2-3:latest"
)
SERVING_CONTAINER_IMAGE_URI = (
    "us-docker.pkg.dev/vertex-ai/prediction/tf2-cpu.2-3:latest"
)
PYTHON_MODULE = "trainer.task"

# Model and training hyperparameters
BATCH_SIZE = 500
NUM_EXAMPLES_TO_TRAIN_ON = 10000
NUM_EVALS = 1000
NBUCKETS = 10
LR = 0.001
NNSIZE = "32 8"

# GCS paths
GCS_PROJECT_PATH = f"gs://{BUCKET}/taxifare"
DATA_PATH = f"{GCS_PROJECT_PATH}/data"
TRAIN_DATA_PATH = f"{DATA_PATH}/taxi-train*"
EVAL_DATA_PATH = f"{DATA_PATH}/taxi-valid*"

#################### Pipeline ####################
from kfp.v2.dsl import component, pipeline
from kfp.v2.google import experimental
from google_cloud_pipeline_components.aiplatform import ModelUploadOp, EndpointCreateOp, ModelDeployOp


@component
def training_op(input1: str):
    print(f"VertexAI pipeline: {input1}")

@pipeline(name="taxifare--train-upload-endpoint-deploy")
def pipeline(
    project: str = PROJECT,
    model_display_name: str = MODEL_DISPLAY_NAME,
):
    # 1. Model Training
    train_task = training_op("taxifare training pipeline")
    experimental.run_as_aiplatform_custom_job(
        train_task,
        display_name=f"pipelines-train-{TIMESTAMP}",
        worker_pool_specs=[
            {
                "pythonPackageSpec": {
                    "executor_image_uri": PYTHON_PACKAGE_EXECUTOR_IMAGE_URI,
                    "package_uris": [PYTHON_PACKAGE_URIS],
                    "python_module": PYTHON_MODULE,
                    "args": [
                        f"--eval_data_path={EVAL_DATA_PATH}",
                        f"--output_dir={OUTDIR}",
                        f"--train_data_path={TRAIN_DATA_PATH}",
                        f"--batch_size={BATCH_SIZE}",
                        f"--num_examples_to_train_on={NUM_EXAMPLES_TO_TRAIN_ON}",  # noqa: E501
                        f"--num_evals={NUM_EVALS}",
                        f"--nbuckets={NBUCKETS}",
                        f"--lr={LR}",
                        f"--nnsize={NNSIZE}",
                    ],
                },
                "replica_count": f"{REPLICA_COUNT}",
                "machineSpec": {
                    "machineType": f"{MACHINE_TYPE}",
                },
            }
        ],
    )

    # 2. Model Upload
    model_upload_op = ModelUploadOp(
        project=f"{PROJECT}",
        display_name=f"pipelines-ModelUpload-{TIMESTAMP}",
        artifact_uri=f"{OUTDIR}/savedmodel",
        serving_container_image_uri=f"{SERVING_CONTAINER_IMAGE_URI}",
        serving_container_environment_variables={"NOT_USED": "NO_VALUE"},
    )
    model_upload_op.after(train_task)

    # 3. Create Endpoint
    endpoint_create_op = EndpointCreateOp(
        project=f"{PROJECT}",
        display_name=f"pipelines-EndpointCreate-{TIMESTAMP}",
    )

    # 4. Deployment
    model_deploy_op = ModelDeployOp(
        project=f"{PROJECT}",
        endpoint=endpoint_create_op.outputs["endpoint"],
        model=model_upload_op.outputs["model"],
        deployed_model_display_name=f"{MODEL_DISPLAY_NAME}",
        machine_type=f"{MACHINE_TYPE}",
    )

# Compile the pipeline
from kfp.v2 import compiler

if not os.path.isdir("vertex_pipelines"):
    os.mkdir("vertex_pipelines")

compiler.Compiler().compile(
    pipeline_func=pipeline,
    package_path="./vertex_pipelines/train_upload_endpoint_deploy.json",
)

# Run the pipeline
from google_cloud_pipeline_components import aiplatform

pipeline_job = aiplatform.pipeline_jobs.PipelineJob(
    display_name="taxifare_pipeline",
    template_path="./vertex_pipelines/train_upload_endpoint_deploy.json",
    pipeline_root=f"{PIPELINE_ROOT}",
    project=PROJECT,
    location=REGION,
)
pipeline_job.run()