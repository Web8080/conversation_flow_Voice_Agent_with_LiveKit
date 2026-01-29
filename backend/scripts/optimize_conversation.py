"""
Conversation Flow Optimization Script

Analyzes conversation flows and suggests improvements:
1. Identifies common failure points
2. Suggests state transition improvements
3. Optimizes retry logic
"""

import json
from typing import List, Dict, Any
from datetime import datetime
from utils.logger import logger


class ConversationAnalyzer:
    def __init__(self):
        self.conversations = []
    
    def load_conversations(self, file_path: str):
        """Load conversation logs from JSON file"""
        with open(file_path, 'r') as f:
            self.conversations = json.load(f)
        logger.info(f"Loaded {len(self.conversations)} conversations")
    
    def analyze_state_transitions(self) -> Dict[str, Any]:
        """Analyze state transition patterns"""
        transitions = {}
        
        for conv in self.conversations:
            states = conv.get("states", [])
            for i in range(len(states) - 1):
                from_state = states[i]
                to_state = states[i + 1]
                key = f"{from_state} -> {to_state}"
                transitions[key] = transitions.get(key, 0) + 1
        
        return transitions
    
    def identify_failure_points(self) -> List[Dict[str, Any]]:
        """Identify states where conversations fail or retry frequently"""
        failures = []
        
        for conv in self.conversations:
            if conv.get("status") == "failed":
                states = conv.get("states", [])
                if states:
                    failure_state = states[-1]
                    failures.append({
                        "state": failure_state,
                        "reason": conv.get("failure_reason", "unknown")
                    })
        
        failure_counts = {}
        for failure in failures:
            state = failure["state"]
            failure_counts[state] = failure_counts.get(state, 0) + 1
        
        return sorted(failure_counts.items(), key=lambda x: x[1], reverse=True)
    
    def suggest_improvements(self, transitions: Dict[str, Any], failures: List[tuple]) -> List[str]:
        """Generate improvement suggestions"""
        suggestions = []
        
        fallback_transitions = [k for k, v in transitions.items() if "fallback" in k.lower()]
        if len(fallback_transitions) > len(transitions) * 0.2:
            suggestions.append("High fallback rate detected. Consider improving input validation.")
        
        if failures:
            top_failure_state = failures[0][0]
            suggestions.append(f"Most failures occur in '{top_failure_state}'. Review retry logic and prompts.")
        
        avg_turns = sum(len(c.get("states", [])) for c in self.conversations) / len(self.conversations) if self.conversations else 0
        if avg_turns > 10:
            suggestions.append("Conversations are taking too many turns. Consider simplifying the flow.")
        
        return suggestions


def main():
    """Main analysis function"""
    analyzer = ConversationAnalyzer()
    
    sample_conversations = [
        {
            "session_id": "session_1",
            "states": ["greeting", "collect_date", "fallback"],
            "status": "failed",
            "failure_reason": "date extraction failed"
        },
        {
            "session_id": "session_2",
            "states": ["greeting", "collect_date", "collect_time", "confirmation", "terminal"],
            "status": "completed"
        }
    ]
    
    analyzer.conversations = sample_conversations
    
    print("=== State Transition Analysis ===")
    transitions = analyzer.analyze_state_transitions()
    for transition, count in sorted(transitions.items(), key=lambda x: x[1], reverse=True):
        print(f"{transition}: {count}")
    
    print("\n=== Failure Point Analysis ===")
    failures = analyzer.identify_failure_points()
    for state, count in failures:
        print(f"{state}: {count} failures")
    
    print("\n=== Improvement Suggestions ===")
    suggestions = analyzer.suggest_improvements(transitions, failures)
    for suggestion in suggestions:
        print(f"- {suggestion}")


if __name__ == "__main__":
    main()


