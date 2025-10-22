#!/usr/bin/env python3
"""
BDD Test Runner for 3D Hunting Simulator
Runs pytest-bdd tests with proper configuration and reporting.
"""

import pytest
import sys
import subprocess
import os
from pathlib import Path

def install_bdd_dependencies():
    """Install required BDD testing dependencies."""
    try:
        import pytest_bdd
        print("✓ pytest-bdd already installed")
    except ImportError:
        print("Installing pytest-bdd...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pytest-bdd'])
        
    try:
        import behave
        print("✓ behave already installed")
    except ImportError:
        print("Installing behave...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'behave'])

def run_bdd_tests():
    """Run all BDD tests with proper configuration."""
    
    # Set up test configuration
    pytest_args = [
        'features/',  # Test directory
        '-v',         # Verbose output
        '--tb=short', # Short traceback format
        '--cov=core', '--cov=player', '--cov=animals', '--cov=physics', '--cov=environment',
        '--cov-report=html:htmlcov_bdd',  # HTML coverage report
        '--cov-report=term',               # Terminal coverage report
        '-k', 'bdd or feature or scenario', # Only run BDD tests
        '--strict-markers',               # Strict marker checking
        '--disable-warnings',             # Clean output
    ]
    
    # Run pytest with BDD configuration
    exit_code = pytest.main(pytest_args)
    return exit_code

def generate_bdd_report():
    """Generate comprehensive BDD report."""
    print("\n" + "="*60)
    print("BDD TEST EXECUTION SUMMARY")
    print("="*60)
    
    print("\nFeatures Available:")
    features_dir = Path("features")
    feature_files = list(features_dir.glob("*.feature"))
    
    for feature_file in feature_files:
        print(f"  ✓ {feature_file.name}")
        
        # Count scenarios in each feature
        with open(feature_file) as f:
            lines = f.readlines()
            scenarios = [line for line in lines if line.strip().startswith('Scenario:')]
            print(f"    {len(scenarios)} scenarios")
    
    print(f"\nStep Definitions: features/step_definitions/")
    step_dir = Path("features/step_definitions")
    if step_dir.exists():
        step_files = list(step_dir.glob("*.py"))
        for step_file in step_files:
            print(f"  ✓ {step_file.name}")
    
    print(f"\nTotal Features: {len(feature_files)}")
    total_scenarios = sum(
        len([line for line in open(f) if line.strip().startswith('Scenario:')])
        for f in feature_files
    )
    print(f"Total Scenarios: {total_scenarios}")
    
    print(f"\nTo run BDD tests manually:")
    print(f"  pytest features/ -v")
    print(f"  pytest features/player_movement.feature -v")
    print(f"  pytest --bdd-features=features/ --bdd-steps=step_definitions/")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    print("Setting up BDD Testing Environment...")
    
    # Install dependencies
    install_bdd_dependencies()
    
    # Generate report
    generate_bdd_report()
    
    # Run tests
    print("\nRunning BDD Tests...")
    exit_code = run_bdd_tests()
    
    print("\nBDD Test Execution Complete!")
    sys.exit(exit_code)
