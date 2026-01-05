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

    def test_cli_availability(self):
        """Test CLI availability in E2B sandbox"""
        self.print_header("TEST 2.5: CLI Availability in E2B Sandbox")

        try:
            # Check if E2B credentials are available
            self.resolver.get_credential("e2b", verbose=False)
        except CredentialNotFoundError:
            self.print_test("CLI Availability Check", "SKIP", "Missing E2B credentials")
            self.record_result("cli_availability", False, "Missing E2B credentials")
            return

        print("\n🔍 Checking which CLIs are installed in sandbox...\n")

        try:
            backend = SandboxBackend(verbose=False)

            # Create a temporary sandbox to check CLI availability
            from e2b import Sandbox
            e2b_key = self.resolver.get_credential("e2b", verbose=False)

            # Set E2B API key in environment (E2B SDK requires this)
            import os
            original_e2b_key = os.environ.get('E2B_API_KEY')
            os.environ['E2B_API_KEY'] = e2b_key

            # Create sandbox using E2B SDK
            sandbox = Sandbox.create(timeout=60)

            try:
                agents = ["claude", "gemini", "codex"]
                cli_status = {}

                for agent in agents:
                    available = backend._check_cli_availability(agent, sandbox)
                    cli_status[agent] = available

                    status = "PASS" if available else "INFO"
                    details = "CLI installed ✓" if available else "Using Python API fallback"

                    self.print_test(
                        f"{agent.upper()} CLI",
                        status,
                        details
                    )
                    self.record_result(f"cli_{agent}", available, details)

                # Summary
                installed_count = sum(1 for v in cli_status.values() if v)
                print(f"\n   📊 Summary: {installed_count}/3 CLIs installed")
                print(f"   Sandbox ID: {sandbox.sandbox_id}")

                # Record overall test result as PASS (fallback is expected behavior)
                self.print_test(
                    "CLI Availability Check",
                    "PASS",
                    f"{installed_count}/3 CLIs installed, {3 - installed_count} using API fallback"
                )
                self.record_result("cli_availability", True, f"{installed_count}/3 CLIs installed")

            finally:
                # Clean up sandbox
                sandbox.kill()
                print("   🧹 Sandbox terminated\n")

                # Restore original E2B key
                if original_e2b_key:
                    os.environ['E2B_API_KEY'] = original_e2b_key
                elif 'E2B_API_KEY' in os.environ:
                    del os.environ['E2B_API_KEY']

        except Exception as e:
            self.print_test("CLI Availability Check", "FAIL", str(e))
            self.record_result("cli_availability", False, str(e))

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

    def test_sandbox_file_upload(self):
        """Test file upload to E2B sandbox"""
        self.print_header("TEST 5: E2B Sandbox File Upload")

        # Check if credentials are available
        try:
            self.resolver.get_credential("gemini", verbose=False)
            self.resolver.get_credential("e2b", verbose=False)
        except CredentialNotFoundError:
            self.print_test(
                "Sandbox File Upload",
                "SKIP",
                "Missing credentials"
            )
            self.record_result("sandbox_file_upload", False, "Missing credentials")
            return

        print(f"\n🧪 Testing file upload to E2B sandbox...")

        # Create a test file
        test_file_path = Path(__file__).parent.parent / "SKILL.md"

        if not test_file_path.exists():
            self.print_test(
                "Sandbox File Upload",
                "SKIP",
                f"Test file not found: {test_file_path}"
            )
            self.record_result("sandbox_file_upload", False, "Test file not found")
            return

        print(f"   Test file: {test_file_path.name} ({test_file_path.stat().st_size} bytes)")
        print(f"   Prompt: 'analyze my SKILL.md file and tell me what this skill does in one sentence'")

        try:
            backend = SandboxBackend(verbose=True)
            result = backend.execute_agent(
                agent="gemini",
                prompt="analyze my SKILL.md file and tell me what this skill does in one sentence",
                auto_close=True,
                working_dir=str(test_file_path.parent)
            )

            if result["success"] and result["output"]:
                # Check if the output mentions fork or terminal (indicating it read the file)
                output_lower = result["output"].lower()
                if "fork" in output_lower or "terminal" in output_lower or "skill" in output_lower:
                    self.print_test(
                        "Sandbox File Upload",
                        "PASS",
                        f"File uploaded and analyzed successfully"
                    )
                    print(f"\n   📝 Analysis result (truncated):")
                    print(f"   {result['output'][:200]}...")
                    self.record_result(
                        "sandbox_file_upload",
                        True,
                        "File upload and content reading verified"
                    )
                else:
                    self.print_test(
                        "Sandbox File Upload",
                        "FAIL",
                        "Agent didn't appear to read file content"
                    )
                    self.record_result(
                        "sandbox_file_upload",
                        False,
                        "File content not read correctly"
                    )
            else:
                self.print_test(
                    "Sandbox File Upload",
                    "FAIL",
                    result.get("error", "No output from agent")
                )
                self.record_result(
                    "sandbox_file_upload",
                    False,
                    result.get("error", "No output")
                )

        except Exception as e:
            self.print_test(
                "Sandbox File Upload",
                "FAIL",
                str(e)
            )
            self.record_result("sandbox_file_upload", False, str(e))

    def test_sandbox_file_download(self):
        """Test file download from E2B sandbox"""
        self.print_header("TEST 6: E2B Sandbox File Download")

        # Check if credentials are available
        try:
            self.resolver.get_credential("gemini", verbose=False)
            self.resolver.get_credential("e2b", verbose=False)
        except CredentialNotFoundError:
            self.print_test(
                "Sandbox File Download",
                "SKIP",
                "Missing credentials"
            )
            self.record_result("sandbox_file_download", False, "Missing credentials")
            return

        print(f"\n🧪 Testing file download from E2B sandbox...")
        print(f"   Prompt: 'create a file /home/user/output/test-report.md with a summary'")

        # Clean up any existing output directory
        import shutil
        output_dir = Path(__file__).parent.parent.parent.parent / "sandbox-output"
        if output_dir.exists():
            shutil.rmtree(output_dir)

        try:
            backend = SandboxBackend(verbose=True)
            result = backend.execute_agent(
                agent="gemini",
                prompt="create a markdown file at /home/user/output/test-report.md with the content: '# Test Report\\nThis file was created by Gemini in an E2B sandbox.\\n\\n## Status\\nFile download test successful!'",
                auto_close=True,
                download_output=True,
                output_dir=str(output_dir)
            )

            if result["success"]:
                # Check if files were downloaded
                if result["downloaded_files"]:
                    # Verify the file exists locally
                    expected_file = output_dir / "test-report.md"
                    if expected_file.exists():
                        with open(expected_file) as f:
                            content = f.read()

                        if "Test Report" in content and "File download test successful" in content:
                            self.print_test(
                                "Sandbox File Download",
                                "PASS",
                                f"{len(result['downloaded_files'])} file(s) downloaded"
                            )
                            print(f"\n   📝 Downloaded file content (first 100 chars):")
                            print(f"   {content[:100]}...")
                            self.record_result(
                                "sandbox_file_download",
                                True,
                                f"Downloaded {len(result['downloaded_files'])} files"
                            )
                        else:
                            self.print_test(
                                "Sandbox File Download",
                                "FAIL",
                                "File downloaded but content is incorrect"
                            )
                            self.record_result(
                                "sandbox_file_download",
                                False,
                                "Incorrect file content"
                            )
                    else:
                        self.print_test(
                            "Sandbox File Download",
                            "FAIL",
                            f"Downloaded file not found at {expected_file}"
                        )
                        self.record_result(
                            "sandbox_file_download",
                            False,
                            "File not found locally"
                        )
                else:
                    self.print_test(
                        "Sandbox File Download",
                        "FAIL",
                        "No files were downloaded"
                    )
                    self.record_result(
                        "sandbox_file_download",
                        False,
                        "No files downloaded"
                    )
            else:
                self.print_test(
                    "Sandbox File Download",
                    "FAIL",
                    result.get("error", "Execution failed")
                )
                self.record_result(
                    "sandbox_file_download",
                    False,
                    result.get("error", "Execution failed")
                )

        except Exception as e:
            self.print_test(
                "Sandbox File Download",
                "FAIL",
                str(e)
            )
            self.record_result("sandbox_file_download", False, str(e))

        finally:
            # Cleanup test output directory
            if output_dir.exists():
                shutil.rmtree(output_dir)

    def test_fork_terminal_integration(self):
        """Test fork_terminal.py integration"""
        self.print_header("TEST 7: Fork Terminal Integration")

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

        # Test 2.5: CLI Availability
        self.test_cli_availability()

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

        # Test 5: Sandbox File Upload
        self.test_sandbox_file_upload()

        # Test 6: Sandbox File Download
        self.test_sandbox_file_download()

        # Test 7: Integration
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
