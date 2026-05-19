from prometheus_client import Gauge, start_http_server

from models import Worker

pods_total = Gauge("pods_total", "Total de Pods da simulacao", ["scheduler"])
pods_allocated_total = Gauge(
    "pods_allocated_total", "Pods alocados totais", ["scheduler"]
)
pods_valid_allocated_total = Gauge(
    "pods_valid_allocated_total", "Pods alocados validos", ["scheduler"]
)
pods_with_violation_total = Gauge(
    "pods_with_violation_total",
    "Pods alocados com violacao de recurso ou latencia",
    ["scheduler"],
)
pods_pending_total = Gauge("pods_pending_total", "Pods pendentes", ["scheduler"])

worker_cpu_used = Gauge(
    "worker_cpu_used", "CPU usada por Worker", ["scheduler", "worker"]
)
worker_cpu_available = Gauge(
    "worker_cpu_available", "CPU disponivel por Worker", ["scheduler", "worker"]
)
worker_memory_used = Gauge(
    "worker_memory_used", "Memoria usada por Worker em GB", ["scheduler", "worker"]
)
worker_memory_available = Gauge(
    "worker_memory_available",
    "Memoria disponivel por Worker em GB",
    ["scheduler", "worker"],
)
worker_disk_used = Gauge(
    "worker_disk_used", "Disco usado por Worker em GB", ["scheduler", "worker"]
)
worker_disk_available = Gauge(
    "worker_disk_available",
    "Disco disponivel por Worker em GB, sem valores negativos",
    ["scheduler", "worker"],
)
worker_pods_allocated = Gauge(
    "worker_pods_allocated", "Pods alocados por Worker", ["scheduler", "worker"]
)
worker_disk_overcommit = Gauge(
    "worker_disk_overcommit",
    "Overcommit de disco por Worker em GB",
    ["scheduler", "worker"],
)
latency_violations_total = Gauge(
    "latency_violations_total", "Violacoes de latencia", ["scheduler"]
)


def start_metrics_server(port: int) -> None:
    start_http_server(port)


def export_metrics(results: list[dict]) -> None:
    for result in results:
        scheduler = result["scheduler_label"]
        stats = result["stats"]

        pods_total.labels(scheduler=scheduler).set(stats["total_pods"])
        pods_allocated_total.labels(scheduler=scheduler).set(stats["allocated_pods"])
        pods_valid_allocated_total.labels(scheduler=scheduler).set(
            stats["valid_allocated_pods"]
        )
        pods_with_violation_total.labels(scheduler=scheduler).set(
            stats["allocated_pods_with_violation"]
        )
        pods_pending_total.labels(scheduler=scheduler).set(stats["pending_pods"])
        latency_violations_total.labels(scheduler=scheduler).set(
            stats["latency_violations"]
        )

        for worker in result["workers"]:
            export_worker_metrics(scheduler, worker)


def export_worker_metrics(scheduler: str, worker: Worker) -> None:
    labels = {"scheduler": scheduler, "worker": worker.name}

    worker_cpu_used.labels(**labels).set(worker.used_cpu)
    worker_cpu_available.labels(**labels).set(max(0, worker.available_cpu))
    worker_memory_used.labels(**labels).set(worker.used_memory)
    worker_memory_available.labels(**labels).set(max(0, worker.available_memory))
    worker_disk_used.labels(**labels).set(worker.used_disk)
    worker_disk_available.labels(**labels).set(max(0, worker.available_disk))
    worker_pods_allocated.labels(**labels).set(len(worker.pods))
    worker_disk_overcommit.labels(**labels).set(
        max(0, worker.used_disk - worker.total_disk)
    )
