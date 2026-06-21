import os
import subprocess
import sys

print("\n🚀 Running FULL Automation Validation...\n")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ✅ Test runner path
test_file = os.path.join(BASE_DIR, "tests", "test_runner.py")

if not os.path.exists(test_file):
    print(f"❌ Test file not found: {test_file}")
    sys.exit(1)

print("🧪 Running Test Suite...\n")

result = subprocess.run(["python", test_file])

if result.returncode != 0:
    print("❌ Tests failed")
    sys.exit(1)

print("\n✅ Tests passed\n")

# ✅ Run main pipeline
print("🚀 Running Main Pipeline...\n")

main_file = os.path.join(BASE_DIR, "main.py")

result = subprocess.run(["python", main_file])

if result.returncode != 0:
    print("❌ Pipeline failed")
    sys.exit(1)

print("\n🎉 VALIDATION SUCCESS ✅")