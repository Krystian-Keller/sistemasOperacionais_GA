from models import Pod, Worker


def calculate_statistics(pods: list[Pod], workers: list[Worker]) -> dict[str, float]:
    total_pods = len(pods)
    allocated_pods = len([pod for pod in pods if pod.status == "running"])
    pending_pods = total_pods - allocated_pods
    worker_count = len(workers)

    return {
        "total_pods": total_pods,
        "allocated_pods": allocated_pods,
        "pending_pods": pending_pods,
        "average_cpu_usage": _average_usage(workers, "used_cpu", "total_cpu", worker_count),
        "average_memory_usage": _average_usage(
            workers, "used_memory", "total_memory", worker_count
        ),
        "average_disk_usage": _average_usage(
            workers, "used_disk", "total_disk", worker_count
        ),
    }


def _average_usage(
    workers: list[Worker], used_attribute: str, total_attribute: str, worker_count: int
) -> float:
    if worker_count == 0:
        return 0

    usage_sum = sum(
        getattr(worker, used_attribute) / getattr(worker, total_attribute)
        for worker in workers
    )

    return (usage_sum / worker_count) * 100
