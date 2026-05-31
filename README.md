# Fauxreal

A powerful, declarative synthetic data and API payload generation engine with relational integrity, nested JSON support and DataFrame exports. It operates in distinct phases to weave static variables, dynamic fakes, transformations, and complex nested payloads seamlessly into Pandas DataFrames and JSON exports.

## Features
- **Deterministic Generation**: Supports strict seeding ensuring your mock datasets are identical across every CI/CD or testing run.
- **Relational Integrity**: Automatically resolves Foreign Keys. DataFrames can sample primary keys generated in upstream DataFrames to ensure valid relationships.
- **Cartesian Cross-Joins**: Easily generate every unique permutation of specified lists and inject them into DataFrames.
- **Deep Nesting**: Construct complex nested JSON payloads (Composites) by injecting previously generated variables into leaf nodes.
- **Conditional Logic**: Evaluate mathematical and boolean `expression` statements against current variables to conditionally generate values (e.g. `If amount > 80, result = REVIEW`).
- **Data Transforms**: Apply string transformations sequentially (padding, truncating, regex replacements) directly within the schema.

## Requirements
- Python 3.8+
- `pandas`
- `faker`
- `pyarrow` or `fastparquet` (Optional, for parquet export support)

---

## Installation & Usage

Install the package directly:
```bash
pip install fauxreal
```

### Python API
Import `generate` directly into your data pipeline or test suite:

```python
from fauxreal import generate

# 1. Execute the pipeline and retrieve only exactly what you want
# Supports .json, .json5, .yaml, and .yml configuration files!
results = generate(
    config_path="fauxreal_config.yaml", 
    targets=["system_environment", "user_identity_payload", "transactions_df"]
)

# 2. Access Data
print(results["system_environment"])
print(results["user_identity_payload"])

# 3. Extract your Pandas DataFrame
df = results["transactions_df"]
```
*Note: If you omit the `targets` parameter, the engine will return the legacy tuple containing all variables: `(fixed, dynamic (includes faker), transformed, composites, dataframes)`.*

### CLI Usage
You can run the engine directly from your terminal and dynamically override any fixed variables at runtime using the `--override` flag. This is extremely useful for CI/CD pipelines!

```bash
fauxreal \
    --config fauxreal_config.json5 \
    --override system_environment=staging \
    --override max_connections=999 \
    --seed 42
```

---

## Full Example Pipeline

Here is an example demonstrating how to construct a schema to generate users and their related transactions:

### 1. Sample Config (`fauxreal_config.json`)
```json
{
  "variable_generation_config": {
    "seed": 42,
    "fixed_variables": [
      { "name": "env", "type": "string", "value": "US" }
    ],
    "dynamic_variables": [
      {
        "name": "transaction_id",
        "type": "string",
        "generation_rules": { "format": "uuid" }
      },
      {
        "name": "amount",
        "type": "float",
        "generation_rules": { "min": 10.0, "max": 100.0, "decimal_places": 2 }
      }
    ],
    "dataframes": [
      {
        "name": "transactions_df",
        "count": 5,
        "columns": [
          { "name": "env", "ref": "env" },
          { "name": "id", "ref": "transaction_id" },
          { "name": "amount", "ref": "amount" }
        ]
      }
    ],
    "exports": [
      {
        "type": "csv",
        "ref": "transactions_df",
        "filepath": "output_transactions.csv"
      }
    ]
  }
}
```

### 2. Python Script
```python
from fauxreal import generate

results = generate(config_path='fauxreal_config.json', targets=['transactions_df'])
df = results['transactions_df']
print(df)
```

---

## Function Reference

### `generate(config_path="fauxreal_config.json", overrides=None, seed=None, targets=None)`

The primary extraction engine.

#### Parameters

* **`config_path`** `(str)`: *(Optional, Default: "fauxreal_config.json")*
  The filepath to your JSON configuration schema.
  
* **`overrides`** `(dict)`: *(Optional)*
  A dictionary of runtime overrides for fixed variables (e.g. `{"env": "prod"}`).

* **`seed`** `(int)`: *(Optional)*
  Optional global seed for deterministic generation. Overrides the seed set inside the JSON config.

* **`targets`** `(list)`: *(Optional)*
  A list of specific variable or DataFrame names to return exclusively. If provided, returns a `dict` mapping the target name to the generated object. If omitted, returns a 5-element tuple.

---

## Configuration Schema Details

This document outlines the structure of the `fauxreal_config.json` file. The configuration drives the `fauxreal` pipeline, which operates through these core mechanisms:

1. **Fixed Variables:** Static mappings of keys to values.
2. **Faker Variables:** Direct hooks into the `Faker` library to generate random names, emails, IDs, text, etc.
3. **Dynamic Variables:** Rule-based generation (random numbers, strings, UUIDs, dates, conditionals, etc.).
4. **Transformations:** Post-processing actions applied to generated variables (e.g., padding, replacing, truncating).
5. **Composite Variables:** Nested schemas (dicts, lists) that reference other generated variables.
6. **DataFrames:** Tabular structures that cross-join combinations and map columns to variables.
7. **Exports:** Automatically save DataFrames to CSVs and Composite payloads to JSON files.
8. **Command Line Interface (CLI):** Dynamically execute and override configurations via terminal.
9. **Python Usage:** Programmatic API to extract exact payloads or DataFrames in external scripts.

---

### Top-Level Structure

```json
{
  "variable_generation_config": {
    "description": "Optional description",
    "seed": 42,
    "fixed_variables": [...],
    "faker_variables": [...],
    "dynamic_variables": [...],
    "transformations": [...],
    "composite_variables": [...],
    "dataframes": [...],
    "exports": [...]
  }
}
```

---

### 1. Fixed Variables
Simple key-value pairs that are loaded directly into the state store.

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | The variable reference name. |
| `type` | string | `string`, `int`, `float`, `boolean`, `list`, `dict`, `date`. |
| `value`| any | The static value to assign. |

---

### 2. Dynamic Variables
Variables generated dynamically at runtime based on specific rules.

#### Common Fields
- `name`: Reference name.
- `type`: Data type. Must be one of: `"int"`, `"float"`, `"string"`, `"list"`, `"dict"`, `"date"`, `"date_range"`, `"choice"`, `"conditional"`, `"foreign_key"`, `"template"`.
- `generation_rules`: Object containing type-specific parameters.

#### Supported Variable Types Summary
- **`int` / `float`**: Uniform or Gaussian random numbers clamped between bounds.
- **`string`**: UUIDs, integers, or fully customized random strings.
- **`choice`**: Randomly selects an item from `options` based on `weights` (optional).
- **`conditional`**: Evaluates conditions using mathematical `expression` strings with `{{variable}}` string interpolation. If a condition evaluates to `True`, returns `result`. Fallback is `default`.
- **`date` / `date_range`**: Creates ISO date strings or arrays of dates using base anchors and offsets.
- **`template`**: Interpolates other variables into a string template using `{{variable_name}}` syntax.
- **`foreign_key`**: Randomly samples a value from a previously generated DataFrame's column (requires `dataframe` and `column` attributes).

#### Integer & Float Rules (`type: "int" | "float"`)
- `min`: Minimum value (number).
- `max`: Maximum value (number).
- `decimal_places`: (Float only) Number of decimal places (integer).
- `distribution`: (Optional) Setting this to `"normal"` switches from uniform random to Gaussian distribution.
  - If `"normal"`, you must provide `"mean"` and `"std_dev"`.
  - E.g., `{"distribution": "normal", "mean": 50, "std_dev": 15}` will group values closely around 50. Results are still strictly clamped between `min` and `max`.

#### String Rules (`type: "string"`)
- `format`: `"uuid"` (generates standard v4 UUID).
- `source`: `"integer"` or `"random_string"`.
  - If `"integer"`: Uses `min` and `max` limits.
  - If `"random_string"`:
    - `min_length`, `max_length`: String boundaries.
    - `include_mixed_case`: boolean.
    - `include_alphanumeric`: boolean.
    - `include_special_characters`: boolean.
    - `special_characters`: List of string chars, e.g., `["!", "@", "#"]`.

#### Choice Rules (`type: "choice"`)
Randomly selects one item from a list, with optional probability weighting.
- `options`: List of items to pick from.
- `weights`: (Optional) List of probabilities. Must be the same length as `options`. If omitted, uniform distribution is used.
- Example: `{"options": ["SUCCESS", "FAILED"], "weights": [0.9, 0.1]}`

#### Template Rules (`type: "template"`)
Dynamically constructs a string by injecting previously generated variables into placeholders.
- `template`: A string containing placeholders wrapped in double curly braces (e.g., `"{{var_name}}"`).
- Example: `{"template": "Receipt for {{customer_name}}: A transaction of ${{transaction_amount_usd}} was {{transaction_status}}."}`

#### Conditional Variable
```json
{
  "name": "transaction_status",
  "type": "conditional",
  "generation_rules": {
    "conditions": [
      {
        "expression": "{{transaction_amount}} > 80",
        "result": "REVIEW"
      },
      {
        "expression": "{{transaction_amount}} > 50",
        "result": "PENDING"
      }
    ],
    "default": "SUCCESS"
  }
}
```

#### Foreign Key Variable (`type: "foreign_key"`)
Randomly samples a value from a previously generated DataFrame's column (requires `dataframe` and `column` attributes).
```json
{
  "name": "transaction_fk",
  "type": "foreign_key",
  "generation_rules": {
    "dataframe": "transactions_df",
    "column": "id"
  }
}
```

#### Faker / Semantic Rules (`type: "faker"`)
Requires `faker` to be installed (`pip install faker`). Allows you to generate highly realistic mocked data for almost any common field type natively.
- `provider`: The Faker provider method to call.
- Supported Providers include:
  - `name`, `first_name`, `last_name`
  - `email`, `company_email`, `domain_name`
  - `address`, `city`, `state`, `country`, `zipcode`
  - `company`, `job`, `catch_phrase`
  - `phone_number`, `ssn`
  - `text`, `sentence`, `paragraph`
  - `credit_card_number`, `iban`, `bban`
  - *Note:* Any valid Faker provider not requiring complex positional arguments is supported.

#### Date Rules (`type: "date"`)
Generates timestamps or standard dates.
- `anchor_date`: Base date to start calculations from. (`"today"`, `"2024-05-18"`, etc.)
- `date_offset`: Offset amount and unit (`"+7 days"`, `"-1 month"`, `"+1 years"`).
- `time_offset`: Sub-day offset (`"+5 hours"`, `"-30 minutes"`).
- `timezone`: Standard tz database name (e.g., `"UTC"`, `"EST"`, `"Europe/London"`).
- `format`: Desired output format string (e.g., `"YYYY-MM-DD"`, `"epoch"`).
- `include_timestamp`: boolean. If false and format is epoch, it zeroes out hours/minutes/seconds.
- `timestamp_format`: e.g., `"HH:mm:ss"` or literal strings like `"T12:00:00Z"`.

#### Date Range Rules (`type: "date_range"`)
Generates a *list* of dates based on start and end offsets.
- `start_anchor` / `end_anchor`: e.g., `"today"`.
- `start_offset` / `end_offset`: e.g., `"-5 days"`, `"+5 days"`.
- `step`: Interval between dates (e.g., `"1 days"`).
- `skip_weekends`: boolean. If true, Saturdays and Sundays will be excluded from the generated list.
- Uses standard formatting fields (`format`, `timezone`, `include_timestamp`).

---

### 3. Transformations
Transformations allow you to take a generated variable and apply sequential modifications.
- `name`: The new transformed variable's name.
- `ref`: The name of the previously generated variable to modify.
- `actions`: List of transformation objects.

#### Possible Actions:
- `{"action": "cast_to_string"}`
- `{"action": "pad_left", "pad_character": "0", "target_length": 9}`
- `{"action": "prepend", "value": "EMP-"}`
- `{"action": "append", "value": " USD"}`
- `{"action": "lowercase"}`
- `{"action": "truncate", "max_length": 10}`
- `{"action": "replace", "target": "[^a-z0-9]", "replacement": ".", "use_regex": true}`

---

### 4. Composite Variables
Composite variables allow you to construct rich nested JSON objects or lists containing references to other variables.
- `name`: Composite variable name.
- `type`: `"dict"` or `"list"`.
- `count`: How many to generate (e.g., `"count": 10`). Defaults to 1.
- `schema`: A nested structure defining the keys. Use `{"ref": "variable_name"}` to inject a generated value into the leaf nodes.

#### Dict Schema Example (with Deep Nesting)
You can nest dictionaries and lists infinitely. Schema resolution is fully recursive.
```json
{
  "name": "profile_payload",
  "type": "dict",
  "count": 5,
  "schema": {
    "user_id": { "ref": "random_user_id" },
    "line_items": { "ref": "line_item_payload" },
    "metadata": {
      "timestamp": { "ref": "timestamp_iso" }
    }
  }
}
```

#### List Schema Example
```json
{
  "name": "line_item_payload",
  "type": "list",
  "count": 5,
  "schema": { "ref": "transaction_amount" }
}
```

---

### 5. DataFrames
Generates Pandas DataFrames using combinations of the previously defined variables.

- `name`: DataFrame name.
- `count`: Number of rows to generate (fallback if `unique_combinations` is not used).
- `columns`: List of column mappings `[{"name": "col_1", "ref": "var_1"}]`.
- `unique_combinations`: (Optional) List of column names (e.g., `["env", "date"]`). 
  - *Note:* If provided, the referenced variables MUST be lists. The script will perform a Cartesian Cross-Join across all provided lists, guaranteeing every unique permutation appears exactly once. The resulting row count will be the multiplied lengths of those lists, completely overriding `count`.
- **Per-Row Dynamic Generation**: Any DataFrame columns pointing to Dynamic or Transformed variables that are *not* part of `unique_combinations` will be actively re-generated with fresh values for every single row in the DataFrame (e.g. generating unique random IDs and amounts per row).

---

### 6. Exports
Exports DataFrames or Composites to external files.

- `type`: `"csv"`, `"json"`, or `"parquet"` (Requires `pyarrow` or `fastparquet`).
- `ref`: The name of the DataFrame or Composite variable to export.
- `filepath`: Output file name.
- **`indent`**: (JSON only) Number of spaces for indentation (default: 4).

#### Example
```json
"exports": [
  {
    "type": "csv",
    "ref": "transactions_df",
    "filepath": "output_transactions.csv"
  },
  {
    "type": "json",
    "ref": "user_identity_payload",
    "filepath": "output_users.json",
    "indent": 4
  }
]
```

---

### 7. Command Line Interface (CLI)
You can run the engine directly from your terminal and dynamically override any fixed variables at runtime using the `--override` flag. This is extremely useful for CI/CD pipelines!

### Command Line Arguments
- `--config`: Path to your JSON configuration file (defaults to `fauxreal_config.json`).
- `--override`: Supply as many times as you want in `key=value` format.
  - The script will automatically infer strings, integers, floats, and booleans (`true`/`false`).
- `--seed`: An integer value to ensure exact reproducibility across multiple runs.

### Example
```bash
fauxreal \
    --config my_config.json \
    --override system_environment=staging \
    --override max_connections=999 \
    --seed 42
```

---

### 8. Python Usage

If you are importing this script into another Python file, you can call `generate()` to execute the pipeline. You can use the `targets` parameter to exclusively return the specific variables or DataFrames you need without dealing with large tuples:

```python
from fauxreal import generate

# Execute the pipeline and retrieve only exactly what you want
results = generate(
    config_path="fauxreal_config.json", 
    targets=["system_environment", "user_identity_payload", "transactions_df"]
)

# Access Data
print(results["system_environment"])
print(results["user_identity_payload"])

# Extract your Pandas DataFrame
df = results["transactions_df"]
```

If you omit the `targets` parameter, the engine will return the legacy tuple containing all variables: `(fixed, dynamic, transformed, composites, dataframes)`.
