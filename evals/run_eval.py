import json
import requests
import os

# Load the test cases
evals_dir = os.path.dirname(__file__)
cases_path = os.path.join(evals_dir, "cases.json")

with open(cases_path, "r", encoding="utf-8") as f:
    cases = json.load(f)

endpoint = "http://localhost:8000/enrich"
passed = 0
total = len(cases)

print(f"Running Eval Suite ({total} cases) against {endpoint}...\n" + "-"*50)

for case in cases:
    print(f"Testing Case {case['id']}: {case['input']['title']}")
    
    # Send the request to your API
    resp = requests.post(endpoint, json=case["input"], timeout=35)
    
    if resp.status_code == 200:
        actual_cat = resp.json().get("category")
        expected_cat = case["expected_category"]
        
        if actual_cat == expected_cat:
            passed += 1
            print(f"  [PASS] Expected: {expected_cat} | Got: {actual_cat}")
        else:
            print(f"  [FAIL] Expected: {expected_cat} | Got: {actual_cat}")
    else:
        print(f"  [ERROR] API returned status code {resp.status_code}")

print("-" * 50)
print(f"Final Score: {passed}/{total} ({(passed/total)*100:.1f}%)")