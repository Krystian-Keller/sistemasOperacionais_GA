from copy import deepcopy
from dataclasses import dataclass, field
from random import Random
from time import sleep

from metrics import export_metrics
from models import Master, Pod, Worker
from schedulers import CustomScheduler, DefaultScheduler, Scheduler
from simulation import create_workers, run_producer_consumer, scheduler_label
from statistics import count_allocated_pods_with_violation, count_latency_violations
from statistics import total_disk_overcommit


@dataclass
class ContinuousState:
    scheduler: Scheduler
    workers: list[Worker]
    all_pods: list[Pod] = field(default_factory=list)
    pending_pods: list[Pod] = field(default_factory=list)


POD_PROFILES = [
    ("api", 1.0, 2.0, 10.0, 30.0),
    ("batch-cpu", 3.5, 3.0, 18.0, 60.0),
    ("cache-memory", 1.0, 6.0, 8.0, 35.0),
    ("log-disk", 1.5, 2.0, 45.0, 70.0),
    ("archive-disk", 1.0, 1.0, 65.0, 90.0),
    ("realtime", 1.5, 2.0, 10.0, 18.0),
    ("analytics", 2.5, 5.0, 25.0, 50.0),
    ("memory-big", 2.0, 9.0, 16.0, 65.0),
]


def run_continuous_simulation(
    cycle_seconds: int = 5, pods_per_cycle: int = 4, seed: int = 42, verbose: bool = False
) -> None:
    states = [
        ContinuousState(DefaultScheduler(), create_workers()),
        ContinuousState(CustomScheduler(), create_workers()),
    ]
    random = Random(seed)
    cycle = 0

    print("SIMULACAO CONTINUA ATIVA")
    print(f"Intervalo entre ciclos: {cycle_seconds}s")
    print(f"Pods novos por ciclo: {pods_per_cycle}")
    print("Metricas Prometheus serao atualizadas a cada ciclo.\n")

    while True:
        cycle += 1
        cycle_pods = generate_cycle_pods(cycle, pods_per_cycle, random)
        results = []

        print(f"CICLO {cycle}: gerando {len(cycle_pods)} Pods")

        for state in states:
            expire_running_pods(state.workers)
            new_pods = deepcopy(cycle_pods)
            state.all_pods.extend(new_pods)

            master = Master(
                "master-1",
                state.scheduler.name,
                state.workers,
            )
            pending = run_producer_consumer(master, new_pods, state.scheduler, verbose)
            state.pending_pods.extend(pending)
            results.append(build_result(state))

        export_metrics(results, cycle=cycle)
        print("Metricas atualizadas para Prometheus.\n")
        sleep(cycle_seconds)


def generate_cycle_pods(cycle: int, amount: int, random: Random) -> list[Pod]:
    pods = []

    for index in range(amount):
        profile = random.choice(POD_PROFILES)
        name, cpu, memory, disk, latency = profile
        duration = random.randint(2, 5)
        pods.append(
            Pod(
                name=f"pod-{name}-c{cycle}-{index + 1}",
                cpu=cpu,
                memory=memory,
                disk=disk,
                latency_requirement=latency,
                duration_cycles=duration,
            )
        )

    return pods


def expire_running_pods(workers: list[Worker]) -> None:
    for worker in workers:
        for pod in list(worker.pods):
            if pod.duration_cycles is None:
                continue

            pod.duration_cycles -= 1
            if pod.duration_cycles <= 0:
                worker.remove(pod)


def build_result(state: ContinuousState) -> dict:
    stats = calculate_continuous_statistics(state)
    return {
        "scheduler": state.scheduler.name,
        "scheduler_label": scheduler_label(state.scheduler),
        "stats": stats,
        "workers": state.workers,
    }


def calculate_continuous_statistics(state: ContinuousState) -> dict[str, float | int]:
    running_pods = [pod for worker in state.workers for pod in worker.pods]
    allocated_with_violation = count_allocated_pods_with_violation(state.workers)
    worker_count = len(state.workers)

    return {
        "total_pods": len(state.all_pods),
        "allocated_pods": len(running_pods),
        "valid_allocated_pods": len(running_pods) - allocated_with_violation,
        "allocated_pods_with_violation": allocated_with_violation,
        "pending_pods": len([pod for pod in state.all_pods if pod.status == "pending"]),
        "average_cpu_usage": average_usage(
            state.workers, "used_cpu", "total_cpu", worker_count
        ),
        "average_memory_usage": average_usage(
            state.workers, "used_memory", "total_memory", worker_count
        ),
        "average_disk_usage": average_usage(
            state.workers, "used_disk", "total_disk", worker_count
        ),
        "workers_cpu_above_90": count_workers_above(
            state.workers, "used_cpu", "total_cpu", 0.90
        ),
        "workers_memory_above_90": count_workers_above(
            state.workers, "used_memory", "total_memory", 0.90
        ),
        "workers_disk_above_90": count_workers_above(
            state.workers, "used_disk", "total_disk", 0.90
        ),
        "latency_violations": count_latency_violations(state.workers),
        "total_disk_overcommit": total_disk_overcommit(state.workers),
    }


def average_usage(
    workers: list[Worker], used_attribute: str, total_attribute: str, worker_count: int
) -> float:
    if worker_count == 0:
        return 0

    usage_sum = sum(
        getattr(worker, used_attribute) / getattr(worker, total_attribute)
        for worker in workers
    )
    return (usage_sum / worker_count) * 100


def count_workers_above(
    workers: list[Worker], used_attribute: str, total_attribute: str, limit: float
) -> int:
    return len(
        [
            worker
            for worker in workers
            if getattr(worker, used_attribute) / getattr(worker, total_attribute) > limit
        ]
    )
