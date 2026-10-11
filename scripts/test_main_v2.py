import base64
import importlib.util
import json
import os
import socket
import sys
import threading
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import yaml


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import main_v2


class SourceParsingTests(unittest.TestCase):
    def test_parses_base64_clash_and_singbox_sources(self):
        vless_uri = (
            "vless://11111111-1111-4111-8111-111111111111"
            "@example.com:443?security=tls&type=tcp#fixture"
        )
        encoded = base64.b64encode(vless_uri.encode()).decode()
        self.assertIn(vless_uri, main_v2.extract_nodes_from_text(encoded))

        clash_yaml = """\
proxies:
  - name: fixture-ss
    type: ss
    server: 127.0.0.1
    port: 8388
    cipher: aes-128-gcm
    password: sample-password
"""
        singbox_json = json.dumps({
            "outbounds": [{
                "type": "shadowsocks",
                "tag": "fixture-ss",
                "server": "127.0.0.1",
                "server_port": 8388,
                "method": "aes-128-gcm",
                "password": "sample-password",
            }]
        })
        for source in (clash_yaml, singbox_json):
            with self.subTest(source=source[:20]):
                nodes = main_v2.extract_nodes_from_text(source)
                self.assertEqual(len(nodes), 1)
                self.assertIsNotNone(main_v2.parse_node_uri(next(iter(nodes))))

    def test_extracts_enabled_manifest_and_subscription_page_links(self):
        manifest = json.dumps([
            {"enabled": True, "url": "https://feed.example/nodes", "remarks": "feed"},
            {"enabled": False, "url": "https://feed.example/disabled", "remarks": "feed"},
        ])
        self.assertEqual(
            main_v2.extract_subscription_urls(manifest),
            ["https://feed.example/nodes"],
        )

        page = """\
<html><body><h3>v2ray订阅链接</h3>
<a href="https://feed.example/nodes.txt">下载</a>
<a href="https://ads.example/banner.png">图片</a>
</body></html>
"""
        self.assertEqual(
            main_v2.extract_subscription_urls(page),
            ["https://feed.example/nodes.txt"],
        )

    def test_rejects_non_base64_when_decoding_feed(self):
        self.assertEqual(main_v2.b64_decode("https://example.com/a+b"), "")


class AggregationTests(unittest.TestCase):
    def test_final_upstream_is_fetched_after_other_sources(self):
        config = {
            "result_pools": ["manual"],
            "result_pool_repositories": ["result-repo"],
            "source_code_repositories": ["source-repo"],
            "final_result_pools": ["ogden-final"],
        }
        calls = []
        response_text = (
            "vless://11111111-1111-4111-8111-111111111111"
            "@example.com:443?security=tls#fixture"
        )

        def fake_get(url, timeout=15, headers=None):
            calls.append(url)
            return Mock(status_code=200, text=response_text)

        with (
            patch.object(main_v2, "load_source_config", return_value=config),
            patch.object(
                main_v2,
                "discover_repository_sources",
                side_effect=lambda entries: ["discovered-" + entries[0]],
            ),
            patch.object(main_v2, "http_get", side_effect=fake_get),
        ):
            nodes = main_v2.fetch_raw_nodes()

        self.assertEqual(calls[-1], "ogden-final")
        self.assertEqual(len(nodes), 1)

    def test_repository_discovery_uses_api_token_and_generates_raw_url(self):
        response_headers = []

        def fake_get(url, timeout=15, headers=None):
            response_headers.append(headers or {})
            response = Mock(status_code=200)
            if "/git/trees/" in url:
                response.json.return_value = {
                    "tree": [{"type": "blob", "path": "sub/all.txt"}]
                }
            else:
                response.json.return_value = {"default_branch": "main"}
            return response

        with (
            patch.dict(os.environ, {"GITHUB_TOKEN": "test-token"}),
            patch.object(main_v2, "http_get", side_effect=fake_get),
        ):
            urls = main_v2.discover_repository_sources(
                [{"repo": "example/source", "max_files": 1}]
            )

        self.assertEqual(
            urls,
            ["https://raw.githubusercontent.com/example/source/main/sub/all.txt"],
        )
        self.assertTrue(all(
            headers.get("Authorization") == "Bearer test-token"
            for headers in response_headers
        ))

    def test_action_schedule_and_source_configuration(self):
        workflow = yaml.safe_load(
            (SCRIPT_DIR.parent / ".github" / "workflows" / "update.yml")
            .read_text(encoding="utf-8")
        )
        self.assertEqual(workflow[True]["schedule"][0]["cron"], "0 4,10,22 * * *")

        config = main_v2.load_source_config()
        self.assertEqual(len(config["result_pool_repositories"]), 3)
        self.assertEqual(len(config["source_code_repositories"]), 3)
        self.assertEqual(
            config["final_result_pools"],
            ["https://raw.githubusercontent.com/OgdenThomas/freesub/main/output/v2ray.txt"],
        )
        self.assertEqual(
            set(config["candidate_region_exclusions"]),
            {"eastern_europe", "africa", "western_asia"},
        )

    def test_candidate_region_filter_uses_server_country_and_keeps_unknowns(self):
        candidates = [
            ("pl", {}, "pl.example", 443, "vless"),
            ("za", {}, "za.example", 443, "vless"),
            ("ir", {}, "ir.example", 443, "vless"),
            ("us", {}, "us.example", 443, "vless"),
            ("unknown", {}, "unknown.example", 443, "vless"),
        ]
        server_ips = {
            "pl.example": "192.0.2.1",
            "za.example": "192.0.2.2",
            "ir.example": "192.0.2.3",
            "us.example": "192.0.2.4",
            "unknown.example": "",
        }
        countries = {
            "192.0.2.1": "PL",
            "192.0.2.2": "ZA",
            "192.0.2.3": "IR",
            "192.0.2.4": "US",
        }

        class CountryReader:
            def get(self, ip):
                return {"country": {"iso_code": countries[ip]}}

        exclusions = {
            "eastern_europe": ["PL"],
            "africa": ["ZA"],
            "western_asia": ["IR"],
        }
        with patch.object(main_v2, "resolve_host", side_effect=server_ips.get):
            retained = main_v2.filter_candidates_by_server_region(
                candidates, exclusions, CountryReader(),
            )

        self.assertEqual([item[0] for item in retained], ["us", "unknown"])

    def test_readme_generates_fixed_repository_subscription_urls(self):
        written = []
        with (
            patch.object(
                main_v2, "atomic_write_text",
                side_effect=lambda path, content: written.append(content),
            ),
            patch.dict(os.environ, {"GITHUB_REPOSITORY": "hzjnet/freesub"}),
        ):
            main_v2.update_readme(0, 0)

        self.assertEqual(len(written), 1)
        self.assertIn(
            "https://cdn.jsdelivr.net/gh/hzjnet/freesub@main/output/clash.yaml",
            written[0],
        )
        self.assertIn(
            "https://raw.githubusercontent.com/hzjnet/freesub/main/output/v2ray.txt",
            written[0],
        )
        self.assertNotIn("?v=", written[0])


class SichuanRttTests(unittest.TestCase):
    def test_rtt_threshold_accepts_800_and_rejects_above_or_missing(self):
        self.assertTrue(main_v2.is_sichuan_rtt_acceptable(800.0))
        self.assertFalse(main_v2.is_sichuan_rtt_acceptable(800.001))
        self.assertFalse(main_v2.is_sichuan_rtt_acceptable(None))

    def test_slow_primary_retries_gateway(self):
        calls = []

        def fake_query(port, address):
            calls.append(address)
            return 900.5 if address == "61.139.2.69" else 710.25

        with patch.object(main_v2, "_query_dns_through_socks", side_effect=fake_query):
            rtt = main_v2.measure_sichuan_dns_rtt(1234)

        self.assertEqual(rtt, 710.25)
        self.assertEqual(calls, ["61.139.2.69", "61.139.2.1"])

    def test_udp_failure_falls_back_to_tcp(self):
        with (
            patch.object(
                main_v2, "_query_dns_through_socks",
                side_effect=socket.timeout("UDP unavailable"),
            ),
            patch.object(
                main_v2, "_query_dns_over_tcp_through_socks", return_value=725.0,
            ) as tcp_query,
        ):
            rtt = main_v2.measure_sichuan_dns_rtt(1234)

        self.assertEqual(rtt, 725.0)
        tcp_query.assert_called_once_with(1234, "61.139.2.69")

    def test_socks5_udp_dns_probe(self):
        relay = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        relay.bind(("127.0.0.1", 0))
        relay_port = relay.getsockname()[1]
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        socks_port = listener.getsockname()[1]
        errors = []

        def socks_server():
            try:
                connection, _ = listener.accept()
                with connection:
                    self.assertEqual(connection.recv(3), b"\x05\x01\x00")
                    connection.sendall(b"\x05\x00")
                    request = bytearray()
                    while len(request) < 10:
                        request.extend(connection.recv(10 - len(request)))
                    self.assertEqual(
                        bytes(request),
                        b"\x05\x03\x00\x01\x00\x00\x00\x00\x00\x00",
                    )
                    connection.sendall(
                        b"\x05\x00\x00\x01\x7f\x00\x00\x01" +
                        relay_port.to_bytes(2, "big")
                    )
            except Exception as error:
                errors.append(error)

        def dns_server():
            try:
                packet, client = relay.recvfrom(4096)
                self.assertEqual(packet[:4], b"\x00\x00\x00\x01")
                self.assertEqual(socket.inet_ntoa(packet[4:8]), "192.0.2.53")
                self.assertEqual(int.from_bytes(packet[8:10], "big"), 53)
                query = packet[10:]
                response = (
                    query[:2] + b"\x81\x80" + query[4:6] +
                    b"\x00\x01\x00\x00\x00\x00" + query[12:] +
                    b"\xc0\x0c\x00\x01\x00\x01\x00\x00\x00\x3c\x00\x04"
                    b"\x08\x08\x08\x08"
                )
                relay.sendto(
                    b"\x00\x00\x00\x01" + socket.inet_aton("192.0.2.53") +
                    (53).to_bytes(2, "big") + response,
                    client,
                )
            except Exception as error:
                errors.append(error)

        threads = [
            threading.Thread(target=socks_server, daemon=True),
            threading.Thread(target=dns_server, daemon=True),
        ]
        try:
            for thread in threads:
                thread.start()
            rtt = main_v2._query_dns_through_socks(socks_port, "192.0.2.53")
            for thread in threads:
                thread.join(timeout=3)
            self.assertFalse(errors, errors)
            self.assertGreaterEqual(rtt, 0)
            self.assertLess(rtt, main_v2.SICHUAN_DNS_TIMEOUT * 1000)
        finally:
            listener.close()
            relay.close()

    def test_socks5_tcp_dns_probe(self):
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        socks_port = listener.getsockname()[1]
        errors = []

        def socks_server():
            try:
                connection, _ = listener.accept()
                with connection:
                    self.assertEqual(connection.recv(3), b"\x05\x01\x00")
                    connection.sendall(b"\x05\x00")
                    request = bytearray()
                    while len(request) < 10:
                        request.extend(connection.recv(10 - len(request)))
                    self.assertEqual(
                        bytes(request),
                        b"\x05\x01\x00\x01" + socket.inet_aton("192.0.2.53") +
                        (53).to_bytes(2, "big"),
                    )
                    connection.sendall(
                        b"\x05\x00\x00\x01\x7f\x00\x00\x01\x00\x35"
                    )
                    length = int.from_bytes(connection.recv(2), "big")
                    query = bytearray()
                    while len(query) < length:
                        query.extend(connection.recv(length - len(query)))
                    response = (
                        bytes(query[:2]) + b"\x81\x80" + bytes(query[4:6]) +
                        b"\x00\x01\x00\x00\x00\x00" + bytes(query[12:]) +
                        b"\xc0\x0c\x00\x01\x00\x01\x00\x00\x00\x3c\x00\x04"
                        b"\x08\x08\x08\x08"
                    )
                    connection.sendall(len(response).to_bytes(2, "big") + response)
            except Exception as error:
                errors.append(error)

        thread = threading.Thread(target=socks_server, daemon=True)
        try:
            thread.start()
            rtt = main_v2._query_dns_over_tcp_through_socks(
                socks_port, "192.0.2.53",
            )
            thread.join(timeout=3)
            self.assertFalse(errors, errors)
            self.assertGreaterEqual(rtt, 0)
            self.assertLess(rtt, main_v2.SICHUAN_DNS_TIMEOUT * 1000)
        finally:
            listener.close()


if __name__ == "__main__":
    unittest.main()
