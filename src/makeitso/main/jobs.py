import time


# Example background job: waits `delay` seconds to simulate slow work, then returns the sum
def add_numbers(x: int, y: int, delay: int = 5) -> int:
    time.sleep(delay)
    return x + y
