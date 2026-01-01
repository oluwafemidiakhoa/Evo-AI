"""
LeetCode Integration for Autonomous Code Evolution

This module integrates with LeetCode problems to:
1. Parse problem descriptions
2. Extract test cases
3. Generate initial code population
4. Evaluate solutions
5. Compare against human benchmarks
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import httpx
import re


@dataclass
class TestCase:
    """A single test case for a LeetCode problem"""
    input_data: Dict[str, Any]
    expected_output: Any


@dataclass
class LeetCodeProblem:
    """Represents a LeetCode problem"""
    number: int
    title: str
    difficulty: str  # "Easy", "Medium", "Hard"
    description: str
    test_cases: List[TestCase]
    function_signature: str
    constraints: List[str]


class LeetCodeEvolver:
    """
    Autonomous LeetCode problem solver using evolutionary algorithms

    This class takes a LeetCode problem and:
    1. Generates multiple solution approaches
    2. Evolves them over generations
    3. Benchmarks against human solutions
    4. Returns the best evolved solution
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.client = httpx.AsyncClient()

    async def fetch_problem(self, problem_id: int) -> LeetCodeProblem:
        """
        Fetch a LeetCode problem by ID

        Args:
            problem_id: The LeetCode problem number (e.g., 1 for "Two Sum")

        Returns:
            LeetCodeProblem with all necessary information
        """
        # For now, we'll use hardcoded problems
        # Later, we can integrate with LeetCode's GraphQL API

        if problem_id == 1:  # Two Sum
            return self._get_two_sum_problem()
        else:
            raise NotImplementedError(f"Problem {problem_id} not yet implemented")

    def _get_two_sum_problem(self) -> LeetCodeProblem:
        """Returns the Two Sum problem definition"""
        return LeetCodeProblem(
            number=1,
            title="Two Sum",
            difficulty="Easy",
            description="""
Given an array of integers nums and an integer target, return indices of
the two numbers such that they add up to target.

You may assume that each input would have exactly one solution, and you
may not use the same element twice.

You can return the answer in any order.
            """,
            test_cases=[
                TestCase(
                    input_data={"nums": [2, 7, 11, 15], "target": 9},
                    expected_output=[0, 1]
                ),
                TestCase(
                    input_data={"nums": [3, 2, 4], "target": 6},
                    expected_output=[1, 2]
                ),
                TestCase(
                    input_data={"nums": [3, 3], "target": 6},
                    expected_output=[0, 1]
                ),
            ],
            function_signature="def twoSum(self, nums: List[int], target: int) -> List[int]:",
            constraints=[
                "2 <= nums.length <= 10^4",
                "-10^9 <= nums[i] <= 10^9",
                "-10^9 <= target <= 10^9",
                "Only one valid answer exists."
            ]
        )

    def generate_initial_population(
        self,
        problem: LeetCodeProblem,
        population_size: int = 10
    ) -> List[str]:
        """
        Generate initial population of solution approaches

        This creates diverse starting points:
        - Brute force
        - Hash map
        - Two pointers
        - Sort-based
        - Hybrid approaches

        Args:
            problem: The LeetCode problem
            population_size: Number of initial solutions to generate

        Returns:
            List of Python code strings
        """
        # This will use your Variant Agent to generate initial solutions
        # For now, here are some starter templates

        solutions = [
            # Brute force O(n²)
            '''
def twoSum(nums: List[int], target: int) -> List[int]:
    """Brute force approach"""
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            if nums[i] + nums[j] == target:
                return [i, j]
    return []
''',
            # Hash map O(n)
            '''
def twoSum(nums: List[int], target: int) -> List[int]:
    """Hash map approach"""
    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []
''',
            # Two pass hash map
            '''
def twoSum(nums: List[int], target: int) -> List[int]:
    """Two-pass hash map"""
    num_map = {num: i for i, num in enumerate(nums)}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in num_map and num_map[complement] != i:
            return [i, num_map[complement]]
    return []
''',
        ]

        return solutions[:population_size]

    async def evaluate_solution(
        self,
        code: str,
        problem: LeetCodeProblem
    ) -> Dict[str, Any]:
        """
        Evaluate a solution against test cases

        Returns:
            {
                "correct": bool,
                "passed_tests": int,
                "total_tests": int,
                "avg_runtime_ms": float,
                "memory_mb": float,
                "complexity": str  # e.g., "O(n)"
            }
        """
        import time
        import tracemalloc
        from typing import List

        results = {
            "correct": True,
            "passed_tests": 0,
            "total_tests": len(problem.test_cases),
            "avg_runtime_ms": 0.0,
            "memory_mb": 0.0,
            "complexity": "Unknown"
        }

        # Execute the code safely
        try:
            # Create namespace
            namespace = {"List": List}
            exec(code, namespace)
            solution_func = namespace.get("twoSum")

            if not solution_func:
                results["correct"] = False
                return results

            total_runtime = 0.0
            total_memory = 0.0

            for test_case in problem.test_cases:
                # Measure runtime
                start_time = time.perf_counter()
                tracemalloc.start()

                try:
                    result = solution_func(**test_case.input_data)

                    # Check correctness
                    if sorted(result) == sorted(test_case.expected_output):
                        results["passed_tests"] += 1
                    else:
                        results["correct"] = False

                except Exception as e:
                    results["correct"] = False
                    continue
                finally:
                    # Measure memory
                    current, peak = tracemalloc.get_traced_memory()
                    tracemalloc.stop()

                    # Record metrics
                    end_time = time.perf_counter()
                    total_runtime += (end_time - start_time) * 1000  # Convert to ms
                    total_memory += peak / 1024 / 1024  # Convert to MB

            # Calculate averages
            if results["passed_tests"] > 0:
                results["avg_runtime_ms"] = total_runtime / results["passed_tests"]
                results["memory_mb"] = total_memory / results["passed_tests"]

        except Exception as e:
            results["correct"] = False
            results["error"] = str(e)

        return results

    async def close(self):
        """Clean up resources"""
        await self.client.aclose()


# Example usage for testing
if __name__ == "__main__":
    import asyncio

    async def main():
        evolver = LeetCodeEvolver()

        # Fetch problem
        problem = await evolver.fetch_problem(1)
        print(f"Problem: {problem.title}")
        print(f"Difficulty: {problem.difficulty}")

        # Generate initial population
        solutions = evolver.generate_initial_population(problem, population_size=3)
        print(f"\nGenerated {len(solutions)} initial solutions")

        # Evaluate each solution
        for i, solution in enumerate(solutions):
            results = await evolver.evaluate_solution(solution, problem)
            print(f"\nSolution {i + 1}:")
            print(f"  Correct: {results['correct']}")
            print(f"  Passed: {results['passed_tests']}/{results['total_tests']}")
            print(f"  Runtime: {results['avg_runtime_ms']:.4f}ms")
            print(f"  Memory: {results['memory_mb']:.4f}MB")

        await evolver.close()

    asyncio.run(main())
