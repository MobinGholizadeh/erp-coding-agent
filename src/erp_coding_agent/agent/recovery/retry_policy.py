class RecoveryLimitReached(Exception):
    pass

class RetryPolicy:
    def __init__(self, max_attempts: int = 5):
        self.max_attempts = max_attempts
        self.attempts = 0

    def increment(self):
        self.attempts += 1
        if self.attempts >= self.max_attempts:
            raise RecoveryLimitReached(f"Maximum recovery attempts ({self.max_attempts}) reached.")

    def reset(self):
        self.attempts = 0

    @property
    def current_attempt(self) -> int:
        return self.attempts
