"""Пишет загрузку процессора и память сервисов во время нагрузочного прогона (каждые 2 секунды).

Два режима, по тому, что передано после имени файла:
  python monitor.py out/res.csv aiesec-matcher-dev aiesec-postgres-dev   # имена контейнеров (docker stats)
  python monitor.py out/res.csv 8002 8000                                # порты процессов uvicorn на этой машине
Останавливается, когда его завершают (это делает run_load.sh).
"""
import csv
import subprocess
import sys
import time


def docker_sample(names):
    """{имя: (cpu %, память МБ)} по данным docker stats."""
    out = subprocess.run(["docker", "stats", "--no-stream", "--format", "{{.Name}};{{.CPUPerc}};{{.MemUsage}}", *names],
                         capture_output=True, text=True).stdout
    res = {}
    for line in out.splitlines():
        name, cpu, mem = line.split(";")
        used = mem.split("/")[0].strip()                     # например "85.4MiB"
        mb = float(used[:-3]) * (1024 if used.endswith("GiB") else 1)
        res[name] = (float(cpu.rstrip("%")), round(mb, 1))
    return res


def run_docker(out, names):
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["t", *[f"cpu_{n}" for n in names], *[f"mem_mb_{n}" for n in names]])
        t0 = time.time()
        while True:
            s = docker_sample(names)                         # сам вызов занимает около 2 секунд
            w.writerow([round(time.time() - t0), *[s.get(n, ("", ""))[0] for n in names],
                        *[s.get(n, ("", ""))[1] for n in names]])
            f.flush()


def run_ports(out, ports):
    import psutil                                            # ставится вместе с locust

    def find(port):
        for p in psutil.process_iter(["cmdline"]):
            if f"--port {port}" in " ".join(p.info["cmdline"] or []):
                return p
        return None

    procs = {port: find(port) for port in ports}
    for p in procs.values():
        if p:
            p.cpu_percent(None)
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["t", *[f"cpu_{p}" for p in ports], *[f"rss_mb_{p}" for p in ports], "cpu_total"])
        t0 = time.time()
        while True:
            time.sleep(2)
            cpu = [round(procs[p].cpu_percent(None), 1) if procs[p] else "" for p in ports]
            rss = [round(procs[p].memory_info().rss / 2**20, 1) if procs[p] else "" for p in ports]
            w.writerow([round(time.time() - t0), *cpu, *rss, psutil.cpu_percent(None)])
            f.flush()


if __name__ == "__main__":
    out, targets = sys.argv[1], sys.argv[2:]
    try:
        if all(t.isdigit() for t in targets):
            run_ports(out, [int(t) for t in targets])
        else:
            run_docker(out, targets)
    except KeyboardInterrupt:
        pass
