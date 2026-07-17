# backend/sandbox/docker_sandbox.py
import logging
import subprocess
from pathlib import Path
from typing import Any


logger = logging.getLogger("supremeai.sandbox.docker")


class DockerSandbox:
    def __init__(self, image_name: str = "python:3.11-slim"):
        self.image_name = image_name
        self.memory_limit = "256m"
        self.cpu_limit = "0.5"
        self.timeout_seconds = 10

    def run_quarantine_test(self, staging_path: Path, entry_file: str, test_payload: str) -> dict[str, Any]:
        """
        Default-deny network এবং Read-only মাউন্টে একটি পাইথন ফাইল স্যান্ডবক্সে রান করায়।
        """
        if not staging_path.exists():
            return {"exit_code": -1, "stdout": "", "stderr": "Staging path does not exist."}

        # স্যান্ডবক্সের ভেতর এক্সিকিউট করার জন্য একটি সেফ রানিং স্ক্রিপ্ট ইনজেক্ট করা হচ্ছে
        # এটি নিশ্চিত করে যে কোডটি রান করার পর আউটপুটটি জেসন ফরম্যাটে ট্র্যাপড হবে
        target_file_path = staging_path / entry_file
        if not target_file_path.exists():
            return {"exit_code": -1, "stdout": "", "stderr": f"Entry file {entry_file} not found."}

        # Subprocess এর মাধ্যমে সরাসরি ডকার সিএলআই এনফোর্সমেন্ট
        cmd = [
            "docker",
            "run",
            "--rm",
            "--network",
            "none",  # 🔒 নো নেটওয়ার্ক (Default-deny)
            "--memory",
            self.memory_limit,  # 📉 মেমরি ক্যাপ
            "--cpus",
            self.cpu_limit,  # 📊 সিপিইউ ক্যাপ
            "-v",
            f"{staging_path.resolve()}:/workspace:ro",  # 📁 রিড-ওনলি মাউন্ট
            "-w",
            "/workspace",
            self.image_name,
            "python",
            "-c",
            f"import sys; import json; import {entry_file.replace('.py', '')} as tool; print(json.dumps(tool.execute_tool({test_payload})))",
        ]

        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=self.timeout_seconds, check=False)
            return {"exit_code": result.returncode, "stdout": result.stdout.strip(), "stderr": result.stderr.strip()}
        except subprocess.TimeoutExpired:
            return {
                "exit_code": 124,  # Standard timeout exit code
                "stdout": "",
                "stderr": f"🚨 Security Sandbox Timeout: Execution exceeded {self.timeout_seconds}s limit.",
            }
        except Exception as e:
            return {"exit_code": -1, "stdout": "", "stderr": f"Docker execution engine failure: {str(e)}"}

    def run_safe_container(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        হোস্টের আইসোলেটেড ফাইলকে কন্টেইনারের ভেতর Read-Only মাউন্ট করে
        নিরাপদে পাইথন স্ক্রিপ্ট এক্সিকিউট করে এবং আউটপুট রিটার্ন করে।
        """
        script = payload.get("script", "")
        bind_source = payload.get("bind_mount_source", "")
        bind_target = payload.get("bind_mount_target", "")

        if not script:
            return {"exit_code": 1, "stdout": "", "stderr": "No script provided for sandbox execution."}

        # 🛡️ ডকার সিকিউরিটি এবং আইসোলেশন ফ্ল্যাগস এনফোর্সমেন্ট
        docker_command = [
            "docker",
            "run",
            "--rm",
            "--network",
            "none",
            "--read-only",
            "-v",
            f"{bind_source}:{bind_target}:ro",
            self.image_name,
            "python3",
            "-c",
            script,
        ]

        try:
            logger.info(f"⚡ Spawning Docker Sandbox for source volume: {bind_source}")

            result = subprocess.run(docker_command, capture_output=True, text=True, timeout=self.timeout_seconds, check=False)

            return {"exit_code": result.returncode, "stdout": result.stdout.strip(), "stderr": result.stderr.strip()}

        except subprocess.TimeoutExpired:
            logger.error(f"❌ Sandbox execution timed out after {self.timeout_seconds}s limit.")
            return {"exit_code": 124, "stdout": "", "stderr": f"Execution barrier breached: Timeout of {self.timeout_seconds}s exceeded."}
        except Exception as e:
            logger.error(f"Critical exception inside Docker execution wrapper: {str(e)}")
            return {"exit_code": -1, "stdout": "", "stderr": f"Sandbox Runtime Anomaly: {str(e)}"}
