from copy import deepcopy

from models import Master, Pod, Worker
from schedulers import CustomScheduler, DefaultScheduler, Scheduler
from statistics import calculate_statistics


def create_workers() -> list[Worker]:
    return [
        Worker("worker-a", total_cpu=8, total_memory=16, total_disk=120, network_latency=20),
        Worker("worker-b", total_cpu=6, total_memory=12, total_disk=80, network_latency=35),
        Worker("worker-c", total_cpu=10, total_memory=24, total_disk=160, network_latency=15),
    ]


def create_pods() -> list[Pod]:
    return [
        Pod("pod-api", cpu=1.5, memory=2, disk=12, latency_requirement=30),
        Pod("pod-web", cpu=1, memory=1.5, disk=8, latency_requirement=40),
        Pod("pod-auth", cpu=2, memory=3, disk=10, latency_requirement=25),
        Pod("pod-payments", cpu=2.5, memory=4, disk=20, latency_requirement=20),
        Pod("pod-cache", cpu=1, memory=5, disk=6, latency_requirement=30),
        Pod("pod-database", cpu=3, memory=6, disk=50, latency_requirement=45),
        Pod("pod-logs", cpu=1.5, memory=2, disk=35, latency_requirement=60),
        Pod("pod-metrics", cpu=1, memory=2, disk=18, latency_requirement=50),
        Pod("pod-worker-1", cpu=2, memory=3.5, disk=22, latency_requirement=35),
        Pod("pod-worker-2", cpu=2, memory=3, disk=25, latency_requirement=30),
        Pod("pod-report", cpu=2.5, memory=5, disk=30, latency_requirement=55),
        Pod("pod-search", cpu=3, memory=4, disk=28, latency_requirement=25),
        Pod("pod-notification", cpu=1, memory=1, disk=5, latency_requirement=80),
        Pod("pod-queue", cpu=1.5, memory=2.5, disk=15, latency_requirement=45),
        Pod("pod-ml", cpu=4, memory=8, disk=45, latency_requirement=70),
        Pod("pod-realtime", cpu=1.5, memory=2, disk=10, latency_requirement=18),
    ]


def run_comparison() -> None:
    base_workers = create_workers()
    base_pods = create_pods()

    simulations = [
        (DefaultScheduler(), deepcopy(base_workers), deepcopy(base_pods)),
        (CustomScheduler(), deepcopy(base_workers), deepcopy(base_pods)),
    ]

    print("SIMULACAO DE ESCALONAMENTO DE PODS")
    print("=" * 72)
    print("Comparacao usando os mesmos Workers e Pods em dois schedulers.\n")

    for scheduler, workers, pods in simulations:
        master = Master("master-1", scheduler.name, workers)
        run_simulation(master, pods, scheduler)


def run_simulation(master: Master, pods: list[Pod], scheduler: Scheduler) -> None:
    print(f"MASTER: {master.name}")
    print(f"SCHEDULER: {master.scheduler_name}")
    print("-" * 72)

    pending_pods = scheduler.schedule(pods, master.workers)

    print_allocations(master.workers, pending_pods)
    print_resources(master.workers)
    print_statistics(pods, master.workers)
    print("\n" + "=" * 72 + "\n")


def print_allocations(workers: list[Worker], pending_pods: list[Pod]) -> None:
    print("ALOCACAO FINAL DOS PODS")

    for worker in workers:
        pod_names = [pod.name for pod in worker.pods]
        allocated = ", ".join(pod_names) if pod_names else "nenhum Pod alocado"
        print(f"- {worker.name}: {allocated}")

    if pending_pods:
        pending_names = ", ".join(pod.name for pod in pending_pods)
        print(f"- pending/rejected: {pending_names}")
    else:
        print("- pending/rejected: nenhum")

    print()


def print_resources(workers: list[Worker]) -> None:
    print("RECURSOS POR WORKER")

    for worker in workers:
        print(
            f"- {worker.name}: "
            f"CPU {worker.used_cpu:.1f}/{worker.total_cpu} usada, "
            f"{worker.available_cpu:.1f} disponivel | "
            f"Memoria {worker.used_memory:.1f}/{worker.total_memory} GB usada, "
            f"{worker.available_memory:.1f} GB disponivel | "
            f"Disco {worker.used_disk:.1f}/{worker.total_disk} GB usado, "
            f"{worker.available_disk:.1f} GB disponivel | "
            f"Latencia {worker.network_latency:.0f} ms"
        )

    print()


def print_statistics(pods: list[Pod], workers: list[Worker]) -> None:
    stats = calculate_statistics(pods, workers)

    print("ESTATISTICAS FINAIS")
    print(f"- Total de Pods: {stats['total_pods']}")
    print(f"- Pods alocados: {stats['allocated_pods']}")
    print(f"- Pods pendentes: {stats['pending_pods']}")
    print(f"- Uso medio de CPU por Worker: {stats['average_cpu_usage']:.2f}%")
    print(f"- Uso medio de memoria por Worker: {stats['average_memory_usage']:.2f}%")
    print(f"- Uso medio de disco por Worker: {stats['average_disk_usage']:.2f}%")
