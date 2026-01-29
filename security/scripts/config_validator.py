#!/usr/bin/env python3
"""
Configuration Validator - DevSecOps

Validates security configuration files and environment setup.
"""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, List, Any
import sys


class ConfigValidator:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.errors = []
        self.warnings = []
    
    def validate_env_files(self) -> List[str]:
        """Validate .env files are properly configured"""
        issues = []
        
        # Check if .env.example exists
        env_example = self.project_root / "backend" / ".env.example"
        if not env_example.exists():
            issues.append("ERROR: backend/.env.example not found")
            return issues
        
        # Check required variables in .env.example
        required_vars = [
            "LIVEKIT_URL",
            "LIVEKIT_API_KEY",
            "LIVEKIT_API_SECRET",
            "OPENAI_API_KEY"
        ]
        
        example_content = env_example.read_text()
        for var in required_vars:
            if var not in example_content:
                issues.append(f"WARNING: {var} not in .env.example")
        
        # Check if actual .env is in .gitignore
        gitignore = self.project_root / ".gitignore"
        if gitignore.exists():
            gitignore_content = gitignore.read_text()
            if ".env" not in gitignore_content and ".env*" not in gitignore_content:
                issues.append("ERROR: .env files not in .gitignore")
        else:
            issues.append("ERROR: .gitignore file not found")
        
        return issues
    
    def validate_security_config(self) -> List[str]:
        """Validate security configuration YAML"""
        issues = []
        config_file = self.project_root / "security" / "config" / "security_config.yaml"
        
        if not config_file.exists():
            issues.append("WARNING: security_config.yaml not found")
            return issues
        
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            # Validate API security
            if "api_security" in config:
                cors = config["api_security"].get("cors", {})
                origins = cors.get("allowed_origins", [])
                if "*" in origins:
                    issues.append("ERROR: CORS allows all origins (*) - security risk")
                if not origins:
                    issues.append("WARNING: No CORS origins configured")
            
            # Validate rate limiting
            if "api_security" in config:
                rate_limit = config["api_security"].get("rate_limiting", {})
                if not rate_limit.get("enabled", False):
                    issues.append("WARNING: Rate limiting not enabled")
            
            # Validate input validation
            if "input_validation" not in config:
                issues.append("WARNING: Input validation configuration missing")
            
        except Exception as e:
            issues.append(f"ERROR: Failed to parse security config: {e}")
        
        return issues
    
    def validate_file_permissions(self) -> List[str]:
        """Check for overly permissive file permissions"""
        issues = []
        
        sensitive_files = [
            "backend/.env",
            "frontend/.env.local",
            "*.pem",
            "*.key",
            "*.p12"
        ]
        
        for pattern in sensitive_files:
            for file_path in self.project_root.rglob(pattern):
                if file_path.is_file():
                    stat = file_path.stat()
                    # Check if file is world-readable (should not be)
                    if stat.st_mode & 0o004:
                        issues.append(
                            f"WARNING: {file_path.relative_to(self.project_root)} "
                            "is world-readable - security risk"
                        )
        
        return issues
    
    def validate_docker_config(self) -> List[str]:
        """Validate Docker security configuration"""
        issues = []
        
        dockerfile = self.project_root / "backend" / "Dockerfile"
        if dockerfile.exists():
            content = dockerfile.read_text()
            
            # Check for root user
            if "USER root" in content and "USER" not in content.split("USER root")[1].split("\n")[:5]:
                issues.append("WARNING: Dockerfile may run as root user")
            
            # Check for secrets in Dockerfile
            if "password" in content.lower() or "secret" in content.lower():
                if "ARG" not in content or "ENV" not in content:
                    issues.append("WARNING: Potential secrets in Dockerfile")
        
        return issues
    
    def run_all_checks(self) -> Dict[str, Any]:
        """Run all validation checks"""
        print("🔍 Validating Security Configuration...")
        print("=" * 60)
        
        all_issues = []
        all_issues.extend(self.validate_env_files())
        all_issues.extend(self.validate_security_config())
        all_issues.extend(self.validate_file_permissions())
        all_issues.extend(self.validate_docker_config())
        
        errors = [i for i in all_issues if i.startswith("ERROR")]
        warnings = [i for i in all_issues if i.startswith("WARNING")]
        
        return {
            "errors": errors,
            "warnings": warnings,
            "total_issues": len(all_issues)
        }
    
    def print_report(self, results: Dict[str, Any]):
        """Print validation report"""
        print("\n" + "=" * 60)
        print("CONFIGURATION VALIDATION REPORT")
        print("=" * 60)
        
        if results["errors"]:
            print(f"\n❌ ERRORS ({len(results['errors'])}):")
            for error in results["errors"]:
                print(f"  {error}")
        
        if results["warnings"]:
            print(f"\n⚠️  WARNINGS ({len(results['warnings'])}):")
            for warning in results["warnings"]:
                print(f"  {warning}")
        
        if not results["errors"] and not results["warnings"]:
            print("\n✅ All configuration checks passed!")
        
        print("\n" + "=" * 60)


def main():
    project_root = sys.argv[1] if len(sys.argv) > 1 else "."
    
    validator = ConfigValidator(project_root)
    results = validator.run_all_checks()
    validator.print_report(results)
    
    sys.exit(1 if results["errors"] else 0)


if __name__ == "__main__":
    main()


