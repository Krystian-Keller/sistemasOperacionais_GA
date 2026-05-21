from dataclasses import dataclass, field


@dataclass
class Pod:
    name: str
    cpu: float
    memory: float
    disk: float
    latency_requirement: float
    status: str = "pending"
    assigned_worker: str | None = None
    rejection_reason: str = ""
    duration_cycles: int | None = None


@dataclass
class Worker:
    name: str
    total_cpu: float
    total_memory: float
    total_disk: float
    network_latency: float
    used_cpu: float = 0
    used_memory: float = 0
    used_disk: float = 0
    pods: list[Pod] = field(default_factory=list)

    @property
    def available_cpu(self) -> float:
        return self.total_cpu - self.used_cpu

    @property
    def available_memory(self) -> float:
        return self.total_memory - self.used_memory

    @property
    def available_disk(self) -> float:
        return self.total_disk - self.used_disk

    def can_fit_basic(self, pod: Pod) -> bool:
        return pod.cpu <= self.available_cpu and pod.memory <= self.available_memory

    def can_fit_custom(self, pod: Pod) -> bool:
        return (
            self.can_fit_basic(pod)
            and pod.disk <= self.available_disk
            and self.network_latency <= pod.latency_requirement
        )

    def allocate(self, pod: Pod) -> None:
        self.used_cpu += pod.cpu
        self.used_memory += pod.memory
        self.used_disk += pod.disk
        pod.status = "running"
        pod.assigned_worker = self.name
        pod.rejection_reason = ""
        self.pods.append(pod)

    def remove(self, pod: Pod) -> None:
        self.used_cpu -= pod.cpu
        self.used_memory -= pod.memory
        self.used_disk -= pod.disk
        pod.status = "completed"
        pod.assigned_worker = None
        self.pods.remove(pod)


@dataclass
class Master:
    name: str
    scheduler_name: str
    workers: list[Worker]
