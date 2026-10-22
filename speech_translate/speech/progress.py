"""Monotonic coverage of decoded audio, rather than guessed completion time."""

import dataclasses


def timestamp(seconds: float) -> str:
    """Format an audio position without rounding beyond the decoded sample."""
    minutes, seconds = divmod(max(0, int(seconds)), 60)
    return f"{minutes}:{seconds:02d}"


@dataclasses.dataclass
class Coverage:
    """Track confirmed timestamps even when word alignment moves backward."""

    duration: float
    operation: object
    completed: float = 0.0

    def update(self, seconds: float) -> None:
        """Report actual coverage; only the service can report completion."""
        self.completed = max(self.completed, min(seconds, self.duration))
        percent = min(99, int(100 * self.completed / max(self.duration, 0.001)))
        message = (
            f"Audio transcribed: {timestamp(self.completed)} / "
            f"{timestamp(self.duration)} · Processing the next passage…"
        )
        self.operation.report(message, percent)
