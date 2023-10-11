# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import Optional
import kfp as kfp
import kfp.components as components
import kfp.dsl as dsl
from pipelines.components.vertex.component import elect_best_tabular_model, batch_prediction
from pipelines.components.bigquery.component import bq_flatten_tabular_binary_prediction_table, bq_flatten_tabular_regression_table
from pipelines.components.pubsub.component import send_pubsub_activation_msg

# elect_best_tabular_model = components.load_component_from_file(
#    os.path.join(os.path.dirname(__file__),'components/vertex/component_metadata/elect_best_tabular_model.yaml')
#  )


@dsl.pipeline()
def prediction_binary_classification_pl(
    project_id: str,
    location: Optional[str],
    model_display_name: str,
    model_metric_name: str,
    model_metric_threshold: float,
    number_of_models_considered: int,


    pubsub_activation_topic: str,
    pubsub_activation_type: str,

    bigquery_source: str,
    bigquery_destination_prefix: str,
    bq_unique_key: str,
    job_name_prefix: str,
    machine_type: str = "n1-standard-4",
    max_replica_count: int = 10,
    batch_size: int = 64,
    accelerator_count: int = 0,
    accelerator_type: str = None,
    generate_explanation: bool = False,

    threashold: float = 0.5,
    positive_label: str = 'true',



):

    purchase_propensity_label = elect_best_tabular_model(
        project=project_id,
        location=location,
        display_name=model_display_name,
        metric_name=model_metric_name,
        metric_threshold=model_metric_threshold,
        number_of_models_considered=number_of_models_considered,
    ).set_display_name('elect_best_model')

    predictions = batch_prediction(
        bigquery_source=bigquery_source,
        bigquery_destination_prefix=bigquery_destination_prefix,
        job_name_prefix=job_name_prefix,
        model=purchase_propensity_label.outputs['elected_model'],
        machine_type=machine_type,
        max_replica_count=max_replica_count,
        batch_size=batch_size,
        accelerator_count=accelerator_count,
        accelerator_type=accelerator_type,
        generate_explanation=generate_explanation
    )

    flatten_predictions = bq_flatten_tabular_binary_prediction_table(
        project_id=project_id,
        location=location,
        source_table=bigquery_source,
        predictions_table=predictions.outputs['destination_table'],
        bq_unique_key=bq_unique_key,
        threashold=threashold,
        positive_label=positive_label
    )

    send_pubsub_activation_msg(
        project=project_id,
        topic_name=pubsub_activation_topic,
        activation_type=pubsub_activation_type,
        predictions_table=flatten_predictions.outputs['destination_table'],
    )


@dsl.pipeline()
def prediction_regression_pl(
    project_id: str,
    location: Optional[str],
    model_display_name: str,
    model_metric_name: str,
    model_metric_threshold: float,
    number_of_models_considered: int,


    pubsub_activation_topic: str,
    pubsub_activation_type: str,

    bigquery_source: str,
    bigquery_destination_prefix: str,
    bq_unique_key: str,

    job_name_prefix: str,
    machine_type: str = "n1-standard-4",
    max_replica_count: int = 10,
    batch_size: int = 64,
    accelerator_count: int = 0,
    accelerator_type: str = None,
    generate_explanation: bool = False
):

    purchase_propensity_label = elect_best_tabular_model(
        project=project_id,
        location=location,
        display_name=model_display_name,
        metric_name=model_metric_name,
        metric_threshold=model_metric_threshold,
        number_of_models_considered=number_of_models_considered,
    ).set_display_name('elect_best_model')

    predictions = batch_prediction(
        bigquery_source=bigquery_source,
        bigquery_destination_prefix=bigquery_destination_prefix,
        job_name_prefix=job_name_prefix,
        model=purchase_propensity_label.outputs['elected_model'],
        machine_type=machine_type,
        max_replica_count=max_replica_count,
        batch_size=batch_size,
        accelerator_count=accelerator_count,
        accelerator_type=accelerator_type,
        generate_explanation=generate_explanation
    )

    flatten_predictions = bq_flatten_tabular_regression_table(
        project_id=project_id,
        location=location,
        source_table=bigquery_source,
        predictions_table=predictions.outputs['destination_table'],
        bq_unique_key=bq_unique_key
    )

    send_pubsub_activation_msg(
        project=project_id,
        topic_name=pubsub_activation_topic,
        activation_type=pubsub_activation_type,
        predictions_table=flatten_predictions.outputs['destination_table'],
    )
