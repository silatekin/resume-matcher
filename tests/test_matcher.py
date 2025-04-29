import json
import os
import pytest 
import sys
"""Follow the Arrange-Act-Assert (AAA) pattern
# Arrange: Set up the necessary inputs. 
Arrange: Set up the necessary inputs. This involves:
Loading or defining a specific parsed_resume dictionary.
Loading or defining a specific parsed_jd dictionary.
Defining the expected output dictionary 
(or specific parts of it, like the expected final score, 
skill score, matching skills list, etc.).

Act: Call your calculate_match_score function with the arranged inputs.

Assert: Use the testing framework's assertion functions to check if the actual 
output from the function matches your expected output.
"""

try:
    from ..matcher import calculate_match_score
except ImportError as e:
    print(f"ERROR importing calculate_match_score: {e}")
    print("Ensure:")
    print(" 1. test_matcher.py is inside the 'tests' folder.")
    print(" 2. matcher.py (or your equivalent file) is in the main 'RESUME-MATCHER' folder (parent of 'tests').")
    sys.exit(1) # Stop if we can't import the function
