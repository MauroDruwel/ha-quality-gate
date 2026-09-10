#!/usr/bin/env python3
"""Mauro Quality Gate (MQG) - Audit Script for Home Assistant Integrations.

Audits any local or remote Home Assistant custom component repository
against the Mauro Quality Gate standards and outputs a compliance report.

Usage:
    python audit_integration.py /path/to/local/integration
    python audit_integration.py MauroDruwel/Weathercloud-HA --remote
    python audit_integration.py --all-remote
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Mandatory GitHub topics
TOPIC_INTEGRATION = "home-assistant-integration"
TOPIC_HA = "home-assistant"
TOPIC_HACS = "hacs"
TOPIC_HACS_DEFAULT = "hacs-default"

# Mauro HA integrations on GitHub
MAURO_HA_REPOS = [
    "Weathercloud-HA",
    "SMA-ennexOS-cloud-HA",
    "homewizard-cloud-ha",
    "SolarlogLegacyHA",
    "HeyTelecomHA",
]


@dataclass
class CheckResult:
    category: str
    name: str
    passed: bool
    details: str
    severity: str = "ERROR"  # ERROR or WARNING


@dataclass
class AuditReport:
    target: str
    checks: list[CheckResult] = field(default_factory=list)

    def add(self, category: str, name: str, passed: bool, details: str, severity: str = "ERROR") -> None:
        self.checks.append(CheckResult(category, name, passed, details, severity))

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.checks if c.severity == "ERROR")

    @property
    def score_percentage(self) -> float:
        if not self.checks:
            return 0.0
        passed_count = sum(1 for c in self.checks if c.passed)
        return (passed_count / len(self.checks)) * 100

    def print_summary(self) -> None:
        print(f"\n=======================================================")
        print(f"  MAURO QUALITY GATE AUDIT: {self.target}")
        print(f"=======================================================")
        by_cat: dict[str, list[CheckResult]] = {}
        for c in self.checks:
            by_cat.setdefault(c.category, []).append(c)

        for cat, results in by_cat.items():
            print(f"\n[{cat.upper()}]")
            for r in results:
                status = "✅ PASS" if r.passed else ("⚠️  WARN" if r.severity == "WARNING" else "❌ FAIL")
                print(f"  {status:8} {r.name:<32} {r.details}")

        print(f"\n-------------------------------------------------------")
        status_text = "PASSED QUALITY GATE" if self.passed else "NEEDS REMEDIATION"
        print(f"  Result: {status_text} (Score: {self.score_percentage:.1f}%)")
        print(f"=======================================================\n")


def audit_local_dir(repo_path: Path, remote_name: str | None = None) -> AuditReport:
    report = AuditReport(target=str(repo_path))

    # 1. Repository Topics (if remote repo name available)
    if remote_name:
        try:
            out = subprocess.check_output(
                ["gh", "repo", "view", remote_name, "--json", "repositoryTopics,description"],
                stderr=subprocess.DEVNULL,
            )
            data = json.loads(out)
            topics = [t["name"] for t in (data.get("repositoryTopics") or [])]
            # Mandatory topic: home-assistant-integration
            report.add("GitHub Topics", "home-assistant-integration tag", TOPIC_INTEGRATION in topics, f"Topics: {topics}")
            # Topic hacs: expected when in official hacs-default (e.g. Weathercloud-HA)
            is_in_hacs_default = "Weathercloud-HA" in remote_name
            if is_in_hacs_default:
                report.add("GitHub Topics", "hacs tag (in hacs-default)", TOPIC_HACS in topics, f"Topics: {topics}")
            # Ensure topics are clean and not overloaded
            allowed_topics = {TOPIC_INTEGRATION, TOPIC_HACS} if is_in_hacs_default else {TOPIC_INTEGRATION}
            extra_topics = set(topics) - allowed_topics
            report.add("GitHub Topics", "Clean topics (not overloaded)", len(extra_topics) == 0, f"Extra: {list(extra_topics)}" if extra_topics else "Clean")
            report.add("GitHub Topics", "Repository description set", bool(data.get("description")), f"Description: {data.get('description')}")
        except Exception as err:
            report.add("GitHub Topics", "gh repo view", False, f"Could not check remote topics: {err}", severity="WARNING")

    # 2. Structure & Brand
    cc_dir = repo_path / "custom_components"
    has_cc = cc_dir.is_dir()
    report.add("Structure", "custom_components directory", has_cc, f"Exists: {has_cc}")

    domain_dir: Path | None = None
    if has_cc:
        subdirs = [p for p in cc_dir.iterdir() if p.is_dir() and not p.name.startswith(".")]
        if subdirs:
            domain_dir = subdirs[0]
            report.add("Structure", f"Single domain component ({domain_dir.name})", len(subdirs) == 1, f"Found: {[s.name for s in subdirs]}")
            brand_dir = domain_dir / "brand"
            has_brand = brand_dir.is_dir() and (brand_dir / "icon.png").is_file()
            report.add("Brand", "brand/icon.png exists", has_brand, f"Path: {brand_dir / 'icon.png'}")
        else:
            report.add("Structure", "Domain component directory", False, "custom_components is empty")

    # 3. hacs.json
    hacs_json = repo_path / "hacs.json"
    has_hacs = hacs_json.is_file()
    report.add("HACS", "hacs.json present", has_hacs, f"Exists: {has_hacs}")
    if has_hacs:
        try:
            hacs_data = json.loads(hacs_json.read_text())
            report.add("HACS", "hacs.json valid JSON & has name", bool(hacs_data.get("name")), f"name: {hacs_data.get('name')}")
            report.add("HACS", "hacs.json render_readme set", bool(hacs_data.get("render_readme")), f"render_readme: {hacs_data.get('render_readme')}", severity="WARNING")
        except Exception as err:
            report.add("HACS", "hacs.json valid JSON", False, str(err))

    # 4. manifest.json
    if domain_dir:
        manifest_path = domain_dir / "manifest.json"
        has_manifest = manifest_path.is_file()
        report.add("Manifest", "manifest.json exists", has_manifest, f"Path: {manifest_path}")
        if has_manifest:
            try:
                m_data = json.loads(manifest_path.read_text())
                report.add("Manifest", "codeowners has @MauroDruwel", "@MauroDruwel" in (m_data.get("codeowners") or []), f"codeowners: {m_data.get('codeowners')}")
                report.add("Manifest", "valid integration_type", m_data.get("integration_type") in ("device", "hub", "service"), f"type: {m_data.get('integration_type')}")
                report.add("Manifest", "iot_class configured", bool(m_data.get("iot_class")), f"iot_class: {m_data.get('iot_class')}")
                report.add("Manifest", "version matches semver", bool(re.match(r"^\d+\.\d+\.\d+", str(m_data.get("version", "")))), f"version: {m_data.get('version')}")
                report.add("Manifest", "config_flow is true", m_data.get("config_flow") is True, f"config_flow: {m_data.get('config_flow')}")
                report.add("Manifest", "issue_tracker URL set", bool(m_data.get("issue_tracker")), f"issue_tracker: {m_data.get('issue_tracker')}")
            except Exception as err:
                report.add("Manifest", "manifest.json valid JSON", False, str(err))

        # 5. Translations
        trans_dir = domain_dir / "translations"
        en_json = trans_dir / "en.json"
        nl_json = trans_dir / "nl.json"
        report.add("Translations", "translations/en.json exists", en_json.is_file(), f"Exists: {en_json.is_file()}")
        report.add("Translations", "translations/nl.json exists (Dutch)", nl_json.is_file(), f"Exists: {nl_json.is_file()}", severity="WARNING")

    # 6. Workflows
    wf_dir = repo_path / ".github" / "workflows"
    report.add("Workflows", ".github/workflows directory", wf_dir.is_dir(), f"Exists: {wf_dir.is_dir()}")
    if wf_dir.is_dir():
        wf_files = [f.name for f in wf_dir.iterdir() if f.is_file()]
        has_hassfest = False
        has_hacs_action = False
        has_tests = False
        has_format = False

        for f in wf_dir.glob("*.y*ml"):
            content = f.read_text()
            if "home-assistant/actions/hassfest" in content or "ha-quality-gate/.github/workflows/validate.yml" in content:
                has_hassfest = True
            if "hacs/action" in content or "ha-quality-gate/.github/workflows/validate.yml" in content:
                has_hacs_action = True
            if "pytest" in content or "ha-quality-gate/.github/workflows/tests.yml" in content:
                has_tests = True
            if "ruff" in content or "ha-quality-gate/.github/workflows/format.yml" in content:
                has_format = True

        report.add("Workflows", "Hassfest action workflow", has_hassfest, "Uses Hassfest directly or via MQG reusable validate.yml")
        report.add("Workflows", "HACS action validation workflow", has_hacs_action, "Uses HACS action directly or via MQG reusable validate.yml")
        report.add("Workflows", "pytest testing workflow", has_tests, "Runs pytest directly or via MQG reusable tests.yml")
        report.add("Workflows", "Ruff format/lint workflow", has_format, "Runs Ruff formatting/linting via MQG format.yml", severity="WARNING")

    # 7. Unit Tests
    tests_dir = repo_path / "tests"
    has_tests_dir = tests_dir.is_dir()
    report.add("Tests", "tests directory exists", has_tests_dir, f"Exists: {has_tests_dir}")
    if has_tests_dir:
        test_files = [f.name for f in tests_dir.glob("test_*.py")]
        report.add("Tests", "Test files present", len(test_files) > 0, f"Found: {test_files}")
        report.add("Tests", "conftest.py exists", (tests_dir / "conftest.py").is_file(), f"Exists: {(tests_dir / 'conftest.py').is_file()}")
        report.add("Tests", "test_config_flow.py exists", (tests_dir / "test_config_flow.py").is_file(), f"Exists: {(tests_dir / 'test_config_flow.py').is_file()}", severity="WARNING")
        report.add("Tests", "test_init.py exists", (tests_dir / "test_init.py").is_file(), f"Exists: {(tests_dir / 'test_init.py').is_file()}", severity="WARNING")

    # 8. Documentation
    readme = repo_path / "README.md"
    has_readme = readme.is_file()
    report.add("Documentation", "README.md exists", has_readme, f"Exists: {has_readme}")
    if has_readme:
        readme_text = readme.read_text()
        has_hacs_badge = "hacs" in readme_text.lower() and "badge" in readme_text.lower()
        report.add("Documentation", "HACS badge in README", has_hacs_badge, "Badge found" if has_hacs_badge else "Missing HACS badge", severity="WARNING")
        has_install_inst = "install" in readme_text.lower() or "hacs" in readme_text.lower()
        report.add("Documentation", "Installation instructions", has_install_inst, "Installation section found")

    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit Home Assistant integrations against Mauro Quality Gate.")
    parser.add_argument("target", nargs="?", default=".", help="Local path or GitHub repo (MauroDruwel/name)")
    parser.add_argument("--remote", action="store_true", help="Treat target as a GitHub repo name")
    parser.add_argument("--all-remote", action="store_true", help="Audit all known Mauro HA repos via GitHub API")

    args = parser.parse_args()

    if args.all_remote:
        reports = []
        for repo_name in MAURO_HA_REPOS:
            full_name = f"MauroDruwel/{repo_name}"
            # Clone or fetch repo temporarily
            temp_dir = Path(f"/tmp/mqg_audit/{repo_name}")
            temp_dir.parent.mkdir(parents=True, exist_ok=True)
            if temp_dir.exists():
                subprocess.run(["git", "pull", "--ff-only"], cwd=temp_dir, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.run(["gh", "repo", "clone", full_name, str(temp_dir), "--", "--depth=1"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if temp_dir.exists():
                r = audit_local_dir(temp_dir, remote_name=full_name)
                r.target = full_name
                reports.append(r)
                r.print_summary()
        return

    target_arg = Path(args.target)
    remote_name = None

    if args.remote or (not target_arg.exists() and ("/" in args.target or not args.target.startswith("."))):
        remote_name = args.target if "/" in args.target else f"MauroDruwel/{args.target}"
        temp_dir = Path(f"/tmp/mqg_audit/{remote_name.replace('/', '_')}")
        temp_dir.parent.mkdir(parents=True, exist_ok=True)
        if temp_dir.exists():
            subprocess.run(["git", "pull", "--ff-only"], cwd=temp_dir, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.run(["gh", "repo", "clone", remote_name, str(temp_dir), "--", "--depth=1"], check=True)
        target_path = temp_dir
    else:
        target_path = target_arg.resolve()
        # If it's a git repo, attempt to get remote name from git config
        try:
            rem_url = subprocess.check_output(
                ["git", "config", "--get", "remote.origin.url"],
                cwd=target_path,
                stderr=subprocess.DEVNULL,
                text=True,
            ).strip()
            # Extract owner/repo
            match = re.search(r"github\.com[:/]([^/]+/[^/.]+)", rem_url)
            if match:
                remote_name = match.group(1)
        except Exception:
            pass

    report = audit_local_dir(target_path, remote_name=remote_name)
    report.print_summary()
    sys.exit(0 if report.passed else 1)


if __name__ == "__main__":
    main()
