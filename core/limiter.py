class DailyLimiter:
    """Tracks the number of emails sent today against a configurable daily limit."""

    def __init__(self, limit):
        """Initialize with the given daily sending limit."""
        self.limit = limit
        self.count = 0

    def can_send(self):
        """Return True if the current count is below the daily limit."""
        return self.count < self.limit

    def increment(self):
        """Increment the sent count by one."""
        self.count += 1

    def remaining(self):
        """Return how many emails can still be sent today."""
        return self.limit - self.count

    def reset(self):
        """Reset the sent count back to zero."""
        self.count = 0
