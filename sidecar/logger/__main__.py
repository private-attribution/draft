import random
import sys
import time

import click
import mnemonic
from loguru import logger


class Formatter:
    # pylint: disable=too-few-public-methods
    def __init__(self):
        self.padding = 0
        self.fmt = (
            "{time} | {level: <8} | {name}:{function}:{line}{extra[padding]}"
            " | {message}\n{exception}"
        )

    def format(self, record):
        fmt = f"{record['name']}:{record['function']}:{record['line']}"
        length = len(fmt)
        self.padding = max(self.padding, length)
        record["extra"]["padding"] = " " * (self.padding - length)
        return self.fmt


formatter = Formatter()

logger.remove()
logger.add(sys.stderr, format=formatter.format)


def generate_random_log():
    log_level = random.choice(["info", "warning", "error"])

    # Choose the appropriate logger function based on the log level
    log_function = getattr(logger, log_level, logger.info)

    # Generate a random word using python-mnemonic
    words = mnemonic.Mnemonic("english").generate()

    log_function(words)


def generate_logs(num_lines, total_runtime):
    expected_time_between_events = total_runtime / num_lines

    for _ in range(num_lines):
        generate_random_log()

        # Calculate sleep time based on exponential distribution
        sleep_time = random.expovariate(1 / expected_time_between_events)

        # Cap the sleep time at 3x the expected time between events (95th percentile)
        sleep_time = min(sleep_time, 3 * expected_time_between_events)

        time.sleep(sleep_time)


@click.command()
@click.option(
    "--num-lines", type=int, default=10, help="Number of log lines to generate"
)
@click.option(
    "--total-runtime", type=float, default=10, help="Approx total runtime in seconds"
)
def main(num_lines, total_runtime):
    generate_logs(num_lines, total_runtime)


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
