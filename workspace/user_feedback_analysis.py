# Script to analyze user feedback
# This will categorize feedback by pain points

import json

# Sample feedback data
feedback_data = []  # Load from DB

# Categorize feedback
categorized_feedback = {}
for feedback in feedback_data:
    category = feedback['category']
    if category not in categorized_feedback:
        categorized_feedback[category] = []
    categorized_feedback[category].append(feedback)

# Output categorized feedback
print(json.dumps(categorized_feedback, indent=4))