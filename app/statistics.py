from models import Pod, Worker


def calculate_statistics(pods: list[Pod], workers: list[Worker]) -> dict[str, float | int]:
    total_pods = len(pods)
    allocated_pods = len([pod for pod in pods if pod.status == "running"])
    allocated_with_violation = count_allocated_pods_with_violation(workers)
    pending_pods = total_pods - allocated_pods
    worker_count = len(workers)

    return {
        "total_pods": total_pods,
        "allocated_pods": allocated_pods,
        "valid_allocated_pods": allocated_pods - allocated_with_violation,
        "allocated_pods_with_violation": allocated_with_violation,
        "pending_pods": pending_pods,
        "average_cpu_usage": _average_usage(workers, "used_cpu", "total_cpu", worker_count),
        "average_memory_usage": _average_usage(
            workers, "used_memory", "total_memory", worker_count
        ),
        "average_disk_usage": _average_usage(
            workers, "used_disk", "total_disk", worker_count
        ),
        "workers_cpu_above_90": _count_workers_above(workers, "used_cpu", "total_cpu", 0.90),
        "workers_memory_above_90": _count_workers_above(
            workers, "used_memory", "total_memory", 0.90
        ),
        "workers_disk_above_90": _count_workers_above(
            workers, "used_disk", "total_disk", 0.90
        ),
        "latency_violations": count_latency_violations(workers),
        "total_disk_overcommit": total_disk_overcommit(workers),
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


def _count_workers_above(
    workers: list[Worker], used_attribute: str, total_attribute: str, limit: float
) -> int:
    return len(
        [
            worker
            for worker in workers
            if getattr(worker, used_attribute) / getattr(worker, total_attribute) > limit
        ]
    )


def count_latency_violations(workers: list[Worker]) -> int:
    violations = 0

    for worker in workers:
        violations += len(
            [pod for pod in worker.pods if worker.network_latency > pod.latency_requirement]
        )

    return violations


def count_allocated_pods_with_violation(workers: list[Worker]) -> int:
    invalid_pods = set()

    for worker in workers:
        has_resource_violation = (
            worker.used_cpu > worker.total_cpu
            or worker.used_memory > worker.total_memory
            or worker.used_disk > worker.total_disk
        )

        for pod in worker.pods:
            has_latency_violation = worker.network_latency > pod.latency_requirement
            if has_resource_violation or has_latency_violation:
                invalid_pods.add(pod.name)

    return len(invalid_pods)


def total_disk_overcommit(workers: list[Worker]) -> float:
    return sum(max(0, worker.used_disk - worker.total_disk) for worker in workers)
