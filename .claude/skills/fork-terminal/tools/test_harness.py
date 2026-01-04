#!/usr/bin/env python3
"""
Comprehensive Test Harness for Fork Terminal with E2B Sandbox Support

Tests all functionality:
1. Credential resolution (waterfall)
2. E2B sandbox execution (all agents)
3. Local terminal execution
4. Auto-close functionality
5. Error handling

Usage:
    python3 test_harness.py
    python3 test_harness.py --skip-local  # Skip local terminal tests
    python3 test_harness.py --agent gemini  # Test only specific agent
"""

import sys
import os
import time
from pathlib import Path
from typing import List, Dict, Tuple

# Add tools directory to path
sys.path.insert(0, str(Path(__file__).parent))

from credential_resolver import CredentialResolver, CredentialNotFoundError
from sandbox_backend import SandboxBackend


class TestHarness:
    """Comprehensive test harness for fork-terminal functionality"""

    def __init__(self):
        self.results: List[Dict] = []
        self.start_time = time.time()
        self.resolver = CredentialResolver()

    def print_header(self, title: str):
        """Print test section header"""
        print("\n" + "=" * 80)
        print(f"  {title}")
        print("=" * 80)

    def print_test(self, name: str, status: str, details: str = ""):
        """Print individual test result"""
        symbols = {
            "PASS": "✅",
            "FAIL": "❌",
            "SKIP": "⏭️",
            "INFO": "ℹ️"
        }
        symbol = symbols.get(status, "•")
        print(f"{symbol} {name}: {status}")
        if details:
            print(f"   {details}")

    def record_result(self, test_name: str, passed: bool, details: str = "", output: str = ""):
        """Record test result"""
        self.results.append({
            "name": test_name,
            "passed": passed,
            "details": details,
            "output": output
        })

    def test_credential_resolution(self):
        """Test credential waterfall resolution for all agents"""
        self.print_header("TEST 1: Credential Resolution (Waterfall)")

        agents = ["claude", "gemini", "codex", "e2b"]

        for agent in agents:
            try:
                credential = self.resolver.get_credential(agent, verbose=False)
                self.print_test(
                    f"Resolve {agent.upper()}_API_KEY",
                    "PASS",
                    f"Found ({len(credential)} chars)"
                )
                self.record_result(f"credential_{agent}", True, f"Found {len(credential)} chars")
            except CredentialNotFoundError as e:
                self.print_test(
                    f"Resolve {agent.upper()}_API_KEY",
                    "FAIL",
                    str(e).split('\n')[0]
                )
                self.record_result(f"credential_{agent}", False, str(e))

    def test_sandbox_backend_init(self):
        """Test sandbox backend initialization"""
        self.print_header("TEST 2: E2B Sandbox Backend Initialization")

        try:
            backend = SandboxBackend(verbose=False)
            self.print_test("Import E2B SDK", "PASS", "E2B Sandbox class loaded")
            self.record_result("e2b_sdk_import", True)

            if backend.template_id:
                self.print_test(
                    "Custom Template",
                    "INFO",
                    f"Using template: {backend.template_id}"
                )
            else:
                self.print_test(
                    "Custom Template",
                    "INFO",
                    "Using base template (runtime install)"
                )

        except Exception as e:
            self.print_test("Import E2B SDK", "FAIL", str(e))
            self.record_result("e2b_sdk_import", False, str(e))

    def test_sandbox_execution(self, agent: str, prompt: str = "tell me a very short joke"):
        """Test E2B sandbox execution for an agent"""

        try:
            # Check if credentials are available
            self.resolver.get_credential(agent, verbose=False)
            self.resolver.get_credential("e2b", verbose=False)
        except CredentialNotFoundError:
            self.print_test(
                f"{agent.upper()} Sandbox Execution",
                "SKIP",
                "Missing credentials"
            )
            self.record_result(f"sandbox_{agent}", False, "Missing credentials")
            return

        print(f"\n🧪 Testing {agent.upper()} in E2B Sandbox...")
        print(f"   Prompt: '{prompt}'")

        try:
            backend = SandboxBackend(verbose=True)
            result = backend.execute_agent(
                agent=agent,
                prompt=prompt,
                auto_close=True
            )

            if result["success"]:
                output = result["output"].strip()
                self.print_test(
                    f"{agent.upper()} Sandbox Execution",
                    "PASS",
                    f"Sandbox ID: {result['sandbox_id']}"
                )
                print(f"\n   📝 Agent Response:")
                print(f"   {'-' * 70}")
                for line in output.split('\n'):
                    print(f"   {line}")
                print(f"   {'-' * 70}\n")

                self.record_result(
                    f"sandbox_{agent}",
                    True,
                    f"Sandbox: {result['sandbox_id']}",
                    output
                )
            else:
                self.print_test(
                    f"{agent.upper()} Sandbox Execution",
                    "FAIL",
                    result.get("error", "Unknown error")
                )
                self.record_result(
                    f"sandbox_{agent}",
                    False,
                    result.get("error", "Unknown error")
                )

        except Exception as e:
            self.print_test(
                f"{agent.upper()} Sandbox Execution",
                "FAIL",
                str(e)
            )
            self.record_result(f"sandbox_{agent}", False, str(e))

    def test_all_sandbox_agents(self):
        """Test all agents in E2B sandbox"""
        self.print_header("TEST 3: E2B Sandbox Execution (All Agents)")

        agents = ["gemini", "codex", "claude"]

        for agent in agents:
            self.test_sandbox_execution(agent)
            print()  # Spacing between tests

    def test_local_terminal_fork(self):
        """Test local terminal forking"""
        self.print_header("TEST 4: Local Terminal Fork")

        import subprocess
        import time

        # Test file path
        test_file = "/tmp/fork-terminal-test.txt"

        # Clean up any existing test file
        if os.path.exists(test_file):
            os.remove(test_file)

        print(f"\n🧪 Testing local terminal fork...")
        print(f"   Command: echo 'Fork test successful' > {test_file}")

        try:
            from fork_terminal import fork_terminal

            # Fork terminal with simple command
            result = fork_terminal(f"echo 'Fork test successful' > {test_file} && sleep 1")

            # Wait for command to execute
            time.sleep(3)

            # Check if file was created
            if os.path.exists(test_file):
                with open(test_file) as f:
                    content = f.read().strip()

                if "Fork test successful" in content:
                    self.print_test(
                        "Local Terminal Fork",
                        "PASS",
                        f"Terminal spawned and executed command"
                    )
                    self.record_result("local_fork", True, "Command executed successfully")
                else:
                    self.print_test(
                        "Local Terminal Fork",
                        "FAIL",
                        f"File created but wrong content: {content}"
                    )
                    self.record_result("local_fork", False, "Wrong file content")
            else:
                self.print_test(
                    "Local Terminal Fork",
                    "FAIL",
                    "Terminal spawned but command didn't execute in time"
                )
                self.record_result("local_fork", False, "Command timeout")

            # Cleanup
            if os.path.exists(test_file):
                os.remove(test_file)

        except Exception as e:
            self.print_test("Local Terminal Fork", "FAIL", str(e))
            self.record_result("local_fork", False, str(e))

    def test_fork_terminal_integration(self):
        """Test fork_terminal.py integration"""
        self.print_header("TEST 5: Fork Terminal Integration")

        from fork_terminal import detect_backend, detect_agent

        # Test backend detection
        test_cases = [
            ("use gemini in sandbox to test", "e2b", "gemini"),
            ("use claude to analyze code", "local", "claude"),
            ("fork terminal use codex in sandbox", "e2b", "codex"),
            ("run npm test", "local", None),
        ]

        for command, expected_backend, expected_agent in test_cases:
            backend = detect_backend(command)
            agent = detect_agent(command)

            backend_match = backend == expected_backend
            agent_match = agent == expected_agent

            if backend_match and agent_match:
                self.print_test(
                    f"Parse: '{command[:40]}...'",
                    "PASS",
                    f"→ backend={backend}, agent={agent}"
                )
                self.record_result("parse_command", True)
            else:
                self.print_test(
                    f"Parse: '{command[:40]}...'",
                    "FAIL",
                    f"Expected {expected_backend}/{expected_agent}, got {backend}/{agent}"
                )
                self.record_result("parse_command", False)

    def print_summary(self):
        """Print test summary"""
        self.print_header("TEST SUMMARY")

        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r["passed"])
        failed_tests = total_tests - passed_tests

        elapsed_time = time.time() - self.start_time

        print(f"\n📊 Results:")
        print(f"   Total Tests: {total_tests}")
        print(f"   ✅ Passed: {passed_tests}")
        print(f"   ❌ Failed: {failed_tests}")
        print(f"   ⏱️  Time: {elapsed_time:.2f}s")
        print(f"   📈 Success Rate: {(passed_tests/total_tests*100):.1f}%")

        if failed_tests > 0:
            print(f"\n❌ Failed Tests:")
            for result in self.results:
                if not result["passed"]:
                    print(f"   • {result['name']}: {result['details']}")

        print("\n" + "=" * 80)

        if failed_tests == 0:
            print("🎉 ALL TESTS PASSED! Fork Terminal with E2B Sandbox is fully functional!")
        else:
            print(f"⚠️  {failed_tests} test(s) failed. Review errors above.")

        print("=" * 80 + "\n")

        return failed_tests == 0

    def run_all_tests(self, skip_local: bool = False, specific_agent: str = None):
        """Run all tests"""

        print("\n" + "=" * 80)
        print("  FORK TERMINAL + E2B SANDBOX - COMPREHENSIVE TEST HARNESS")
        print("=" * 80)
        print(f"\n  Testing Directory: {Path(__file__).parent}")
        print(f"  Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")

        # Test 1: Credential Resolution
        self.test_credential_resolution()

        # Test 2: Sandbox Backend
        self.test_sandbox_backend_init()

        # Test 3: Sandbox Execution
        if specific_agent:
            self.print_header(f"TEST 3: E2B Sandbox Execution ({specific_agent.upper()} only)")
            self.test_sandbox_execution(specific_agent)
        else:
            self.test_all_sandbox_agents()

        # Test 4: Local Terminal Fork
        if not skip_local:
            self.test_local_terminal_fork()
        else:
            print("\n⏭️  Skipping local terminal tests (--skip-local)")

        # Test 5: Integration
        self.test_fork_terminal_integration()

        # Summary
        return self.print_summary()


def main():
    """Main test harness entry point"""

    # Parse arguments
    skip_local = "--skip-local" in sys.argv
    specific_agent = None

    if "--agent" in sys.argv:
        idx = sys.argv.index("--agent")
        if idx + 1 < len(sys.argv):
            specific_agent = sys.argv[idx + 1]

    # Run tests
    harness = TestHarness()
    success = harness.run_all_tests(skip_local=skip_local, specific_agent=specific_agent)

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
