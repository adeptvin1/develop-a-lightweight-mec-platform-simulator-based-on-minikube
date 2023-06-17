from collections import UserList, defaultdict
from datetime import datetime
from kubernetes import client, config
import requests
import json
import asyncio
import logging

async def log_connection(mode, data):
    log_time = (datetime.now()).strftime("%d.%m.%Y_%H:%M:%S")
    logging.basicConfig(filename =("./log/" + log_time + ".log"), level=logging.INFO)
    if mode == "debug":
        logging.debug("Connection" + " " + data + " " + log_time)
    elif mode == "info":
        logging.info("Connection" + " " + data +  " " + log_time)
    elif mode == "error":
        logging.error("Connection" + " " + data + " " + log_time)

async def rest_api(delay, zone):
    api_id = "sbxfgqbt9g"
    api_url = "https://try-mec.etsi.org/" + api_id + "/mep1/location/v2/queries/zones/" + zone
    print(api_url)
    response = requests.get(api_url)
    if response:
        await asyncio.sleep(delay)
        await log_connection("info", "established")
        return response.json()
        response = ""
    else:
        await log_connection("error", "error")

async def deploy_kubernetes_deployment(namespace, deployment_name, image, replicas, node_affinity_value):
    # Load Kubernetes configuration from default location or provide your own kubeconfig file path
    config.load_kube_config()

    # Create the Kubernetes API client
    api_client = client.AppsV1Api()

    # Create the deployment object
    deployment = client.V1Deployment(
        metadata=client.V1ObjectMeta(name=deployment_name, namespace=namespace),
        spec=client.V1DeploymentSpec(
            replicas=replicas,
            selector=client.V1LabelSelector(
                match_labels={"app": deployment_name}
            ),
            template=client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(labels={"app": deployment_name}),
                spec=client.V1PodSpec(
                    containers=[
                        client.V1Container(
                            name=deployment_name,
                            image=image,
                            ports=[client.V1ContainerPort(container_port=80)]  # Adjust the container port as needed
                        )
                    ],
                    affinity=client.V1Affinity(
                        node_affinity=client.V1NodeAffinity(
                            required_during_scheduling_ignored_during_execution=client.V1NodeSelector(
                                node_selector_terms=[
                                    client.V1NodeSelectorTerm(
                                        match_expressions=[
                                            client.V1NodeSelectorRequirement(
                                                key="zone",
                                                operator="In",
                                                values=[node_affinity_value]
                                            )
                                        ]
                                    )
                                ]
                            )
                        )
                    )
                )
            )
        )
    )

    # Create the deployment in Kubernetes
    api_client.create_namespaced_deployment(namespace, deployment)

    print(f"Deployment '{deployment_name}' created successfully.")

async def initiate_deployment(zone):
    await deploy_kubernetes_deployment("default", "test-app-" + zone, "nginx", 0, zone)

async def update_kubernetes_deployment(namespace, deployment_name, replicas):

    # Create the Kubernetes API client
    api_client = client.AppsV1Api()

    # Retrieve the existing deployment
    deployment = api_client.read_namespaced_deployment(deployment_name, namespace)

    # Update the deployment's container image
    deployment.spec.replicas = replicas

    # Patch the deployment
    api_client.patch_namespaced_deployment(deployment_name, namespace, deployment)

    print(f"Deployment '{deployment_name}' updated successfully.")

async def app_deployment(zone, users):
    # TODO: refactor it
    if users >= 1:
        replicas = 1
    if users >= 2:
        replicas = 2
    await update_kubernetes_deployment("default", "test-app-" + zone, replicas)


async def main():
    # vars for collect data and send to mongodb base
    config.load_kube_config()
    time_data_collect = 1
    list_zone = ["zone01", "zone02", "zone03", "zone04"]
    # TODO: Add check on existing deployments
    for zone in list_zone:
        await initiate_deployment(zone)

    while time_data_collect == 1:
        rawdata = dict()
        data = dict()
        count_of_ue = dict()
        for zone in list_zone:
            rawdata[zone] = await rest_api(10, zone)
            
            data[zone] = json.loads(json.dumps(rawdata[zone]))

        for zone in data:
            count_of_ue[zone] = data[zone]["zoneInfo"]["numberOfUsers"]
            print(count_of_ue[zone])

        for k in count_of_ue:
            if count_of_ue[k] > 1:
                await app_deployment(k, count_of_ue[k])
            else:
                pass
        

if __name__ == "__main__":
    asyncio.run(main())

