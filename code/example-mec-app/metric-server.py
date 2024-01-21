from kubernetes import client, config

config.load_kube_config()


api = client.CustomObjectsApi()

pod_list = client.CoreV1Api().list_namespaced_pod('default')

for pod in pod_list.items:
    pod_name = pod.metadata.name
    pod_namespace = pod.metadata.namespace
    pod_phase = pod.status.phase
    pod_node = pod.spec.node_name

    print(f"Pod Name: {pod_name}, Located on Node: {pod_node}, Namespace: {pod_namespace}, Phase: {pod_phase}")

    try:
        api_response = api.get_namespaced_custom_object(
            group="metrics.k8s.io",
            version="v1beta1",
            namespace=pod_namespace,
            plural="pods",
            name=pod_name
        )

        containers = api_response['containers']
        if containers:
            metrics = containers[0]['usage']
            cpu_usage = metrics['cpu']
            memory_usage = metrics['memory']

            print(f"CPU Usage: {cpu_usage}")
            print(f"Memory Usage: {memory_usage}")
        else:
            print(f"Metrics not found for pod {pod_name}.")
        print('-' * 50)

    except Exception as e:
        print(f"Error fetching metrics for pod {pod_name}: {e}")

