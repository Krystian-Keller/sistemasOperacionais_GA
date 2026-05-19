from abc import ABC, abstractmethod

from models import Pod, Worker


class Scheduler(ABC):
    name: str

    @abstractmethod
    def select_worker(self, pod: Pod, workers: list[Worker]) -> Worker | None:
        pass

    def schedule(self, pods: list[Pod], workers: list[Worker]) -> list[Pod]:
        pending_pods = []

        for pod in pods:
            worker = self.select_worker(pod, workers)
            if worker is None:
                pod.status = "pending"
                pending_pods.append(pod)
            else:
                worker.allocate(pod)

        return pending_pods


class DefaultScheduler(Scheduler):
    name = "Scheduler padrao simplificado (CPU + memoria)"

    def select_worker(self, pod: Pod, workers: list[Worker]) -> Worker | None:
        candidates = [worker for worker in workers if worker.can_fit_basic(pod)]

        if not candidates:
            return None

        return max(candidates, key=lambda worker: self._score(pod, worker))

    def _score(self, pod: Pod, worker: Worker) -> float:
        cpu_after = worker.available_cpu - pod.cpu
        memory_after = worker.available_memory - pod.memory

        cpu_score = cpu_after / worker.total_cpu
        memory_score = memory_after / worker.total_memory

        return (cpu_score + memory_score) / 2


class CustomScheduler(Scheduler):
    name = "Scheduler customizado (CPU + memoria + disco + latencia)"

    def select_worker(self, pod: Pod, workers: list[Worker]) -> Worker | None:
        candidates = [worker for worker in workers if worker.can_fit_custom(pod)]

        if not candidates:
            return None

        return max(candidates, key=lambda worker: self.score(pod, worker))

    def score(self, pod: Pod, worker: Worker) -> float:
        cpu_after = worker.available_cpu - pod.cpu
        memory_after = worker.available_memory - pod.memory
        disk_after = worker.available_disk - pod.disk

        cpu_score = cpu_after / worker.total_cpu
        memory_score = memory_after / worker.total_memory
        disk_score = disk_after / worker.total_disk
        latency_score = 1 - (worker.network_latency / pod.latency_requirement)

        return (
            0.30 * cpu_score
            + 0.30 * memory_score
            + 0.25 * disk_score
            + 0.15 * latency_score
        )
