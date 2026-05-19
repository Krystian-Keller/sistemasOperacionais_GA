from copy import deepcopy
from threading import Lock, Semaphore, Thread

from models import Master, Pod, Worker
from schedulers import CustomScheduler, DefaultScheduler, Scheduler
from statistics import calculate_statistics

BUFFER_CAPACITY = 5


class PodBuffer:
    def __init__(self, capacity: int) -> None:
        self.capacity = capacity
        self.items: list[Pod | None] = []
        self.empty_slots = Semaphore(capacity)
        self.available_items = Semaphore(0)
        self.mutex = Lock()

    def put(self, item: Pod | None) -> None:
        self.empty_slots.acquire()
        with self.mutex:
            self.items.append(item)
        self.available_items.release()

    def get(self) -> Pod | None:
        self.available_items.acquire()
        with self.mutex:
            item = self.items.pop(0)
        self.empty_slots.release()
        return item


def create_workers() -> list[Worker]:
    return [
        Worker("worker-a-fast", total_cpu=8, total_memory=16, total_disk=70, network_latency=12),
        Worker("worker-b-storage", total_cpu=8, total_memory=16, total_disk=180, network_latency=38),
        Worker("worker-c-balanced", total_cpu=10, total_memory=28, total_disk=130, network_latency=22),
    ]


def create_pods() -> list[Pod]:
    return [
        Pod("pod-realtime-chat", cpu=1, memory=1.5, disk=8, latency_requirement=15),
        Pod("pod-payments-low-latency", cpu=2, memory=3, disk=12, latency_requirement=20),
        Pod("pod-api", cpu=1.5, memory=2, disk=10, latency_requirement=30),
        Pod("pod-video-ingest", cpu=1, memory=2, disk=55, latency_requirement=60),
        Pod("pod-backup", cpu=1, memory=1, disk=70, latency_requirement=80),
        Pod("pod-logs", cpu=1.5, memory=2, disk=45, latency_requirement=70),
        Pod("pod-analytics-cpu", cpu=4, memory=4, disk=18, latency_requirement=55),
        Pod("pod-search-cpu", cpu=3.5, memory=3, disk=15, latency_requirement=35),
        Pod("pod-cache-memory", cpu=1, memory=7, disk=8, latency_requirement=30),
        Pod("pod-report-memory", cpu=2, memory=8, disk=20, latency_requirement=50),
        Pod("pod-database", cpu=3, memory=6, disk=50, latency_requirement=45),
        Pod("pod-metrics", cpu=1, memory=2, disk=12, latency_requirement=45),
        Pod("pod-queue", cpu=1.5, memory=2.5, disk=14, latency_requirement=40),
        Pod("pod-notification", cpu=1, memory=1, disk=5, latency_requirement=90),
        Pod("pod-ml-batch", cpu=4.5, memory=9, disk=40, latency_requirement=75),
        Pod("pod-fraud-detection", cpu=2.5, memory=4, disk=18, latency_requirement=18),
        Pod("pod-archive-huge-disk", cpu=1, memory=1, disk=95, latency_requirement=100),
        Pod("pod-memory-big", cpu=2, memory=12, disk=16, latency_requirement=65),
    ]


def run_comparison(verbose: bool = False) -> list[dict]:
    base_workers = create_workers()
    base_pods = create_pods()

    simulations = [
        (DefaultScheduler(), deepcopy(base_workers), deepcopy(base_pods)),
        (CustomScheduler(), deepcopy(base_workers), deepcopy(base_pods)),
    ]

    print("SIMULACAO DE ESCALONAMENTO DE PODS")
    print("=" * 72)
    print("Comparacao usando os mesmos Workers e Pods em dois schedulers.\n")

    results = []

    for scheduler, workers, pods in simulations:
        master = Master("master-1", scheduler.name, workers)
        results.append(run_simulation(master, pods, scheduler, verbose))

    print_comparison_table(results)
    return results


def run_simulation(
    master: Master, pods: list[Pod], scheduler: Scheduler, verbose: bool
) -> dict:
    print(f"MASTER: {master.name}")
    print(f"SCHEDULER: {master.scheduler_name}")
    print("-" * 72)

    pending_pods = run_producer_consumer(master, pods, scheduler, verbose)

    if verbose:
        print_allocations(master.workers, pending_pods)
        print_resources(master.workers)

    stats = print_statistics(pods, master.workers)

    if verbose:
        print_rejection_reasons(pending_pods)

    print("\n" + "=" * 72 + "\n")
    return {
        "scheduler": master.scheduler_name,
        "scheduler_label": scheduler_label(scheduler),
        "stats": stats,
        "workers": master.workers,
    }


def scheduler_label(scheduler: Scheduler) -> str:
    if isinstance(scheduler, DefaultScheduler):
        return "default"
    if isinstance(scheduler, CustomScheduler):
        return "custom"
    return scheduler.name.lower().replace(" ", "_")


def run_producer_consumer(
    master: Master, pods: list[Pod], scheduler: Scheduler, verbose: bool
) -> list[Pod]:
    buffer = PodBuffer(BUFFER_CAPACITY)
    pending_pods: list[Pod] = []

    producer = Thread(
        target=produce_pods,
        args=(pods, buffer, verbose),
        name=f"producer-{scheduler.name}",
    )
    consumer = Thread(
        target=consume_pods,
        args=(master, scheduler, buffer, pending_pods, verbose),
        name=f"consumer-{scheduler.name}",
    )

    if verbose:
        print(f"BUFFER COMPARTILHADO: capacidade maxima de {BUFFER_CAPACITY} Pods")

    consumer.start()
    producer.start()
    producer.join()
    consumer.join()

    if verbose:
        print()

    return pending_pods


def produce_pods(pods: list[Pod], buffer: PodBuffer, verbose: bool) -> None:
    for pod in pods:
        log_verbose(verbose, f"[Produtor] Pod criado: {pod.name}")
        log_verbose(verbose, "[Produtor] aguardando espaco no buffer")
        buffer.put(pod)
        log_verbose(verbose, f"[Produtor] Pod inserido no buffer: {pod.name}")

    log_verbose(verbose, "[Produtor] aguardando espaco no buffer")
    buffer.put(None)
    log_verbose(verbose, "[Produtor] sentinel None inserido no buffer")


def consume_pods(
    master: Master,
    scheduler: Scheduler,
    buffer: PodBuffer,
    pending_pods: list[Pod],
    verbose: bool,
) -> None:
    while True:
        log_verbose(verbose, "[Consumidor/Master] aguardando item no buffer")
        pod = buffer.get()

        if pod is None:
            log_verbose(
                verbose,
                "[Consumidor/Master] sentinel None recebido; encerrando consumidor",
            )
            break

        log_verbose(verbose, f"[Consumidor/Master] Scheduler consumindo Pod: {pod.name}")
        worker = scheduler.select_worker(pod, master.workers)

        if worker is None:
            pod.status = "pending"
            pod.rejection_reason = scheduler.rejection_reason(pod, master.workers)
            pending_pods.append(pod)
            log_verbose(verbose, "[Consumidor/Master] Worker escolhido: nenhum")
            log_verbose(
                verbose,
                "[Consumidor/Master] Pod marcado como pending/rejected: "
                f"{pod.name} ({pod.rejection_reason})",
            )
        else:
            log_verbose(verbose, f"[Consumidor/Master] Worker escolhido: {worker.name}")
            worker.allocate(pod)
            log_verbose(
                verbose, f"[Consumidor/Master] Pod alocado: {pod.name} -> {worker.name}"
            )


def log_verbose(verbose: bool, message: str) -> None:
    if verbose:
        print(message)


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
        disk_text = _format_disk_usage(worker)
        print(
            f"- {worker.name}: "
            f"CPU {worker.used_cpu:.1f}/{worker.total_cpu} usada, "
            f"{worker.available_cpu:.1f} disponivel | "
            f"Memoria {worker.used_memory:.1f}/{worker.total_memory} GB usada, "
            f"{worker.available_memory:.1f} GB disponivel | "
            f"{disk_text} | "
            f"Latencia {worker.network_latency:.0f} ms"
        )

    print()


def _format_disk_usage(worker: Worker) -> str:
    if worker.used_disk > worker.total_disk:
        overcommit = worker.used_disk - worker.total_disk
        return (
            f"Disco {worker.used_disk:.1f}/{worker.total_disk} GB usado, "
            f"OVERCOMMIT de {overcommit:.1f} GB"
        )

    return (
        f"Disco {worker.used_disk:.1f}/{worker.total_disk} GB usado, "
        f"{worker.available_disk:.1f} GB disponivel"
    )


def print_statistics(pods: list[Pod], workers: list[Worker]) -> dict:
    stats = calculate_statistics(pods, workers)

    print("ESTATISTICAS FINAIS")
    print(f"- Total de Pods: {stats['total_pods']}")
    print(f"- Pods alocados totais: {stats['allocated_pods']}")
    print(f"- Pods alocados validos: {stats['valid_allocated_pods']}")
    print(
        "- Pods alocados com violacao de recurso ou latencia: "
        f"{stats['allocated_pods_with_violation']}"
    )
    print(f"- Pods pendentes: {stats['pending_pods']}")
    print(f"- Uso medio de CPU por Worker: {stats['average_cpu_usage']:.2f}%")
    print(f"- Uso medio de memoria por Worker: {stats['average_memory_usage']:.2f}%")
    print(f"- Uso medio de disco por Worker: {stats['average_disk_usage']:.2f}%")
    print(f"- Workers com CPU acima de 90%: {stats['workers_cpu_above_90']}")
    print(f"- Workers com memoria acima de 90%: {stats['workers_memory_above_90']}")
    print(f"- Workers com disco acima de 90%: {stats['workers_disk_above_90']}")
    print(f"- Violacoes de latencia: {stats['latency_violations']}")
    print(f"- Overcommit de disco total: {stats['total_disk_overcommit']:.1f} GB")
    return stats


def print_rejection_reasons(pending_pods: list[Pod]) -> None:
    print()
    print("MOTIVOS DE REJEICAO")

    if not pending_pods:
        print("- nenhum Pod rejeitado")
        return

    for pod in pending_pods:
        print(f"- {pod.name}: {pod.rejection_reason}")


def print_comparison_table(results: list[dict]) -> None:
    print("TABELA COMPARATIVA FINAL")
    print("=" * 100)

    headers = ["Metrica"] + [result["scheduler"] for result in results]
    rows = [
        ("Pods alocados totais", "allocated_pods"),
        ("Pods alocados validos", "valid_allocated_pods"),
        ("Pods com violacao", "allocated_pods_with_violation"),
        ("Pods pendentes", "pending_pods"),
        ("Uso medio CPU", "average_cpu_usage"),
        ("Uso medio memoria", "average_memory_usage"),
        ("Uso medio disco", "average_disk_usage"),
        ("Overcommit disco total", "total_disk_overcommit"),
        ("Workers CPU > 90%", "workers_cpu_above_90"),
        ("Workers memoria > 90%", "workers_memory_above_90"),
        ("Workers disco > 90%", "workers_disk_above_90"),
        ("Violacoes de latencia", "latency_violations"),
    ]

    widths = [26, 35, 43]
    print(_format_row(headers, widths))
    print("-" * 100)

    for label, key in rows:
        values = [label]
        for result in results:
            value = result["stats"][key]
            if key == "total_disk_overcommit":
                values.append(f"{value:.1f} GB")
            elif isinstance(value, float):
                values.append(f"{value:.2f}%")
            else:
                values.append(str(value))
        print(_format_row(values, widths))

    print()


def _format_row(values: list[str], widths: list[int]) -> str:
    return " | ".join(value.ljust(width) for value, width in zip(values, widths))
