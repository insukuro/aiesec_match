"""Summarize a k6 NDJSON export for NT01 or the steady-state start cohort."""
import argparse
import json
import math
from collections import Counter
from datetime import datetime
from pathlib import Path


def percentile_95(samples):
    if not samples:
        return None
    return round(sorted(samples)[math.ceil(0.95 * len(samples)) - 1], 3)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw", type=Path)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--hold", type=int)
    parser.add_argument("--start-ms", type=int, help="scenario_start_ms from k6 log")
    args = parser.parse_args()
    if (args.hold is None) != (args.start_ms is None) or (args.hold is not None and args.hold < 60):
        parser.error("provide --hold (at least 60 seconds) and --start-ms together")

    phase = "plateau" if args.hold else "control"
    counts = Counter()
    latency = []
    http_latency = []
    iteration_latency = []
    late_requests = 0
    window_requests = 0
    samples = {
        "match_started", "match_completed", "match_success", "http_req_failed",
        "candidate_iteration",
        "match_wall", "http_reqs", "http_req_duration",
    }
    with args.raw.open() as raw:
        for line in raw:
            point = json.loads(line)
            if point.get("type") != "Point" or point.get("metric") not in samples:
                continue
            metric, data = point["metric"], point["data"]
            tags, value = data["tags"], data["value"]
            if tags.get("run_id") != args.run_id:
                continue
            if metric.startswith("http_"):
                if tags.get("op") != "recommend":
                    continue
                if metric == "http_reqs" and args.hold:
                    elapsed = datetime.fromisoformat(data["time"].replace("Z", "+00:00")).timestamp()
                    elapsed -= args.start_ms / 1000
                    if 60 <= elapsed < 60 + args.hold:
                        window_requests += value
                    elif elapsed >= 60 + args.hold and tags.get("phase") == phase:
                        late_requests += value
            if tags.get("phase") != phase:
                continue
            if metric == "match_wall":
                latency.append(value)
            elif metric == "http_req_duration":
                http_latency.append(value)
            elif metric == "candidate_iteration":
                iteration_latency.append(value)
            else:
                counts[metric] += value

    started = counts["match_started"]
    completed = counts["match_completed"]
    success = counts["match_success"]
    http_requests = counts["http_reqs"]
    http_errors = counts["http_req_failed"]
    if not started or not (0 <= success <= completed <= started):
        parser.error("invalid or empty cohort")
    if len(latency) != success or not (http_errors <= http_requests and completed <= http_requests <= started):
        parser.error("inconsistent metrics; verify raw export")
    print(json.dumps({
        "phase": phase,
        "started": started,
        "completed": completed,
        "correct": success,
        "unfinished": started - completed,
        "http_requests": http_requests,
        "http_errors": http_errors,
        "http_error_pct": (100 * http_errors / http_requests) if http_requests else None,
        "business_success_pct": 100 * success / started,
        "requests_completed_in_plateau_window": window_requests if args.hold else None,
        "plateau_start_cohort_http_completions_after_window": late_requests if args.hold else None,
        "plateau_rps": (window_requests / args.hold) if args.hold else None,
        "correct_match_p95_ms": percentile_95(latency),
        "recommend_http_p95_ms_on_start_cohort": percentile_95(http_latency),
        "iteration_p95_ms": percentile_95(iteration_latency),
        "sample_target_400_met": len(latency) >= 400 if args.hold else None,
    }, indent=2))
    if phase == "control" and (started != 1 or success != 1):
        raise SystemExit("НТ-01: ожидается один корректный новый подбор")


if __name__ == "__main__":
    main()
