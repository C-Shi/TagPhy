import queue
from threading import Event, Lock, Thread
from typing import Literal, TypedDict
from tagphy.tools.pipeline import ImageProcessingPipeline


class BusyError(Exception):
    status_code = 409
    detail = "Job is not idle"

    def __init__(self, detail: str = None):
        self.detail = detail or self.detail

    def __str__(self):
        return self.detail


class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


JobState = Literal["idle", "running", "stopping"]


class ScanLog(TypedDict):
    status: Literal["success", "fail"]
    stage: str
    msg: str


class ScanJobController(metaclass=SingletonMeta):
    def __init__(self, pipeline: ImageProcessingPipeline):
        self.pipeline = pipeline
        self.state: JobState = "idle"
        self.log_queue = queue.Queue()
        self.stop_event = Event()
        self._lock = Lock()

    @property
    def scan_logs(self) -> queue.Queue[ScanLog]:
        return self.log_queue

    @property
    def job_state(self) -> JobState:
        return self.state

    def start(self, path: str) -> None:
        """Claim job under Lock. Validate path. Clear ring buffer. Spawn worker.
        Raises BusyError if not idle → route maps to 409.
        Raises ValueError if path invalid / outside app_root / is Photo_Tagged.
        """

        def _worker():
            try:
                # If a locker can start, recreate a new queue for this job
                while not self.log_queue.empty():
                    self.log_queue.get_nowait()
                self.pipeline.run(
                    path=path,
                    should_stop=self.stop_event.is_set,
                    on_progress=self._enqueue,
                )
            finally:
                with self._lock:
                    self.state = "idle"

        with self._lock:
            if self.state != "idle":
                raise BusyError(f"A Scan job is currently in {self.state}")

            if not self.pipeline.validate_path(path):
                raise ValueError("Target is the output directory or inside it")

            self.stop_event.clear()
            self.state = "running"
            # start in a separate thread to avoid blocking any other method calls
            Thread(target=_worker, daemon=True).start()

            return {"status": self.state}

    def stop(self) -> None:
        """If running, set Event and move to stopping.
        If idle: no-op or raise — recommend no-op (idempotent).
        """

        with self._lock:
            if self.state == "idle":
                return {"status": self.state}

            self.stop_event.set()
            self.state = "stopping"
            return {"status": self.state}

    def iter_log_history(self) -> list[dict]:
        """Copy of ring buffer for reconnect."""

    def _enqueue(self, message: ScanLog) -> None:
        with self._lock:
            self.log_queue.put(message)
            if self.log_queue.qsize() > 100:
                self.log_queue.get()
