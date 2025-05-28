import ollama\nimport json\n\n# Get the model list from Ollama API\nmodels_response = ollama.list()\n\n# Print raw response\nprint(\
=========
RAW
RESPONSE
=========\\n\)\nprint(json.dumps(models_response, indent=2))\n\n# Print model names\nprint(\\\n=========
MODEL
NAMES
=========\\n\)\nif 'models' in models_response:\n    for model in models_response['models']:\n        if 'model' in model:\n            print(f\Found
model
key:
model['model']
\)\n        elif 'name' in model:\n            print(f\Found
name
key:
model['name']
\)\n        else:\n            print(f\No
model
or
name
key
found
in:
model
\)\nelse:\n    print(\No
models
key
in
response\)\n\n# Check for specific models\nprint(\\\n=========
MODEL
CHECK
=========\\n\)\nLLM_MODEL = \phi3:mini\\nEMBEDDING_MODEL = \nomic-embed-text\\n\nfor model_name in [LLM_MODEL, EMBEDDING_MODEL]:\n    found = False\n    if 'models' in models_response:\n        for model in models_response['models']:\n            model_id = model.get('model') or model.get('name', '')\n            if model_id == model_name or model_id == f\
model_name
:latest\ or model_id.split(':')[0] == model_name:\n                found = True\n                print(f\✅
Found
model
matching
model_name
:
model_id
\)\n                break\n    if not found:\n        print(f\❌
Could
not
find
model
matching
model_name
\)
