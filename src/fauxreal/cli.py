import argparse
from fauxreal.engine import generate

def main():
    parser = argparse.ArgumentParser(description="Fauxreal: Data Generation Engine")
    parser.add_argument("--config", type=str, default="fauxreal_config.json", help="Path to the JSON configuration file.")
    parser.add_argument("--override", action="append", help="Override fixed variables in key=value format (e.g. --override env=prod)")
    parser.add_argument("--seed", type=int, help="Set global seed for deterministic generation")
    
    args = parser.parse_args()
    
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
