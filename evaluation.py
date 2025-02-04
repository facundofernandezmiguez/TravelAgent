from deepeval.metrics import RelevanceMetric, AnswerConsistencyMetric
from deepeval.test_case import TestCase
from travel_agent import TravelAgent

def evaluate_response(user_input: str, expected_behavior: str = None):
    """
    Evaluate the travel agent's response using basic metrics.
    
    Args:
        user_input: The user's input message
        expected_behavior: Optional description of expected behavior/response
    """
    # Initialize the travel agent
    agent = TravelAgent()
    
    # Get the response
    response = agent.process_message(user_input)
    
    # Initialize metrics
    metrics = [
        RelevanceMetric(threshold=0.7),
        AnswerConsistencyMetric(threshold=0.7)
    ]
    
    # Create a test case
    test_case = TestCase(
        input=user_input,
        actual_output=response,
        expected_output=expected_behavior if expected_behavior else "",
        context="Travel agent assistant helping users plan their trips"
    )
    
    # Evaluate using each metric
    print("\n=== Evaluation Results ===")
    print(f"Input: {user_input}")
    print(f"Response: {response}")
    print("\nMetrics:")
    
    for metric in metrics:
        try:
            score = metric.measure(test_case)
            passed = score >= metric.threshold
            print(f"{metric.__class__.__name__}: {'✅ Passed' if passed else '❌ Failed'} (Score: {score:.2f})")
        except Exception as e:
            print(f"{metric.__class__.__name__}: Error - {str(e)}")

if __name__ == "__main__":
    # Example usage with test cases
    test_cases = [
        {
            "input": "I want to travel to Madrid next month",
            "expected": "I'll help you plan your trip to Madrid. To provide you with the best recommendations, I need some additional information..."
        },
        {
            "input": "What's the best time to visit Paris?",
            "expected": "The best time to visit Paris depends on your preferences. Spring (April to June) and Fall (September to November) are generally considered ideal..."
        }
    ]
    
    for test_case in test_cases:
        evaluate_response(test_case["input"], test_case["expected"])
        print("\n" + "="*50 + "\n")
