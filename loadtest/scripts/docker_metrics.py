"""Expose Backend/Matcher Docker Stats as Prometheus metrics, including on WSL."""

import http.client
import json
import logging
import os
import socket
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlencode


class DockerConnection(http.client.HTTPConnection):
    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        self.sock.connect("/var/run/docker.sock")


def docker_get(path):
    connection = DockerConnection("localhost", timeout=2)
    try:
        connection.request("GET", path)
        response = connection.getresponse()
        if response.status != 200:
            raise RuntimeError(f"Docker API returned {response.status}")
        return json.load(response)
    finally:
        connection.close()


def resource_values(stats):
    cpu_seconds = stats["cpu_stats"]["cpu_usage"]["total_usage"] / 1e9
    memory = stats["memory_stats"]
    cache = memory.get("stats", {})
    # cgroup v1 uses total_inactive_file; v2 uses inactive_file.
    inactive = cache.get("total_inactive_file", cache.get("inactive_file", 0))
    return cpu_seconds, max(0, memory["usage"] - inactive)


def collect():
    project = os.environ.get("DOCKER_PROJECT", "aiesec-match")
    filters = json.dumps({"label": [f"com.docker.compose.project={project}"]})
    containers = docker_get("/containers/json?" + urlencode({"filters": filters}))
    lines = [
        "# HELP container_cpu_usage_seconds_total Cumulative container CPU time in seconds.",
        "# TYPE container_cpu_usage_seconds_total counter",
        "# HELP container_memory_working_set_bytes Memory usage excluding inactive file cache.",
        "# TYPE container_memory_working_set_bytes gauge",
    ]
    for container in containers:
        service = container.get("Labels", {}).get("com.docker.compose.service")
        if service not in {"backend", "matcher"}:
            continue
        container_id = container["Id"]
        stats = docker_get(f"/containers/{container_id}/stats?stream=false&one-shot=true")
        cpu, memory = resource_values(stats)
        labels = f'service="{service}",id="{container_id}"'
        lines.extend([
            f"container_cpu_usage_seconds_total{{{labels}}} {cpu}",
            f"container_memory_working_set_bytes{{{labels}}} {memory}",
        ])
    return "\n".join(lines) + "\n"


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/metrics":
            self.send_error(404)
            return
        try:
            body = collect().encode()
        except (OSError, ValueError, KeyError, RuntimeError, http.client.HTTPException):
            logging.exception("Unable to collect Docker resource metrics")
            self.send_error(503, "Docker resource collection failed")
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass


if __name__ == "__main__":
    HTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
