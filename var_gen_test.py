from numpy.matrixlib import defmatrix
import fauxreal as var_gen
import json

fixed, dynamic, transformed, composites, dataframes = var_gen.generate("/Users/dodos/Documents/repositories/vatsa_codes/Variable Generation/fauxreal_config.json")

"""
print("\nFixed Variables:")
print(fixed)

for key, value in fixed.items():
    print(f"{key}: {value}")

print("\nDynamic Variables:")
print(dynamic)
for key, value in dynamic.items():
    print(f"{key}: {value}")

print("\nTransformed Variables:")
print(transformed)
for key, value in transformed.items():
    print(f"{key}: {value}")
"""
print("\nComposite Variables:")
print(json.dumps(composites, indent=4))
print("\nDataFrames:")
import pandas as pd
pd.set_option('display.max_columns', None)
print(dataframes["transactions_df"].head())
