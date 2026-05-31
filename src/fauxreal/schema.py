from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union, Literal

class FixedVariable(BaseModel):
    name: str = Field(..., description="The name of the variable to store")
    type: Literal["string", "int", "float", "boolean", "list", "dict", "date"] = Field(..., description="The data type")
    value: Any = Field(..., description="The static value to assign")

class FakerVariable(BaseModel):
    name: str = Field(..., description="The name of the variable to store")
    provider: str = Field(..., description="The Faker provider method name (e.g. email, name, pyint)")
    kwargs: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Optional keyword arguments passed to the Faker provider")

class DynamicVariable(BaseModel):
    name: str = Field(..., description="The name of the variable to store")
    type: Literal["int", "float", "string", "list", "dict", "date", "date_range", "choice", "conditional", "foreign_key", "template"] = Field(..., description="The dynamic type")
    generation_rules: Dict[str, Any] = Field(default_factory=dict, description="Rules governing the generation of this variable")

class TransformationAction(BaseModel):
    action: Literal["pad", "truncate", "replace", "cast_to_string"] = Field(..., description="The transformation action to perform")
    length: Optional[int] = None
    pad_char: Optional[str] = None
    direction: Optional[str] = None
    old: Optional[str] = None
    new: Optional[str] = None
    format: Optional[str] = None
    
    model_config = {"extra": "allow"}

class Transformation(BaseModel):
    name: str = Field(..., description="The name to save the transformed variable as")
    ref: Optional[str] = Field(None, description="The variable to transform (alias for source)")
    source: Optional[str] = Field(None, description="The variable to transform")
    actions: List[TransformationAction] = Field(..., description="List of actions to apply sequentially")

class CompositeVariable(BaseModel):
    name: str = Field(..., description="The name of the composite variable to store")
    type: Literal["dict", "list"] = Field(..., description="The structure type")
    count: Optional[int] = Field(None, description="Number of items to generate if type is list")
    schema_def: Optional[Union[Dict[str, Any], str]] = Field(None, alias="schema", description="The structure containing variable references")

class DataFrameColumn(BaseModel):
    name: str = Field(..., description="The resulting column name in the DataFrame")
    ref: str = Field(..., description="The generated variable name to sample from")

class DataFrameDefinition(BaseModel):
    name: str = Field(..., description="The name of the DataFrame to store")
    count: Optional[int] = Field(None, description="Number of rows to generate (alias for num_rows)")
    num_rows: Optional[int] = Field(None, description="Number of rows to generate")
    columns: List[DataFrameColumn] = Field(default_factory=list, description="List of columns mapping to generated variables")
    unique_combinations: Optional[List[str]] = Field(None, description="Cross-join combinations of fixed variables to seed the DataFrame")

class ExportDefinition(BaseModel):
    type: Literal["csv", "parquet", "json"] = Field("csv", description="The export format")
    ref: Optional[str] = Field(None, description="The variable/DataFrame name to export (alias for source)")
    source: Optional[str] = Field(None, description="The variable/DataFrame name to export")
    filepath: str = Field(..., description="The destination file path")
    indent: Optional[int] = Field(4, description="JSON indentation level")

class VariableGenerationConfig(BaseModel):
    description: Optional[str] = Field(None, description="Optional description of the configuration")
    seed: Optional[int] = Field(None, description="Random seed for reproducibility")
    fixed_variables: Optional[List[FixedVariable]] = Field(default_factory=list)
    faker_variables: Optional[List[FakerVariable]] = Field(default_factory=list)
    dynamic_variables: Optional[List[DynamicVariable]] = Field(default_factory=list)
    transformations: Optional[List[Transformation]] = Field(default_factory=list)
    composite_variables: Optional[List[CompositeVariable]] = Field(default_factory=list)
    dataframes: Optional[List[DataFrameDefinition]] = Field(default_factory=list)
    exports: Optional[List[ExportDefinition]] = Field(default_factory=list)

class FauxrealConfig(BaseModel):
    fauxreal_config: VariableGenerationConfig = Field(..., description="The root configuration block")
