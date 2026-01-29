#!/usr/bin/env python3
"""
Security Scanning Script - DevSecOps

Performs automated security checks:
1. Dependency vulnerability scanning
2. Secrets detection in code
3. Security configuration checks
4. API security validation
"""

import os
import re
import json
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any
import argparse


class SecurityScanner:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.issues = []
        self.warnings = []
        
    def scan_dependencies(self) -> List[Dict[str, Any]]:
        """Scan Python and Node dependencies for vulnerabilities"""
        issues = []
        
        # Python dependencies
        if (self.project_root / "backend" / "requirements.txt").exists():
            print("Scanning Python dependencies...")
            try:
                result = subprocess.run(
                    ["pip-audit", "--format=json", "--requirement", "backend/requirements.txt"],
                    capture_output=True,
                    text=True,
                    cwd=self.project_root
                )
                if result.returncode == 0:
                    data = json.loads(result.stdout)
                    for vuln in data.get("vulnerabilities", []):
                        issues.append({
                            "type": "dependency",
                            "severity": "high",
                            "package": vuln.get("name"),
                            "message": f"Vulnerability: {vuln.get('id')}"
                        })
            except FileNotFoundError:
                self.warnings.append("pip-audit not installed. Install with: pip install pip-audit")
        
        # Node dependencies
        if (self.project_root / "frontend" / "package.json").exists():
            print("Scanning Node dependencies...")
            try:
                result = subprocess.run(
                    ["npm", "audit", "--json"],
                    capture_output=True,
                    text=True,
                    cwd=self.project_root / "frontend"
                )
                if result.returncode != 0:  # npm audit returns non-zero on vulnerabilities
                    data = json.loads(result.stdout)
                    for vuln_type, vulns in data.get("vulnerabilities", {}).items():
                        issues.append({
                            "type": "dependency",
                            "severity": vulns.get("severity", "medium"),
                            "package": vuln_type,
                            "message": f"Vulnerability: {vulns.get('title', 'Unknown')}"
                        })
            except Exception as e:
                self.warnings.append(f"npm audit failed: {e}")
        
        return issues
    
    def scan_secrets(self) -> List[Dict[str, Any]]:
        """Scan for hardcoded secrets and API keys"""
        issues = []
        
        # Patterns to detect secrets
        secret_patterns = [
            (r'api[_-]?key["\']?\s*[:=]\s*["\']([A-Za-z0-9_\-]{20,})["\']', "API Key"),
            (r'secret["\']?\s*[:=]\s*["\']([A-Za-z0-9_\-]{20,})["\']', "Secret"),
            (r'password["\']?\s*[:=]\s*["\']([^"\']{8,})["\']', "Password"),
            (r'sk-[A-Za-z0-9]{32,}', "OpenAI API Key"),
            (r'AIza[0-9A-Za-z\-_]{35}', "Google API Key"),
            (r'-----BEGIN PRIVATE KEY-----', "Private Key"),
            (r'-----BEGIN RSA PRIVATE KEY-----', "RSA Private Key"),
            (r'AKIA[0-9A-Z]{16}', "AWS Access Key"),
        ]
        
        # Files to scan (exclude certain directories)
        exclude_dirs = {'.git', 'node_modules', '__pycache__', 'venv', '.venv', 'dist', 'build'}
        
        for file_path in self.project_root.rglob('*'):
            if file_path.is_file() and not any(exclude in file_path.parts for exclude in exclude_dirs):
                # Skip binary files
                if file_path.suffix in {'.png', '.jpg', '.jpeg', '.gif', '.pdf', '.zip'}:
                    continue
                
                try:
                    content = file_path.read_text(errors='ignore')
                    for pattern, secret_type in secret_patterns:
                        matches = re.finditer(pattern, content, re.IGNORECASE)
                        for match in matches:
                            line_num = content[:match.start()].count('\n') + 1
                            issues.append({
                                "type": "secret",
                                "severity": "critical",
                                "file": str(file_path.relative_to(self.project_root)),
                                "line": line_num,
                                "message": f"Potential {secret_type} found: {match.group(0)[:20]}..."
                            })
                except Exception:
                    pass
        
        return issues
    
    def check_env_files(self) -> List[Dict[str, Any]]:
        """Check .env files for security issues"""
        issues = []
        
        env_files = list(self.project_root.rglob('.env')) + list(self.project_root.rglob('.env.*'))
        
        for env_file in env_files:
            # Check if .env is in .gitignore
            gitignore = self.project_root / '.gitignore'
            if gitignore.exists():
                gitignore_content = gitignore.read_text()
                if '.env' not in gitignore_content and '.env*' not in gitignore_content:
                    issues.append({
                        "type": "configuration",
                        "severity": "high",
                        "file": str(env_file.relative_to(self.project_root)),
                        "message": ".env file not in .gitignore - risk of committing secrets"
                    })
            
            # Check if actual .env has real secrets (not .example)
            if env_file.name != '.env.example' and env_file.exists():
                content = env_file.read_text()
                if 'your-api-key' not in content.lower() and 'placeholder' not in content.lower():
                    # Real .env file - should not be committed
                    if '.git' in env_file.parts:
                        issues.append({
                            "type": "configuration",
                            "severity": "critical",
                            "file": str(env_file.relative_to(self.project_root)),
                            "message": "Real .env file found in repository - remove immediately!"
                        })
        
        return issues
    
    def check_api_security(self) -> List[Dict[str, Any]]:
        """Check API endpoints for security issues"""
        issues = []
        
        # Check frontend API routes
        api_routes = list((self.project_root / "frontend" / "app" / "api").rglob("*.ts"))
        api_routes += list((self.project_root / "frontend" / "app" / "api").rglob("*.tsx"))
        
        for route_file in api_routes:
            content = route_file.read_text()
            
            # Check for missing authentication
            if 'POST' in content or 'GET' in content:
                if 'authentication' not in content.lower() and 'auth' not in content.lower():
                    if 'token' not in content.lower() or 'verify' not in content.lower():
                        issues.append({
                            "type": "api",
                            "severity": "high",
                            "file": str(route_file.relative_to(self.project_root)),
                            "message": "API endpoint may be missing authentication"
                        })
            
            # Check for SQL injection risks
            if 'query' in content and 'sql' in content.lower():
                if not any(term in content.lower() for term in ['parameterized', 'prepared', 'orm', 'prisma']):
                    issues.append({
                        "type": "api",
                        "severity": "high",
                        "file": str(route_file.relative_to(self.project_root)),
                        "message": "Potential SQL injection risk - use parameterized queries"
                    })
        
        return issues
    
    def check_cors_config(self) -> List[Dict[str, Any]]:
        """Check CORS configuration"""
        issues = []
        
        # Check Next.js config
        next_config = self.project_root / "frontend" / "next.config.js"
        if next_config.exists():
            content = next_config.read_text()
            if 'cors' not in content.lower() or '*origin*' in content:
                issues.append({
                    "type": "configuration",
                    "severity": "medium",
                    "file": "frontend/next.config.js",
                    "message": "CORS configuration may allow all origins - restrict to specific domains"
                })
        
        return issues
    
    def run_all_checks(self):
        """Run all security checks"""
        print("🔒 Running Security Scan...")
        print("=" * 60)
        
        all_issues = []
        all_issues.extend(self.scan_dependencies())
        all_issues.extend(self.scan_secrets())
        all_issues.extend(self.check_env_files())
        all_issues.extend(self.check_api_security())
        all_issues.extend(self.check_cors_config())
        
        return all_issues
    
    def generate_report(self, issues: List[Dict[str, Any]], output_file: str = None):
        """Generate security report"""
        report = {
            "scan_date": str(Path.cwd()),
            "total_issues": len(issues),
            "critical": len([i for i in issues if i.get("severity") == "critical"]),
            "high": len([i for i in issues if i.get("severity") == "high"]),
            "medium": len([i for i in issues if i.get("severity") == "medium"]),
            "issues": issues,
            "warnings": self.warnings
        }
        
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"\n📄 Report saved to {output_file}")
        
        # Print summary
        print("\n" + "=" * 60)
        print("SECURITY SCAN SUMMARY")
        print("=" * 60)
        print(f"Total Issues: {report['total_issues']}")
        print(f"  Critical: {report['critical']}")
        print(f"  High: {report['high']}")
        print(f"  Medium: {report['medium']}")
        
        if self.warnings:
            print(f"\n⚠️  Warnings: {len(self.warnings)}")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        if issues:
            print("\n🚨 Issues Found:")
            for issue in issues[:10]:  # Show first 10
                print(f"  [{issue['severity'].upper()}] {issue['type']}: {issue['message']}")
                if 'file' in issue:
                    print(f"    File: {issue['file']}")
        
        return report


def main():
    parser = argparse.ArgumentParser(description='Security Scanner for Voice Agent')
    parser.add_argument('--project-root', default='.', help='Project root directory')
    parser.add_argument('--output', help='Output JSON report file')
    parser.add_argument('--fail-on-critical', action='store_true', help='Exit with error if critical issues found')
    
    args = parser.parse_args()
    
    scanner = SecurityScanner(args.project_root)
    issues = scanner.run_all_checks()
    report = scanner.generate_report(issues, args.output)
    
    if args.fail_on_critical and report['critical'] > 0:
        print("\n❌ Critical issues found. Exiting with error code.")
        sys.exit(1)
    
    sys.exit(0 if report['total_issues'] == 0 else 1)


if __name__ == "__main__":
    main()


