from datetime import datetime, timezone


class UptimeTracker:
    def __init__(self):
        self._start_time: datetime | None = None

    def start(self) -> None:
        self._start_time = datetime.now(timezone.utc)

    @property
    def start_time(self) -> datetime | None:
        return self._start_time

    @property
    def uptime_seconds(self) -> int:
        if self._start_time is None:
            return 0
        return int((datetime.now(timezone.utc) - self._start_time).total_seconds())


uptime_tracker = UptimeTracker()
