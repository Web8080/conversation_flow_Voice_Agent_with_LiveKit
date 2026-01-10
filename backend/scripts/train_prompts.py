"""
Prompt Optimization and Training Script

This script helps optimize prompts for the state machine by:
1. Testing different prompt variations
2. Measuring extraction accuracy
3. Generating prompt suggestions
"""

import asyncio
import json
from typing import List, Dict, Any
from agent.services.llm_service import create_llm_service
from utils.logger import logger


class PromptTester:
    def __init__(self):
        self.llm_service = create_llm_service()
        self.test_cases = []
    
    def load_test_cases(self, file_path: str):
        """Load test cases from JSON file"""
        with open(file_path, 'r') as f:
            self.test_cases = json.load(f)
        logger.info(f"Loaded {len(self.test_cases)} test cases")
    
    async def test_prompt(self, prompt_template: str, test_input: str, expected_output: Dict[str, Any]) -> Dict[str, Any]:
        """Test a single prompt and measure accuracy"""
        prompt = prompt_template.format(user_input=test_input)
        
        try:
            response = await self.llm_service.generate_response(prompt)
            
            result = {
                "input": test_input,
                "expected": expected_output,
                "actual": response,
                "match": False,
                "confidence": 0.0
            }
            
            if expected_output.get("type") == "date":
                result["match"] = self._validate_date(response, expected_output.get("value"))
            elif expected_output.get("type") == "time":
                result["match"] = self._validate_time(response, expected_output.get("value"))
            elif expected_output.get("type") == "name":
                result["match"] = expected_output.get("value").lower() in response.lower()
            
            return result
        except Exception as e:
            logger.error(f"Prompt test failed: {e}")
            return {
                "input": test_input,
                "expected": expected_output,
                "error": str(e)
            }
    
    def _validate_date(self, response: str, expected: str) -> bool:
        """Simple date validation"""
        return expected in response or response in expected
    
    def _validate_time(self, response: str, expected: str) -> bool:
        """Simple time validation"""
        return expected in response or response in expected
    
    async def test_prompt_variations(self, base_prompt: str, variations: List[str], test_cases: List[Dict]) -> Dict[str, Any]:
        """Test multiple prompt variations and compare results"""
        results = {}
        
        all_prompts = [base_prompt] + variations
        
        for prompt in all_prompts:
            prompt_results = []
            for test_case in test_cases:
                result = await self.test_prompt(
                    prompt,
                    test_case["input"],
                    test_case["expected"]
                )
                prompt_results.append(result)
            
            accuracy = sum(1 for r in prompt_results if r.get("match", False)) / len(prompt_results)
            results[prompt] = {
                "accuracy": accuracy,
                "results": prompt_results
            }
        
        return results
    
    def generate_prompt_suggestions(self, test_results: Dict[str, Any]) -> List[str]:
        """Generate improved prompt suggestions based on test results"""
        suggestions = []
        
        best_prompt = max(test_results.items(), key=lambda x: x[1]["accuracy"])
        accuracy = best_prompt[1]["accuracy"]
        
        if accuracy < 0.8:
            suggestions.append("Consider adding examples to the prompt")
            suggestions.append("Make the expected output format more explicit")
            suggestions.append("Add validation instructions to the prompt")
        
        return suggestions


async def main():
    """Main training function"""
    tester = PromptTester()
    
    test_cases = [
        {
            "input": "My name is John Doe",
            "expected": {"type": "name", "value": "John Doe"}
        },
        {
            "input": "I want to schedule for January 15th",
            "expected": {"type": "date", "value": "2025-01-15"}
        },
        {
            "input": "How about 2 PM?",
            "expected": {"type": "time", "value": "14:00"}
        },
        {
            "input": "Tomorrow at 3pm",
            "expected": {"type": "date", "value": "tomorrow"}
        },
    ]
    
    base_prompt = """Extract the {entity_type} from this text.
Text: "{user_input}"
Return only the {entity_type}, nothing else."""
    
    variations = [
        """Extract the {entity_type} from this text. Be precise and return only the value.
Text: "{user_input}"
Format: {format_example}""",
        
        """From the following text, identify and extract the {entity_type}.
Text: "{user_input}"
Return the {entity_type} in the format: {format_example}"""
    ]
    
    logger.info("Starting prompt optimization tests...")
    results = await tester.test_prompt_variations(base_prompt, variations, test_cases)
    
    print("\n=== Test Results ===")
    for prompt, result in results.items():
        print(f"\nPrompt: {prompt[:50]}...")
        print(f"Accuracy: {result['accuracy']:.2%}")
    
    suggestions = tester.generate_prompt_suggestions(results)
    if suggestions:
        print("\n=== Suggestions ===")
        for suggestion in suggestions:
            print(f"- {suggestion}")


if __name__ == "__main__":
    asyncio.run(main())

