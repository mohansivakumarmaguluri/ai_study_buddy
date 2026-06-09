import traceback
from utils.gemini_helper import GeminiHelper

print("Preferred list:", GeminiHelper._get_models_to_try())
try:
    res = GeminiHelper.explain_concept('Binary Search Tree')
    print("SUCCESS:", res.keys())
except Exception as e:
    traceback.print_exc()
