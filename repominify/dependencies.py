"""Utility module for managing Node.js, npm, and Repomix dependencies.

This module handles the checking and installation of required system dependencies
for repo-minify to function properly.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Union, List, Optional, Tuple

from .exceptions import DependencyError, CommandExecutionError, InstallationError
from .types import DependencyVersion, CommandResult, ProcessOutput, VersionInfo

logger = logging.getLogger(__name__)


class DependencyManager:
    """Manages system dependencies for repo-minify.

    This class handles checking and installing required system dependencies,
    with proper error handling and logging.

    Attributes:
        debug: Whether debug mode is enabled
        stats: Runtime statistics for monitoring installations
        _version_cache: Cache of dependency version information
    """

    debug: bool
    stats: Dict[str, Union[int, float, str]]
    _version_cache: Dict[str, DependencyVersion]

    def __init__(self, debug: bool = False) -> None:
        """Initialize dependency manager.

        Args:
            debug: Enable debug logging and version tracking

        Examples::
            >>> manager = DependencyManager(debug=True)
            >>> manager.stats["commands_executed"]
            0
        """
        self.debug = debug
        if debug:
            logging.basicConfig(level=logging.DEBUG)

        self.stats = {
            "commands_executed": 0,
            "install_attempts": 0,
            "total_install_time_ms": 0,
            "last_check_time": 0,
        }

        self._version_cache = {}

    def _run_command(
        self, cmd: List[str], capture_stderr: bool = True, timeout: Optional[int] = 30
    ) -> subprocess.CompletedProcess:  # sourcery skip: extract-method
        """Execute a system command and return the result.

        Args:
            cmd: List of command components to execute
            capture_stderr: Whether to capture stderr in the output
            timeout: Command timeout in seconds

        Returns:
            CompletedProcess instance with command results

        Raises:
            CommandExecutionError: If command execution fails
            subprocess.TimeoutExpired: If command exceeds timeout

        Examples::
            >>> manager = DependencyManager()
            >>> result = manager._run_command(["echo", "test"])
            >>> result.returncode
            0
        """
        start_time = time.time()

        try:
            logger.debug(f"Executing command: {' '.join(cmd)}")
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=False, timeout=timeout
            )

            self.stats["commands_executed"] += 1
            execution_time = (time.time() - start_time) * 1000
            logger.debug(f"Command completed in {execution_time:.2f}ms")

            return result
        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out after {timeout}s: {' '.join(cmd)}")
            raise
        except Exception as e:
            logger.error(f"Command failed: {e}")
            raise CommandExecutionError(f"Failed to execute {cmd[0]}: {str(e)}") from e

    def check_node_npm(self) -> CommandResult:  # sourcery skip: extract-method
        """Check if Node.js and npm are installed.

        Returns:
            Tuple of (success, message) indicating installation status

        Raises:
            FileNotFoundError: If Node.js or npm executables are not found
            CommandExecutionError: If version check commands fail
            subprocess.TimeoutExpired: If version checks timeout

        Examples::
            >>> manager = DependencyManager()
            >>> success, msg = manager.check_node_npm()
            >>> success
            True
        """
        current_time = time.time()
        if (current_time - self.stats["last_check_time"]) < 60 and (
            "node" in self._version_cache and "npm" in self._version_cache
        ):
            node = self._version_cache["node"]
            npm = self._version_cache["npm"]
            return True, f"{node} and {npm} found."

        try:
            # Check node version
            node_proc = self._run_command(["node", "--version"], timeout=5)
            if node_proc.returncode != 0:
                return (
                    False,
                    "Node.js not found. Please install Node.js from https://nodejs.org/",
                )

            # Check npm version
            npm_proc = self._run_command(["npm", "--version"], timeout=5)
            if npm_proc.returncode != 0:
                return (
                    False,
                    "npm not found. Please install Node.js from https://nodejs.org/",
                )

            # Cache results
            node = DependencyVersion("Node.js", node_proc.stdout.strip())
            npm = DependencyVersion("npm", npm_proc.stdout.strip())
            self._version_cache["node"] = node
            self._version_cache["npm"] = npm
            self.stats["last_check_time"] = current_time

            return True, f"{node} and {npm} found."
        except FileNotFoundError:
            return (
                False,
                "Node.js and/or npm not found. Please install Node.js from https://nodejs.org/",
            )
        except subprocess.TimeoutExpired:
            return False, "Timeout checking Node.js/npm versions"
        except CommandExecutionError as e:
            return False, f"Error checking Node.js/npm: {str(e)}"

    def check_repomix(self) -> CommandResult:
        """Check if Repomix is installed globally.

        Returns:
            Tuple of (success, message) indicating installation status

        Raises:
            FileNotFoundError: If Repomix executable is not found
            CommandExecutionError: If version check command fails
            subprocess.TimeoutExpired: If version check times out

        Examples::
            >>> manager = DependencyManager()
            >>> success, msg = manager.check_repomix()
            >>> isinstance(success, bool)
            True
        """
        current_time = time.time()
        if (
            current_time - self.stats["last_check_time"]
        ) < 60 and "repomix" in self._version_cache:
            version = self._version_cache["repomix"]
            return True, f"{version} found."

        try:
            result = self._run_command(["repomix", "--version"], timeout=5)
            if result.returncode == 0:
                version = DependencyVersion(
                    "Repomix",
                    result.stdout.strip(),
                    True,
                    current_time,
                    shutil.which("repomix"),
                )
                self._version_cache["repomix"] = version
                self.stats["last_check_time"] = current_time
                return True, f"{version} found."
            return False, "Repomix not found."
        except FileNotFoundError:
            return False, "Repomix not found."
        except subprocess.TimeoutExpired:
            return False, "Timeout checking Repomix version"
        except CommandExecutionError as e:
            return False, f"Error checking Repomix: {str(e)}"

    def install_repomix(self) -> CommandResult:
        """Install Repomix globally using npm.

        Returns:
            Tuple of (success, message) indicating installation result

        Raises:
            CommandExecutionError: If npm install command fails
            subprocess.TimeoutExpired: If installation times out

        Examples::
            >>> manager = DependencyManager()
            >>> success, msg = manager.install_repomix()
            >>> isinstance(success, bool)
            True
        """
        start_time = time.time()
        self.stats["install_attempts"] += 1

        try:
            logger.info("Installing Repomix globally...")
            result = self._run_command(["npm", "install", "-g", "repomix"], timeout=60)

            install_time = (time.time() - start_time) * 1000
            self.stats["total_install_time_ms"] += install_time

            if result.returncode == 0:
                logger.info(f"Repomix installed successfully in {install_time:.2f}ms")
                # Clear version cache to force fresh check
                self._version_cache.pop("repomix", None)
                return True, "Repomix installed successfully."
            return False, f"Failed to install Repomix: {result.stderr}"
        except subprocess.TimeoutExpired:
            return False, "Timeout installing Repomix"
        except CommandExecutionError as e:
            return False, f"Error installing Repomix: {str(e)}"


def ensure_dependencies(debug: bool = False) -> bool:
    """Ensure all required dependencies are installed.

    This function checks for Node.js, npm, and Repomix installations,
    attempting to install Repomix if it's not found.

    Args:
        debug: Enable debug logging and version tracking

    Returns:
        True if all dependencies are satisfied, False otherwise

    Raises:
        CommandExecutionError: If dependency checks or installation fails

    Examples::
        >>> success = ensure_dependencies(debug=True)
        >>> isinstance(success, bool)
        True
    """
    manager = DependencyManager(debug=debug)

    # Check Node.js and npm
    node_ok, node_msg = manager.check_node_npm()
    if not node_ok:
        print(f"Error: {node_msg}", file=sys.stderr)
        return False

    # Check Repomix
    repomix_ok, repomix_msg = manager.check_repomix()
    if not repomix_ok:
        print("Installing Repomix...", file=sys.stderr)
        install_ok, install_msg = manager.install_repomix()
        if not install_ok:
            print(f"Error: {install_msg}", file=sys.stderr)
            return False
        print("Repomix installed successfully.", file=sys.stderr)

    if debug:
        print("\nDependency Manager Statistics:", file=sys.stderr)
        for key, value in manager.stats.items():
            print(f"{key}: {value}", file=sys.stderr)

    return True
