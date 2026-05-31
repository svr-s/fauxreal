import json
import json5
import yaml

try:
    from pydantic import ValidationError
    from .schema import FauxrealConfig
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    
import os
import random
import uuid
import re
import string
import logging
from datetime import datetime, timedelta
import pandas as pd
import itertools
import zoneinfo
import ast
import operator

try:
    from faker import Faker
    fake = Faker()
    FAKER_AVAILABLE = True
except ImportError:
    FAKER_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def _parse_expression(expr_str: str):
    """Safely evaluates a boolean or mathematical expression string using an AST."""
    allowed_operators = {
        ast.Add: operator.add, ast.Sub: operator.sub,
        ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.Eq: operator.eq, ast.NotEq: operator.ne,
        ast.Lt: operator.lt, ast.LtE: operator.le,
        ast.Gt: operator.gt, ast.GtE: operator.ge,
        ast.Not: operator.not_,
    }

    def _parse_node(node):
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.BinOp):
            return allowed_operators[type(node.op)](_parse_node(node.left), _parse_node(node.right))
        elif isinstance(node, ast.UnaryOp):
            return allowed_operators[type(node.op)](_parse_node(node.operand))
        elif isinstance(node, ast.BoolOp):
            if isinstance(node.op, ast.And):
                return all(_parse_node(v) for v in node.values)
            elif isinstance(node.op, ast.Or):
                return any(_parse_node(v) for v in node.values)
        elif isinstance(node, ast.Compare):
            left = _parse_node(node.left)
            for op, right in zip(node.ops, node.comparators):
                if not allowed_operators[type(op)](left, _parse_node(right)):
                    return False
                left = _parse_node(right)
            return True
        else:
            raise ValueError(f"Unsupported expression node: {type(node)}")

    return _parse_node(ast.parse(expr_str, mode='eval').body)

def load_config(filepath):
    """
    Loads and parses the JSON, JSON5, or YAML configuration file containing variable definitions.
    
    Args:
        filepath (str): The path to the config file.
        
    Returns:
        dict: The parsed "variable_generation_config" dictionary.
    """
    try:
        ext = os.path.splitext(filepath)[1].lower()
        with open(filepath, 'r') as f:
            if ext in ['.yaml', '.yml']:
                data = yaml.safe_load(f)
            elif ext == '.json5':
                data = json5.load(f)
            else:
                data = json.load(f)
            
            if PYDANTIC_AVAILABLE:
                try:
                    # Validate the raw data using Pydantic
                    validated_model = FauxrealConfig(**data)
                    return validated_model.variable_generation_config.model_dump(exclude_none=True, by_alias=True)
                except ValidationError as ve:
                    logging.error(f"Configuration Validation Error in {filepath}:\n{ve}")
                    raise
            
            return data.get("variable_generation_config", {})
    except FileNotFoundError:
        logging.error(f"Configuration file not found: {filepath}")
        return {}
    except ValidationError:
        # Re-raise ValidationError so user gets strict feedback
        raise
    except Exception as e:
        logging.error(f"Unexpected error loading config {filepath}: {e}")
        return {}

def generate_fixed(variables_def):
    """
    Parses and loads fixed variables (static mappings) into a state store.
    
    Args:
        variables_def (list): A list of dictionaries defining fixed variables.
        
    Returns:
        dict: A dictionary of {name: value} pairs.
    """
    variables = {}
    if not isinstance(variables_def, list):
        logging.warning("fixed_variables must be a list.")
        return variables
        
    for var in variables_def:
        try:
            variables[var["name"]] = var["value"]
        except KeyError:
            logging.warning(f"Malformed fixed variable definition: {var}")
    return variables

def parse_date_offset(offset_str):
    try:
        if not isinstance(offset_str, str):
            return timedelta(0)
            
        offset_str = offset_str.strip()
        match = re.match(r"([+-]?\d+)\s+(days?|months?|years?|hours?|minutes?|seconds?)", offset_str)
        if not match:
            return timedelta(0)
        
        val = int(match.group(1))
        unit = match.group(2)
        if unit.startswith("day"):
            return timedelta(days=val)
        elif unit.startswith("month"):
            return timedelta(days=val * 30)
        elif unit.startswith("year"):
            return timedelta(days=val * 365)
        elif unit.startswith("hour"):
            return timedelta(hours=val)
        elif unit.startswith("minute"):
            return timedelta(minutes=val)
        elif unit.startswith("second"):
            return timedelta(seconds=val)
        return timedelta(0)
    except Exception as e:
        logging.warning(f"Failed to parse date offset '{offset_str}': {e}")
        return timedelta(0)

def _get_tz_aware_base_date(rules):
    timezone_str = rules.get("timezone", "UTC")
    if timezone_str == "EST":
        timezone_str = "America/New_York"
    
    try:
        tz = zoneinfo.ZoneInfo(timezone_str)
    except Exception:
        logging.warning(f"Timezone '{timezone_str}' not found. Falling back to UTC.")
        tz = zoneinfo.ZoneInfo("UTC")

    anchor = rules.get("anchor_date", rules.get("start_anchor", "today"))
    return datetime.now(tz) if anchor == "today" else datetime.now(tz)

def _format_date(final_date, rules):
    fmt = rules.get("format", "YYYY-MM-DD")
    
    if fmt == "epoch":
        if not rules.get("include_timestamp", True):
            final_date = final_date.replace(hour=0, minute=0, second=0, microsecond=0)
        return int(final_date.timestamp())
    elif fmt == "epoch_ms":
        if not rules.get("include_timestamp", True):
            final_date = final_date.replace(hour=0, minute=0, second=0, microsecond=0)
        return int(final_date.timestamp() * 1000)
    
    fmt = fmt.replace("YYYY", "%Y").replace("MM", "%m").replace("DD", "%d")
    date_str = final_date.strftime(fmt)
    
    if rules.get("include_timestamp"):
        t_fmt = rules.get("timestamp_format", "HH:mm:ss").replace("HH", "%H").replace("mm", "%M").replace("ss", "%S")
        if "T00" in t_fmt or t_fmt.startswith("T"):
            date_str += t_fmt
        else:
            date_str += " " + final_date.strftime(t_fmt)
    return date_str

def generate_dynamic_value(var_def, current_store=None, dataframes=None):
    """
    Generates a dynamic value based on the specified type and generation rules.
    
    Supports distributions (uniform/normal), string formatting (uuid, alphanumeric), 
    faker injection (emails, names), date math, conditionals, and foreign keys.
    
    Args:
        var_def (dict): A dictionary describing the dynamic variable definition.
        current_store (dict): Optional reference to the state store for conditional reads.
        dataframes (dict): Optional reference to generated dataframes (for foreign keys).
        
    Returns:
        any: The dynamically generated value (int, float, str, list, dict, date).
    """
    try:
        v_type = var_def.get("type")
        rules = var_def.get("generation_rules", {})
        
        if v_type == "int":
            if rules.get("distribution") == "normal":
                mean = rules.get("mean", 50)
                std = rules.get("std_dev", 15)
                val = int(round(random.gauss(mean, std)))
            else:
                val = random.randint(rules.get("min", 0), rules.get("max", 100))
            
            # Apply clamping if min/max are provided
            min_val = rules.get("min", float('-inf'))
            max_val = rules.get("max", float('inf'))
            return max(min_val, min(max_val, val))
            
        elif v_type == "float":
            if rules.get("distribution") == "normal":
                mean = rules.get("mean", 0.5)
                std = rules.get("std_dev", 0.15)
                val = random.gauss(mean, std)
            else:
                val = random.uniform(rules.get("min", 0.0), rules.get("max", 1.0))
            
            # Apply clamping if min/max are provided
            min_val = rules.get("min", float('-inf'))
            max_val = rules.get("max", float('inf'))
            val = max(min_val, min(max_val, val))
            
            return round(val, rules.get("decimal_places", 2))
        elif v_type == "string":
            fmt = rules.get("format")
            source = rules.get("source")
            if fmt == "uuid":
                return str(uuid.uuid4())
            elif source == "integer":
                return str(random.randint(rules.get("min", 0), rules.get("max", 100)))
            elif source == "random_string":
                min_l = rules.get("min_length", 5)
                max_l = rules.get("max_length", 10)
                length = random.randint(min_l, max_l)
                chars = ""
                if rules.get("include_mixed_case"):
                    chars += string.ascii_letters
                if rules.get("include_alphanumeric"):
                    chars += string.digits
                if rules.get("include_special_characters"):
                    chars += "".join(rules.get("special_characters", ["!"]))
                if not chars:
                    chars = string.ascii_lowercase
                return "".join(random.choice(chars) for _ in range(length))
            return "placeholder"
        elif v_type == "choice":
            options = rules.get("options", [])
            weights = rules.get("weights") # None implies uniform distribution
            if not options:
                return None
            return random.choices(options, weights=weights, k=1)[0]
        elif v_type == "conditional":
            conditions = rules.get("conditions", [])
            for cond in conditions:
                if "expression" in cond:
                    expr_str = cond["expression"]
                    
                    def replacer(match):
                        var_name = match.group(1).strip()
                        if current_store is not None and var_name in current_store:
                            return str(current_store[var_name])
                        return match.group(0)
                        
                    resolved_str = re.sub(r'\{\{(.*?)\}\}', replacer, expr_str)
                    
                    try:
                        if _parse_expression(resolved_str):
                            return cond.get("result")
                    except Exception as e:
                        logging.debug(f"Expression evaluation failed for '{resolved_str}': {e}")
                else:
                    # Legacy support for single-source conditions
                    source_name = rules.get("source")
                    if current_store is None or source_name not in current_store:
                        continue
                        
                    src_val = current_store[source_name]
                    op = cond.get("operator", "==")
                    cmp_val = cond.get("value")
                    result = cond.get("result")
                    
                    try:
                        if isinstance(src_val, int): cmp_val = int(cmp_val)
                        elif isinstance(src_val, float): cmp_val = float(cmp_val)
                    except Exception:
                        pass
                    
                    matched = False
                    try:
                        if op == "==": matched = (src_val == cmp_val)
                        elif op == "!=": matched = (src_val != cmp_val)
                        elif op == "<": matched = (src_val < cmp_val)
                        elif op == "<=": matched = (src_val <= cmp_val)
                        elif op == ">": matched = (src_val > cmp_val)
                        elif op == ">=": matched = (src_val >= cmp_val)
                    except TypeError:
                        pass 
                        
                    if matched:
                        return result
            
            return rules.get("default")
        elif v_type == "foreign_key":
            df_name = rules.get("dataframe")
            col_name = rules.get("column")
            
            if dataframes is not None and df_name in dataframes:
                df = dataframes[df_name]
                if col_name in df.columns and not df.empty:
                    # Randomly sample one value
                    return df[col_name].sample(1).iloc[0]
            
            return rules.get("default", "fk_not_found")
        elif v_type == "template":
            template_str = rules.get("template", "")
            
            def replacer(match):
                var_name = match.group(1).strip()
                if current_store is not None and var_name in current_store:
                    return str(current_store[var_name])
                return match.group(0) # Leave placeholder intact if not found
                
            return re.sub(r'\{\{(.*?)\}\}', replacer, template_str)
        elif v_type == "list":
            item_type = rules.get("item_type", "string")
            length = rules.get("count", rules.get("list_length", 1))
            if item_type == "boolean":
                return [random.choice([True, False]) for _ in range(length)]
            return [f"item_{i}" for i in range(length)]
        elif v_type == "dict":
            keys = rules.get("keys", [])
            return {k: "val" for k in keys}
        elif v_type == "date":
            base_date = _get_tz_aware_base_date(rules)
            d_offset = parse_date_offset(rules.get("date_offset", "0 days"))
            t_offset = parse_date_offset(rules.get("time_offset", "0 minutes"))
            final_date = base_date + d_offset + t_offset
            return _format_date(final_date, rules)
        elif v_type == "date_range":
            base_date = _get_tz_aware_base_date(rules)
            start_d_offset = parse_date_offset(rules.get("start_offset", "0 days"))
            end_d_offset = parse_date_offset(rules.get("end_offset", "+5 days"))
            
            start_date = base_date + start_d_offset
            end_date = base_date + end_d_offset
            
            step = parse_date_offset(rules.get("step", "1 days"))
            if step.total_seconds() <= 0:
                step = timedelta(days=1)
            
            skip_weekends = rules.get("skip_weekends", False)
                
            dates = []
            curr_date = start_date
            while curr_date <= end_date:
                if skip_weekends and curr_date.weekday() >= 5:
                    curr_date += step
                    continue
                dates.append(_format_date(curr_date, rules))
                curr_date += step
                
            return dates
        else:
            logging.warning(f"Unsupported dynamic variable type: {v_type}")
            return None
    except Exception as e:
        logging.error(f"Error generating dynamic value for {var_def.get('name', 'unknown')}: {e}")
        return None

def apply_transformation(val, actions):
    """
    Applies a sequence of string/math transformations to a value sequentially.
    
    Args:
        val (any): The initial source value.
        actions (list): List of transformation action dictionaries (e.g., truncate, pad).
        
    Returns:
        any: The transformed value.
    """
    if not isinstance(actions, list):
        return val
        
    for action_def in actions:
        try:
            action = action_def.get("action")
            if action == "cast_to_string":
                val = str(val)
            elif action == "pad_left":
                char = action_def.get("pad_character", " ")
                length = action_def.get("target_length", len(str(val)))
                val = str(val).rjust(length, char)
            elif action == "prepend":
                val = action_def.get("value", "") + str(val)
            elif action == "append":
                val = str(val) + action_def.get("value", "")
            elif action == "lowercase":
                val = str(val).lower()
            elif action == "replace":
                tgt = action_def.get("target", "")
                repl = action_def.get("replacement", "")
                if action_def.get("use_regex"):
                    val = re.sub(tgt, repl, str(val))
                else:
                    val = str(val).replace(tgt, repl)
            elif action == "truncate":
                max_len = action_def.get("max_length", len(str(val)))
                val = str(val)[:max_len]
            else:
                logging.warning(f"Unknown transformation action: {action}")
        except Exception as e:
            logging.warning(f"Failed to apply action {action_def} on value {val}: {e}")
    return val

def resolve_ref(ref_name, store):
    if ref_name in store:
        return store[ref_name]
    logging.warning(f"Reference '{ref_name}' not found in store.")
    return None

def build_composite(comp_def, config, base_store, exclude_composite_names=None):
    """
    Recursively builds a composite schema (dict or list), actively resolving 
    references using a fresh, row-specific state store to ensure dynamic regeneration.
    
    Args:
        comp_def (dict): The composite schema definition.
        config (dict): The full variable generation JSON configuration.
        base_store (dict): The current global state store.
        exclude_composite_names (set): A tracking set to prevent infinite recursion.
        
    Returns:
        dict|list|None: The fully resolved nested schema payload.
    """
    if exclude_composite_names is None:
        exclude_composite_names = set()
        
    def resolve_schema_node(node, current_store):
        if isinstance(node, dict):
            if "ref" in node:
                return resolve_ref(node["ref"], current_store)
            else:
                return {k: resolve_schema_node(v, current_store) for k, v in node.items()}
        elif isinstance(node, list):
            return [resolve_schema_node(v, current_store) for v in node]
        else:
            return node

    try:
        comp_type = comp_def.get("type", "dict")
        schema = comp_def.get("schema", {})
        if comp_type == "dict":
            return resolve_schema_node(schema, base_store)
        elif comp_type == "list":
            length = comp_def.get("count", comp_def.get("list_length", 1))
            res = []
            for _ in range(length):
                item_store = generate_row_store(config, base_store, exclude_composite_names)
                res.append(resolve_schema_node(schema, item_store))
            return res
        return None
    except Exception as e:
        logging.error(f"Failed to build composite variable {comp_def.get('name', 'unknown')}: {e}")
        return None

def generate_row_store(config, base_store, exclude_composite_names=None, dataframes=None):
    """
    Creates an isolated row-level state store by cloning the base store and actively 
    regenerating all dynamic variables and transformations. Used heavily when looping 
    through dataframe rows or composite list items to ensure unique data.
    
    Args:
        config (dict): The full config.
        base_store (dict): The parent state store.
        exclude_composite_names (set): Recursion lock set.
        dataframes (dict): DataFrames context for foreign key sampling.
        
    Returns:
        dict: The refreshed isolated row store.
    """
    if exclude_composite_names is None:
        exclude_composite_names = set()
    
    row_store = base_store.copy()
    
    # 1. Regenerate scalars in dynamic variables
    for d_var in config.get("dynamic_variables", []):
        if d_var.get("type") not in ["list", "date_range"]:
            try:
                row_store[d_var["name"]] = generate_dynamic_value(d_var, row_store, dataframes)
            except Exception:
                pass
                
    # 2. Re-apply transformations
    for t_def in config.get("transformations", []):
        src = t_def.get("ref", t_def.get("source"))
        if src in row_store:
            try:
                row_store[t_def["name"]] = apply_transformation(row_store[src], t_def.get("actions", []))
            except Exception:
                pass
                
    # 3. Re-build scalar composites
    for comp_def in config.get("composite_variables", []):
        name = comp_def.get("name")
        if comp_def.get("count", comp_def.get("num_rows", 1)) == 1 and name not in exclude_composite_names:
            try:
                new_excludes = exclude_composite_names | {name}
                row_store[name] = build_composite(comp_def, config, row_store, new_excludes)
            except Exception:
                pass
                
    return row_store

def generate(config_path="fauxreal_config.json", overrides=None, seed=None, targets=None):
    """
    The core pipeline orchestrator. Reads the configuration file and sequentially 
    executes Phase 1-5 (Fixed, Dynamic, Transformations, Composites, DataFrames).
    
    Args:
        config_path (str): Filepath to the JSON config.
        overrides (dict): Optional dictionary of runtime overrides for fixed variables.
        seed (int): Optional global seed for deterministic generation.
        targets (list): Optional list of variable names (strings) to return exclusively.
        
    Returns:
        tuple|dict: If targets is None, returns the legacy tuple (fixed, dynamic (includes faker), transformed, composites, dataframes).
                    If targets is provided, returns a single dictionary of {target_name: generated_value}.
    """
    config = load_config(config_path)
    if not config:
        logging.error("Configuration is empty or invalid. Exiting.")
        return {}, {}, {}, {}, {}

    if seed is None:
        seed = config.get("seed")
    if seed is not None:
        try:
            random.seed(int(seed))
            if FAKER_AVAILABLE:
                Faker.seed(int(seed))
            logging.info(f"Random seed set to: {seed}")
        except Exception as e:
            logging.warning(f"Failed to set seed: {e}")
            
    store = {}
    
    fixed_vars = {}
    faker_vars = {}
    dynamic_vars = {}
    transformed_vars = {}
    composites = {}
    dataframes = {}

    # 1. Fixed Variables
    for f_var in config.get("fixed_variables", []):
        store[f_var["name"]] = f_var["value"]
        fixed_vars[f_var["name"]] = f_var["value"]
        
    # Inject CLI Overrides
    if overrides:
        for k, v in overrides.items():
            store[k] = v
            fixed_vars[k] = v
    store.update(fixed_vars)
    logging.info(f"Fixed variables loaded: {list(fixed_vars.keys())}")
    
    # 2. Faker Variables
    for fk_var in config.get("faker_variables", []):
        name = fk_var.get("name")
        provider = fk_var.get("provider", "name")
        kwargs = fk_var.get("kwargs", {})
        
        if not FAKER_AVAILABLE:
            logging.warning(f"Faker library is not installed. Returning placeholder for '{name}'.")
            val = "faker_missing_placeholder"
        else:
            try:
                faker_func = getattr(fake, provider)
                val = faker_func(**kwargs)
            except AttributeError:
                logging.warning(f"Faker provider '{provider}' not found.")
                val = "unknown_faker_value"
                
        store[name] = val
        faker_vars[name] = val
    if faker_vars:
        logging.info(f"Faker variables generated: {list(faker_vars.keys())}")
    
    # 3. Dynamic Variables
    for d_var in config.get("dynamic_variables", []):
        try:
            val = generate_dynamic_value(d_var, store)
            store[d_var["name"]] = val
            dynamic_vars[d_var["name"]] = val
        except Exception as e:
            logging.error(f"Unexpected error creating dynamic variable {d_var.get('name')}: {e}")
    logging.info(f"Dynamic variables generated: {list(dynamic_vars.keys())}")
    
    # 3. Transformations
    for t_def in config.get("transformations", []):
        try:
            src_name = t_def.get("ref", t_def.get("source"))
            if src_name in store:
                val = apply_transformation(store[src_name], t_def.get("actions", []))
                store[t_def["name"]] = val
                transformed_vars[t_def["name"]] = val
            else:
                logging.warning(f"Transformation source '{src_name}' not found in store.")
        except Exception as e:
            logging.error(f"Unexpected error running transformation {t_def.get('name')}: {e}")
    logging.info(f"Transformations applied: {list(transformed_vars.keys())}")
    
    # 4. Composite Variables
    for comp_def in config.get("composite_variables", []):
        try:
            name = comp_def.get("name")
            num_rows = comp_def.get("count", comp_def.get("num_rows", 1))
            if num_rows > 1:
                val = []
                for _ in range(num_rows):
                    row_store = generate_row_store(config, store)
                    val.append(build_composite(comp_def, config, row_store))
            else:
                row_store = generate_row_store(config, store)
                val = build_composite(comp_def, config, row_store)
            
            # Immediately add to store so subsequent composites can reference it
            store[name] = val
            composites[name] = val
        except Exception as e:
            logging.error(f"Unexpected error building composite {comp_def.get('name')}: {e}")
    logging.info(f"Composite variables generated: {list(composites.keys())}")
    
    # 5. DataFrames
    dataframes = {}
    for df_def in config.get("dataframes", []):
        try:
            name = df_def.get("name")
            num_rows = df_def.get("count", df_def.get("num_rows", 10))
            columns = df_def.get("columns", [])
            unique_combinations = df_def.get("unique_combinations", [])
            
            data = []
            
            if unique_combinations:
                # 1. Fetch the lists for unique combinations
                combination_lists = []
                combination_col_names = []
                for col in columns:
                    if col["name"] in unique_combinations:
                        val = resolve_ref(col["ref"], store)
                        if not isinstance(val, list):
                            logging.warning(f"Column '{col['name']}' in unique_combinations must reference a list. Wrapping in list.")
                            val = [val]
                        combination_lists.append(val)
                        combination_col_names.append(col["name"])
                
                # 2. Compute Cartesian Product
                if combination_lists:
                    cartesian_product = list(itertools.product(*combination_lists))
                    for comb in cartesian_product:
                        row_store = generate_row_store(config, store)
                        row = {}
                        # Fill the combinations
                        for idx, col_name in enumerate(combination_col_names):
                            row[col_name] = comb[idx]
                        
                        # Fill the rest with standard ref resolutions
                        for col in columns:
                            if col["name"] not in unique_combinations:
                                row[col["name"]] = resolve_ref(col["ref"], row_store)
                        data.append(row)
                else:
                    logging.warning("No valid lists found for unique_combinations. Falling back to num_rows.")
                    for _ in range(num_rows):
                        row_store = generate_row_store(config, store, dataframes=dataframes)
                        row = {col["name"]: resolve_ref(col["ref"], row_store) for col in columns}
                        data.append(row)
            else:
                # Standard random generation
                for _ in range(num_rows):
                    row_store = generate_row_store(config, store, dataframes=dataframes)
                    row = {col["name"]: resolve_ref(col["ref"], row_store) for col in columns}
                    data.append(row)
                
            dataframes[name] = pd.DataFrame(data)
            logging.info(f"DataFrame '{name}' created with shape {dataframes[name].shape}")
        except Exception as e:
            logging.error(f"Unexpected error creating DataFrame {df_def.get('name')}: {e}")
    # 6. Exports
    for exp_def in config.get("exports", []):
        try:
            exp_type = exp_def.get("type", "csv")
            source = exp_def.get("ref", exp_def.get("source"))
            filepath = exp_def.get("filepath", "output.csv")
            
            if not filepath or not source:
                logging.warning(f"Export definition missing 'filepath' or 'source': {exp_def}")
                continue
                
            if exp_type == "csv":
                if source in dataframes:
                    dataframes[source].to_csv(filepath, index=False)
                    logging.info(f"Exported DataFrame '{source}' to {filepath}")
                else:
                    logging.warning(f"Export source DataFrame '{source}' not found.")
            elif exp_type == "parquet":
                if source in dataframes:
                    try:
                        dataframes[source].to_parquet(filepath, index=False)
                        logging.info(f"Exported DataFrame '{source}' to {filepath}")
                    except ImportError:
                        logging.error(f"Missing dependency for parquet export. Please run: pip install pyarrow fastparquet")
                else:
                    logging.warning(f"Export source DataFrame '{source}' not found.")
            elif exp_type == "json":
                if source in store:
                    with open(filepath, 'w') as f:
                        json.dump(store[source], f, indent=exp_def.get("indent", 4))
                    logging.info(f"Exported JSON '{source}' to {filepath}")
                else:
                    logging.warning(f"Export source '{source}' not found in store.")
            else:
                logging.warning(f"Unsupported export type: {exp_type}")
        except Exception as e:
            logging.error(f"Failed to export {exp_def.get('ref', exp_def.get('source', 'unknown'))}: {e}")
    if targets is not None:
        return {target: store.get(target) for target in targets}

    # Merge faker_vars into dynamic_vars for backward compatibility in the 5-tuple
    merged_dynamic = {**faker_vars, **dynamic_vars}
    return fixed_vars, merged_dynamic, transformed_vars, composites, dataframes
