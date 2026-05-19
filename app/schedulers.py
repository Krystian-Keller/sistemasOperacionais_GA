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
                pod.rejection_reason = self.rejection_reason(pod, workers)
                pending_pods.append(pod)
            else:
                worker.allocate(pod)

        return pending_pods

    def rejection_reason(self, pod: Pod, workers: list[Worker]) -> str:
        if any(pod.cpu <= worker.available_cpu for worker in workers):
            cpu_reason = ""
        else:
            cpu_reason = "CPU insuficiente"

        if any(pod.memory <= worker.available_memory for worker in workers):
            memory_reason = ""
        else:
            memory_reason = "memoria insuficiente"

        reasons = [reason for reason in [cpu_reason, memory_reason] if reason]
        return (
            ", ".join(reasons)
            if reasons
            else "CPU e memoria insuficientes no mesmo Worker"
        )


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
        disk_usage_after = 1 - disk_score
        disk_pressure_penalty = 0.25 if disk_usage_after > 0.90 else 0

        return (
            0.25 * cpu_score
            + 0.25 * memory_score
            + 0.35 * disk_score
            + 0.15 * latency_score
            - disk_pressure_penalty
        )

    def rejection_reason(self, pod: Pod, workers: list[Worker]) -> str:
        reasons = []

        if not any(pod.cpu <= worker.available_cpu for worker in workers):
            reasons.append("CPU insuficiente")
        if not any(pod.memory <= worker.available_memory for worker in workers):
            reasons.append("memoria insuficiente")
        if not any(pod.disk <= worker.available_disk for worker in workers):
            reasons.append("disco insuficiente")
        if not any(worker.network_latency <= pod.latency_requirement for worker in workers):
            reasons.append("latencia acima do requisito")

        return ", ".join(reasons) if reasons else "sem Worker que atenda todas as metricas"
