# Dagger Workflow Templates

This document describes the workflow templates feature for the Dagger Workflow Integration in the AI-Orchestration-Platform.

## Overview

Workflow templates provide pre-defined workflow patterns that can be customized and instantiated for specific tasks. Templates include common patterns such as CI/CD pipelines, data processing, ML training, and scheduled maintenance workflows.

## Available Templates

The following templates are available out of the box:

### CI/CD Pipeline Template

A standard CI/CD pipeline for software projects with the following stages:

1. **Build**: Compile and lint the code
2. **Test**: Run tests
3. **Package**: Create deployment artifacts
4. **Deploy**: Deploy to target environment
5. **Notify**: Send deployment notification

**Template ID**: `cicd_pipeline`

**Customizable Parameters**:
- `build_image`: Docker image for building (default: `python:3.9-slim`)
- `test_framework`: Testing framework to use (default: `pytest`)
- `artifact_type`: Type of artifact to create (default: `docker`)
- `deployment_target`: Target environment for deployment (default: `kubernetes`)
- `notification_channel`: Channel for notifications (default: `slack`)

### Data Processing Template

An ETL workflow for data processing and transformation with the following stages:

1. **Extract**: Extract data from source
2. **Validate**: Validate data quality
3. **Transform**: Transform data
4. **Load**: Load data to destination
5. **Report**: Generate processing report

**Template ID**: `data_processing`

**Customizable Parameters**:
- `source_type`: Type of data source (default: `csv`)
- `source_path`: Path to source data (default: `/data/raw/`)
- `destination_type`: Type of destination (default: `database`)
- `destination_path`: Path to destination (default: `postgresql://user:pass@localhost:5432/db`)
- `validation_rules`: Rules for data validation (default: `basic`)

### ML Training Template

An end-to-end machine learning model training workflow with the following stages:

1. **Data Preprocessing**: Prepare and clean the dataset
2. **Feature Engineering**: Create and select features
3. **Model Training**: Train the machine learning model
4. **Model Evaluation**: Evaluate model performance
5. **Model Deployment**: Deploy the model if it meets criteria

**Template ID**: `ml_training`

**Customizable Parameters**:
- `dataset_path`: Path to the dataset (default: `/data/raw/dataset.csv`)
- `model_type`: Type of model to train (default: `gradient_boosting`)
- `hyperparameters`: Model hyperparameters (default: `{"n_estimators": 100, "learning_rate": 0.1, "max_depth": 5}`)
- `target_column`: Target column for prediction (default: `target`)
- `test_size`: Size of test set (default: `0.2`)
- `random_state`: Random state for reproducibility (default: `42`)

### Scheduled Maintenance Template

An automated system maintenance and health check workflow with the following stages:

1. **Health Check**: Check system health
2. **Backup**: Create system backups
3. **Cleanup**: Clean up old files and logs
4. **Verification**: Verify system integrity after maintenance
5. **Reporting**: Generate maintenance report

**Template ID**: `scheduled_maintenance`

**Customizable Parameters**:
- `target_systems`: Systems to maintain (default: `["database", "api", "frontend"]`)
- `backup_destination`: Destination for backups (default: `/backups/`)
- `retention_days`: Number of days to retain files (default: `30`)
- `notification_email`: Email for notifications (default: `admin@example.com`)

## Using Templates with MCP Tools

The Dagger Workflow Integration MCP server provides the following tools for working with templates:

### List Workflow Templates

List all available workflow templates, optionally filtered by category.

```json
{
  "name": "list_workflow_templates",
  "description": "List available workflow templates",
  "inputSchema": {
    "type": "object",
    "properties": {
      "category": {
        "type": "string",
        "description": "Optional category to filter templates"
      }
    }
  }
}
```

Example response:

```json
{
  "templates": [
    {
      "template_id": "cicd_pipeline",
      "name": "CI/CD Pipeline",
      "description": "Standard CI/CD pipeline for software projects",
      "category": "deployment",
      "version": "1.0.0"
    },
    {
      "template_id": "data_processing",
      "name": "Data Processing Pipeline",
      "description": "ETL workflow for data processing and transformation",
      "category": "data",
      "version": "1.0.0"
    }
  ],
  "categories": [
    "deployment",
    "data",
    "machine_learning",
    "operations"
  ],
  "count": 2
}
```

### Get Workflow Template

Get details of a specific workflow template.

```json
{
  "name": "get_workflow_template",
  "description": "Get details of a specific workflow template",
  "inputSchema": {
    "type": "object",
    "properties": {
      "template_id": {
        "type": "string",
        "description": "ID of the template to retrieve"
      }
    },
    "required": ["template_id"]
  }
}
```

Example response:

```json
{
  "template_id": "cicd_pipeline",
  "name": "CI/CD Pipeline",
  "description": "Standard CI/CD pipeline for software projects",
  "category": "deployment",
  "version": "1.0.0",
  "parameters": {
    "build_image": "python:3.9-slim",
    "test_framework": "pytest",
    "artifact_type": "docker",
    "deployment_target": "kubernetes",
    "notification_channel": "slack"
  },
  "stages": [
    {
      "id": "build",
      "name": "Build",
      "description": "Compile and lint the code",
      "agent": "builder",
      "inputs": {
        "image": "${parameters.build_image}",
        "commands": [
          "pip install -r requirements.txt",
          "flake8 .",
          "mypy ."
        ]
      }
    },
    // Additional stages...
  ],
  "metadata": {
    "tags": ["cicd", "deployment", "automation"],
    "complexity": "medium",
    "estimated_duration": "30m"
  }
}
```

### Create Workflow from Template

Create a workflow from a template for a specific task.

```json
{
  "name": "create_workflow_from_template",
  "description": "Create a workflow from a template",
  "inputSchema": {
    "type": "object",
    "properties": {
      "task_id": {
        "type": "string",
        "description": "ID of the task to create a workflow for"
      },
      "template_id": {
        "type": "string",
        "description": "ID of the template to use"
      },
      "parameters": {
        "type": "object",
        "description": "Custom parameters for the template"
      }
    },
    "required": ["task_id", "template_id"]
  }
}
```

Example request:

```json
{
  "task_id": "task_12345",
  "template_id": "cicd_pipeline",
  "parameters": {
    "build_image": "node:18-alpine",
    "test_framework": "jest",
    "deployment_target": "aws"
  }
}
```

Example response:

```json
{
  "workflow_id": "workflow_67890",
  "task_id": "task_12345",
  "name": "CI/CD Pipeline for Task task_12345",
  "template_id": "cicd_pipeline",
  "template_name": "CI/CD Pipeline"
}
```

## Creating Custom Templates

You can create custom templates by defining them in YAML files and placing them in a templates directory. The template registry will automatically load templates from this directory.

Example template YAML file:

```yaml
template_id: custom_template
name: Custom Template
description: A custom workflow template
category: custom
version: 1.0.0
parameters:
  param1: default_value1
  param2: default_value2
stages:
  - id: stage1
    name: Stage 1
    description: First stage
    agent: agent1
    inputs:
      input1: ${parameters.param1}
      input2: value2
  - id: stage2
    name: Stage 2
    description: Second stage
    agent: agent2
    depends_on: [stage1]
    inputs:
      input1: ${parameters.param2}
      input2: value2
metadata:
  tags: [custom, example]
  complexity: low
  estimated_duration: 10m
```

## Template Customization

Templates can be customized by providing custom parameters when creating a workflow from a template. The custom parameters will override the default parameters defined in the template.

Parameter substitution is supported in template stages using the `${parameters.param_name}` syntax. For example, if a template has a parameter `build_image` with a default value of `python:3.9-slim`, you can override it by providing a custom parameter `build_image: node:18-alpine` when creating a workflow from the template.

## Integration with Task Management

Workflows created from templates are associated with tasks in the task management system. When a workflow is executed, the task status is updated based on the workflow execution result.

## Future Enhancements

Future enhancements to the workflow templates feature may include:

- Template versioning and migration
- Template sharing and import/export
- Template validation and testing
- Template visualization
- Template composition (combining multiple templates)
- Template inheritance (extending existing templates)
