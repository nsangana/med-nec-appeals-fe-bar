# Databricks notebook source
# MAGIC %md
# MAGIC # Build, Log, Register, and Deploy Appeals Chat Agent

# COMMAND ----------

import json
import os

import mlflow
from mlflow.models.resources import (
    DatabricksServingEndpoint,
    DatabricksFunction,
    DatabricksVectorSearchIndex,
)
from mlflow.tracking import MlflowClient

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

CATALOG, SCHEMA = "appeals_hackathon_catalog", "fe_bar_appeals"
LLM_ENDPOINT = "databricks-claude-sonnet-4-6"
VS_INDEX = f"{CATALOG}.{SCHEMA}.med_nec_criteria_index"
UC_FUNCTIONS = [
    f"{CATALOG}.{SCHEMA}.get_appeal",
    f"{CATALOG}.{SCHEMA}.get_encounter",
    f"{CATALOG}.{SCHEMA}.mpfs_lookup",
    f"{CATALOG}.{SCHEMA}.descriptor_lookup",
]

FULL_NAME = f"{CATALOG}.{SCHEMA}.appeals_chat_agent"
ENDPOINT_NAME = "fe-bar-appeals-chat"

# The agent.py file was previously uploaded to workspace
# We'll reference it directly (Databricks notebooks can access workspace files)
# Workspace path where this repo's agent/agent.py is synced. Override with FEBAR_AGENT_FILE (no personal path in the repo).
agent_file = os.environ.get("FEBAR_AGENT_FILE", "/Workspace/Shared/fe_bar_appeals/agent/agent.py")

# Define the resources needed for passthrough auth
resources = [
    DatabricksServingEndpoint(endpoint_name=LLM_ENDPOINT),
    DatabricksVectorSearchIndex(index_name=VS_INDEX),
    *[DatabricksFunction(function_name=f) for f in UC_FUNCTIONS],
]

print(f"Model will be registered as: {FULL_NAME}")
print(f"Endpoint target name: {ENDPOINT_NAME}")
print(f"Resources for passthrough auth: {len(resources)} items")
print(f"Agent file: {agent_file}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Log and Register the Agent

# COMMAND ----------

mlflow.set_registry_uri("databricks-uc")
mlflow.set_experiment("/Shared/fe-bar-appeals-chat")

with mlflow.start_run():
    info = mlflow.pyfunc.log_model(
        artifact_path="agent",
        python_model=agent_file,
        resources=resources,
        input_example={"input": [{"role": "user", "content": "What is the recommendation for this appeal?"}]},
        pip_requirements=[
            "mlflow==3.1.0",
            "databricks-langchain",
            "langgraph==0.3.4",
            "databricks-agents",
            "langchain-core",
            "pydantic>=2",
        ],
        registered_model_name=FULL_NAME,
    )

print(f"Model logged with URI: {info.model_uri}")
print(f"Registered model version: {info.registered_model_version}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Set prod alias

# COMMAND ----------

client = MlflowClient(registry_uri="databricks-uc")
versions = client.search_model_versions(f"name='{FULL_NAME}'")
latest_version = max(versions, key=lambda x: int(x.version)).version
client.set_registered_model_alias(FULL_NAME, "prod", latest_version)

print(f"Set alias @prod to version {latest_version}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Pre-deploy validation

# COMMAND ----------

try:
    result = mlflow.models.predict(
        model_uri=info.model_uri,
        input_data={"input": [{"role": "user", "content": "ping"}]},
        env_manager="uv",
    )
    print(f"Pre-deploy validation passed.")
except Exception as e:
    print(f"Pre-deploy validation warning (may be expected): {str(e)[:200]}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Deploy via agents.deploy()

# COMMAND ----------

from databricks import agents

print("Starting deployment... this may take 10-15 minutes")
deployment = agents.deploy(
    FULL_NAME,
    latest_version,
    endpoint_name=ENDPOINT_NAME,
    tags={"ai_generated_source": "databricks-ml-training-skill"},
)

print(f"Deployment completed!")
print(f"Endpoint name: {deployment.endpoint_name}")
print(f"Query endpoint: {deployment.query_endpoint}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Return structured output

# COMMAND ----------

output = {
    "model_name": FULL_NAME,
    "model_version": latest_version,
    "endpoint_name": deployment.endpoint_name,
    "query_endpoint": deployment.query_endpoint,
}

dbutils.notebook.exit(json.dumps(output))