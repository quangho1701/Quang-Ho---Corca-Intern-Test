#!/usr/bin/env python3
"""
Comprehensive API Test Suite for Equation Solver
Tests standard equations, implicit multiplication, complex roots, edge cases, and security.
"""

import requests
import sys
from typing import Dict, List, Tuple, Optional

# Configuration
API_BASE_URL = "http://localhost:8000"
SOLVE_ENDPOINT = f"{API_BASE_URL}/solve"


class TestCase:
    """Represents a single test case with expected behavior."""
    
    def __init__(
        self,
        name: str,
        equation: str,
        expected_status: int,
        expected_result: Optional[str] = None,
        contains_text: Optional[List[str]] = None,
        category: str = "General"
    ):
        self.name = name
        self.equation = equation
        self.expected_status = expected_status
        self.expected_result = expected_result
        self.contains_text = contains_text or []
        self.category = category


def run_test(test: TestCase) -> Tuple[bool, str]:
    """
    Execute a single test case against the API.
    
    Returns:
        (passed, message) tuple
    """
    try:
        # Make POST request with JSON body
        response = requests.post(
            SOLVE_ENDPOINT,
            json={"equation": test.equation},
            timeout=5
        )
        
        # Check status code
        if response.status_code != test.expected_status:
            return False, f"Expected status {test.expected_status}, got {response.status_code}"
        
        # Parse JSON response
        try:
            data = response.json()
        except Exception as e:
            return False, f"Failed to parse JSON response: {e}"
        
        # Check for expected result (exact match)
        if test.expected_result is not None:
            actual = data.get("result") or data.get("error", "")
            if actual != test.expected_result:
                return False, f"Expected '{test.expected_result}', got '{actual}'"
        
        # Check for text that should be contained in response
        response_text = str(data)
        for text in test.contains_text:
            if text not in response_text:
                return False, f"Response missing expected text: '{text}'"
        
        return True, f"✓ {data.get('result') or data.get('error', 'OK')}"
        
    except requests.exceptions.ConnectionError:
        return False, "Connection failed - Is the server running?"
    except requests.exceptions.Timeout:
        return False, "Request timeout"
    except Exception as e:
        return False, f"Unexpected error: {e}"


def main():
    """Run all test cases and print results."""
    
    # Define comprehensive test suite
    test_cases = [
        # ========== STANDARD MATH ==========
        TestCase(
            name="Linear equation with fraction result",
            equation="2x + 4 = 10",
            expected_status=200,
            expected_result="x = 3",
            category="Standard Math"
        ),
        TestCase(
            name="Simple linear equation",
            equation="x + 5 = 12",
            expected_status=200,
            expected_result="x = 7",
            category="Standard Math"
        ),
        TestCase(
            name="Quadratic equation (two solutions)",
            equation="x^2 - 4 = 0",
            expected_status=200,
            contains_text=["x = -2", "x = 2"],
            category="Standard Math"
        ),
        
        # ========== IMPLICIT MULTIPLICATION ==========
        TestCase(
            name="Implicit multiplication: 2x",
            equation="2x = 10",
            expected_status=200,
            expected_result="x = 5",
            category="Implicit Multiplication"
        ),
        TestCase(
            name="Implicit multiplication: 3(x+2)",
            equation="3(x+2) = 15",
            expected_status=200,
            expected_result="x = 3",
            category="Implicit Multiplication"
        ),
        TestCase(
            name="Implicit multiplication: complex expression",
            equation="2(x+1) + 3x = 17",
            expected_status=200,
            expected_result="x = 3",
            category="Implicit Multiplication"
        ),
        
        # ========== COMPLEX/ROOTS ==========
        TestCase(
            name="Cubic equation (3 solutions)",
            equation="x^3 = 27",
            expected_status=200,
            contains_text=["x = 3"],  # Should have real solution x=3
            category="Complex/Roots"
        ),
        TestCase(
            name="Quadratic with complex roots",
            equation="x^2 + 1 = 0",
            expected_status=200,
            contains_text=["I", "-I"],  # Complex roots ±i
            category="Complex/Roots"
        ),
        
        # ========== SMART FALLBACK (abs, real-only) ==========
        TestCase(
            name="Absolute value equation (smart fallback)",
            equation="abs(x) = 5",
            expected_status=200,
            contains_text=["x = -5", "x = 5"],
            category="Smart Fallback"
        ),
        TestCase(
            name="Absolute value with offset",
            equation="abs(x - 3) = 2",
            expected_status=200,
            contains_text=["x = 1", "x = 5"],
            category="Smart Fallback"
        ),
        
        # ========== ERROR HANDLING ==========
        TestCase(
            name="Invalid syntax: double operator",
            equation="2 + + 2",
            expected_status=400,
            contains_text=["error"],
            category="Error Handling"
        ),
        TestCase(
            name="Invalid syntax: missing operand",
            equation="2x + = 10",
            expected_status=400,
            contains_text=["error"],
            category="Error Handling"
        ),
        TestCase(
            name="Empty equation",
            equation="",
            expected_status=400,
            contains_text=["Missing"],
            category="Error Handling"
        ),
        TestCase(
            name="Multiple equals signs",
            equation="x = 5 = 10",
            expected_status=400,
            contains_text=["multiple '=' signs"],
            category="Error Handling"
        ),
        
        # ========== SECURITY ==========
        TestCase(
            name="Code injection attempt: import",
            equation="import os",
            expected_status=400,
            contains_text=["error"],
            category="Security"
        ),
        TestCase(
            name="Code injection attempt: __import__",
            equation="__import__('os').system('ls')",
            expected_status=400,
            contains_text=["error"],
            category="Security"
        ),
        TestCase(
            name="Code injection attempt: eval-like",
            equation="eval('2+2')",
            expected_status=400,
            contains_text=["error"],
            category="Security"
        ),
    ]
    
    # Run all tests
    print("=" * 70)
    print("🧪 EQUATION SOLVER API TEST SUITE")
    print("=" * 70)
    print(f"Testing endpoint: {SOLVE_ENDPOINT}\n")
    
    results_by_category: Dict[str, List[Tuple[str, bool, str]]] = {}
    total_passed = 0
    total_failed = 0
    
    for test in test_cases:
        passed, message = run_test(test)
        
        # Track results by category
        if test.category not in results_by_category:
            results_by_category[test.category] = []
        results_by_category[test.category].append((test.name, passed, message))
        
        if passed:
            total_passed += 1
        else:
            total_failed += 1
    
    # Print results grouped by category
    for category, results in results_by_category.items():
        print(f"\n{'═' * 70}")
        print(f"📁 {category}")
        print(f"{'═' * 70}")
        
        for name, passed, message in results:
            status_icon = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status_icon} | {name}")
            if not passed or message.startswith("✓"):
                print(f"         {message}")
    
    # Print summary
    print(f"\n{'=' * 70}")
    print(f"📊 SUMMARY")
    print(f"{'=' * 70}")
    print(f"Total Tests: {total_passed + total_failed}")
    print(f"✅ Passed: {total_passed}")
    print(f"❌ Failed: {total_failed}")
    
    if total_failed == 0:
        print(f"\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total_failed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
