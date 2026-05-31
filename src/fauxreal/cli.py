import argparse
from fauxreal.engine import generate

import json
import os
from fauxreal.engine import generate

def generate_init_config():
    example_config = {
        "$schema": "https://raw.githubusercontent.com/svr-s/fauxreal/main/fauxreal-schema.json",
        "fauxreal_config": {
            "description": "Auto-generated example configuration for Fauxreal",
            "seed": 12345,
            "fixed_variables": [
                {
                    "name": "environment",
                    "type": "string",
                    "value": "development"
                }
            ],
            "faker_variables": [
                {
                    "name": "customer_email",
                    "provider": "email"
                }
            ],
            "dynamic_variables": [
                {
                    "name": "age",
                    "type": "int",
                    "generation_rules": {"min": 18, "max": 65}
                }
            ],
            "transformations": [
                {
                    "name": "formatted_age",
                    "source": "age",
                    "actions": [
                        {"action": "cast_to_string"},
                        {"action": "append", "value": " years old"}
                    ]
                }
            ],
            "composite_variables": [
                {
                    "name": "user_payload",
                    "type": "dict",
                    "schema": {
                        "email": {"ref": "customer_email"},
                        "age": {"ref": "formatted_age"}
                    }
                }
            ],
            "dataframes": [
                {
                    "name": "users_df",
                    "num_rows": 10,
                    "columns": [
                        {"name": "env", "ref": "environment"},
                        {"name": "email", "ref": "customer_email"},
                        {"name": "age_desc", "ref": "formatted_age"}
                    ]
                }
            ],
            "exports": [
                {
                    "type": "csv",
                    "source": "users_df",
                    "filepath": "users_output.csv"
                }
            ]
        }
    }
    
    filepath = "example_config.json"
    with open(filepath, "w") as f:
        json.dump(example_config, f, indent=4)
    print(f"✅ Generated {filepath} in the current directory.")
    print("Run this config using: python -m fauxreal.cli --config example_config.json")

def main():
    parser = argparse.ArgumentParser(description="Fauxreal: Data Generation Engine")
    parser.add_argument("--config", type=str, default="fauxreal_config.json", help="Path to the JSON configuration file.")
    parser.add_argument("--override", action="append", help="Override fixed variables in key=value format (e.g. --override env=prod)")
    parser.add_argument("--seed", type=int, help="Set global seed for deterministic generation")
    parser.add_argument("--init", action="store_true", help="Generate an example_config.json file in the current directory")
    
    args = parser.parse_args()
    
    if args.init:
        generate_init_config()
        return
    
    overrides = {}
    if args.override:
        for item in args.override:
            if "=" in item:
                k, v = item.split("=", 1)
                k = k.strip()
                v = v.strip()
                
                # Basic type inference
                if v.lower() == "true": v = True
                elif v.lower() == "false": v = False
                else:
                    try: v = int(v)
                    except ValueError:
                        try: v = float(v)
                        except ValueError: pass
                        
                overrides[k] = v
                
    fixed, dynamic, transformed, composites, dataframes = generate(args.config, overrides, args.seed)
    
    print("\n[+] Fauxreal Generation Complete [+]")
    print(f"Fixed Variables Loaded: {len(fixed)}")
    print(f"Dynamic Variables Generated: {len(dynamic)}")
    print(f"Transformations Applied: {len(transformed)}")
    print(f"Composites Generated: {len(composites)}")
    
    if dataframes:
        import pandas as pd
        pd.set_option('display.max_columns', None)
        print("\nDataFrames Generated:")
        for df_name, df in dataframes.items():
            print(f"\n--- {df_name} ({len(df)} rows) ---")
            print(df.head(10))
            print("-" * 40)

if __name__ == "__main__":
    main()
