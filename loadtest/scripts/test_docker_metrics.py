import unittest
from unittest.mock import patch

from docker_metrics import collect, resource_values


class DockerMetricsTests(unittest.TestCase):
    def test_cgroup_v2_units_and_cache(self):
        stats = {"cpu_stats": {"cpu_usage": {"total_usage": 2500000000}},
                 "memory_stats": {"usage": 1000, "stats": {"inactive_file": 200}}}
        self.assertEqual(resource_values(stats), (2.5, 800))

    def test_cgroup_v1_cache_and_nonnegative_memory(self):
        stats = {"cpu_stats": {"cpu_usage": {"total_usage": 0}},
                 "memory_stats": {"usage": 1000, "stats": {
                     "total_inactive_file": 1200, "inactive_file": 100}}}
        self.assertEqual(resource_values(stats), (0, 0))

    @patch("docker_metrics.docker_get")
    def test_exports_only_target_services_and_keeps_container_identity(self, get):
        get.side_effect = [
            [{"Id": "abc", "Labels": {"com.docker.compose.service": "backend"}},
             {"Id": "def", "Labels": {"com.docker.compose.service": "postgres"}}],
            {"cpu_stats": {"cpu_usage": {"total_usage": 1000000000}},
             "memory_stats": {"usage": 512, "stats": {}}},
        ]
        result = collect()
        self.assertIn('container_cpu_usage_seconds_total{service="backend",id="abc"} 1.0', result)
        self.assertIn('container_memory_working_set_bytes{service="backend",id="abc"} 512', result)
        self.assertNotIn("postgres", result)
        self.assertEqual(get.call_count, 2)
        self.assertIn("com.docker.compose.project", get.call_args_list[0].args[0])


if __name__ == "__main__":
    unittest.main()
