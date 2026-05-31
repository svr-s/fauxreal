import json
import os
import sys

# Ensure src is in PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from fauxreal.schema import FauxrealConfig

def main():
    schema = FauxrealConfig.model_json_schema()
    
    output_path = os.path.join(os.path.dirname(__file__), "fauxreal-schema.json")
    with open(output_path, "w") as f:
        json.dump(schema, f, indent=4)
        
    print(f"✅ Generated JSON Schema at: {output_path}")
    print("Add '\"$schema\": \"./fauxreal-schema.json\"' to the top of your config files for autocomplete!")

if __name__ == "__main__":
    main()
