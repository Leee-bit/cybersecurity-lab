import re
import sys
import time
from datetime import datetime, timedelta
from collections import defaultdict

# --- Configuration ---
THRESHOLD = 10           # failed attempts that counts as suspicious
WINDOW_SECONDS = 60       # time window to count attempts within
CHECK_INTERVAL = 1        # seconds to sleep between checking for new log lines
CLEANUP_AFTER = 300       # drop timestamps older than this (seconds) to keep memory small
ALERT_LOG = "alerts.log"

LOG_PATTERN = re.compile(
    r"^(\w{3}\s+\d+\s+\d{2}:\d{2}:\d{2}).*Failed password for \w+ from (\d+\.\d+\.\d+\.\d+)"
)

CURRENT_YEAR = datetime.now().year


def parse_timestamp(ts_string):
    full_string = f"{CURRENT_YEAR} {ts_string}"
    return datetime.strptime(full_string, "%Y %b %d %H:%M:%S")


def get_log_file():
    if len(sys.argv) > 1:
        return sys.argv[1]
    return "auth.log"


def write_alert(ip, count, start_time):
    alert_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    alert_text = (
        f"[{alert_time}] ALERT: Brute force suspected from {ip} — "
        f"{count} failed attempts within {WINDOW_SECONDS}s "
        f"starting at {start_time}"
    )
    print(alert_text)
    with open(ALERT_LOG, "a") as f:
        f.write(alert_text + "\n")


def check_for_brute_force(attempts_by_ip, already_alerted):
    """Check each IP's recent attempts against the threshold."""
    for ip, timestamps in attempts_by_ip.items():
        if ip in already_alerted:
            continue  # don't spam repeated alerts for the same ongoing burst

        timestamps.sort()
        for i, start_time in enumerate(timestamps):
            count_in_window = sum(
                1 for t in timestamps[i:]
                if (t - start_time).total_seconds() <= WINDOW_SECONDS
            )
            if count_in_window >= THRESHOLD:
                write_alert(ip, count_in_window, start_time)
                already_alerted.add(ip)
                break


def cleanup_old_entries(attempts_by_ip):
    """Drop timestamps older than CLEANUP_AFTER to keep memory usage flat over time."""
    cutoff = datetime.now() - timedelta(seconds=CLEANUP_AFTER)
    for ip in list(attempts_by_ip.keys()):
        attempts_by_ip[ip] = [t for t in attempts_by_ip[ip] if t >= cutoff]
        if not attempts_by_ip[ip]:
            del attempts_by_ip[ip]


def main():
    log_file = get_log_file()
    print(f"[*] Monitoring log file: {log_file}")
    print(f"[*] Threshold: {THRESHOLD} attempts / {WINDOW_SECONDS}s")
    print("[*] Press Ctrl+C to stop monitoring.\n")

    attempts_by_ip = defaultdict(list)
    already_alerted = set()

    try:
        f = open(log_file, "r")
    except FileNotFoundError:
        print(f"[!] Error: could not find log file '{log_file}'")
        sys.exit(1)

    # Start reading from the END of the file — we only care about NEW activity,
    # same principle as `tail -f`
    f.seek(0, 2)

    last_cleanup = time.time()

    try:
        while True:
            line = f.readline()

            if not line:
                # No new line yet — sleep briefly instead of busy-looping (saves CPU)
                time.sleep(CHECK_INTERVAL)

                # Periodically clear out old timestamps so memory doesn't grow forever
                if time.time() - last_cleanup > CLEANUP_AFTER:
                    cleanup_old_entries(attempts_by_ip)
                    already_alerted.clear()
                    last_cleanup = time.time()

                continue

            match = LOG_PATTERN.search(line)
            if match:
                ts_string, ip = match.groups()
                timestamp = parse_timestamp(ts_string)
                attempts_by_ip[ip].append(timestamp)
                check_for_brute_force(attempts_by_ip, already_alerted)

    except KeyboardInterrupt:
        print("\n[*] Monitoring stopped.")
    finally:
        f.close()


if __name__ == "__main__":
    main()
