"""
FastAPI 0.121.x OpenAPI schema 生成兼容性补丁

修复 _remap_definitions_and_field_mappings 中 KeyError: '$ref' 的问题。
当可选请求体参数（Body/Form 参数带有默认值）生成 JSON Schema 时，
Pydantic v2 会产生 {"allOf": [{"$ref": "..."}], "default": None} 格式，
而 FastAPI 0.121.x 的实现假定 schema 顶层直接有 "$ref" 键，导致崩溃。

此补丁在读取 $ref 时兼容 allOf 包裹格式。
升级 FastAPI 到修复此问题的版本后可移除本补丁。
"""
import fastapi._compat.v2 as _v2

_original_remap = _v2._remap_definitions_and_field_mappings


def _extract_ref(schema: dict) -> str | None:
    """从 schema 中提取 $ref，兼容直接引用和 allOf 包裹两种格式"""
    if "$ref" in schema:
        return schema["$ref"]
    if "allOf" in schema:
        for item in schema["allOf"]:
            if isinstance(item, dict) and "$ref" in item:
                return item["$ref"]
    return None


def _patched_remap(*, model_name_map, definitions, field_mapping):
    old_name_to_new_name_map = {}
    for field_key, schema in field_mapping.items():
        model = field_key[0].type_
        if model not in model_name_map:
            continue
        new_name = model_name_map[model]
        ref = _extract_ref(schema)
        if ref is None:
            continue
        old_name = ref.split("/")[-1]
        if old_name in {f"{new_name}-Input", f"{new_name}-Output"}:
            continue
        old_name_to_new_name_map[old_name] = new_name

    new_field_mapping = {}
    for field_key, schema in field_mapping.items():
        new_schema = _v2._replace_refs(
            schema=schema, old_name_to_new_name_map=old_name_to_new_name_map
        )
        new_field_mapping[field_key] = new_schema

    new_definitions = {}
    for key, value in definitions.items():
        new_key = old_name_to_new_name_map.get(key, key)
        new_value = _v2._replace_refs(
            schema=value, old_name_to_new_name_map=old_name_to_new_name_map
        )
        new_definitions[new_key] = new_value

    return new_field_mapping, new_definitions


_v2._remap_definitions_and_field_mappings = _patched_remap
