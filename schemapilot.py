#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SchemaPilot - Lightweight JSON Schema Intelligent Validation & Testing Engine
轻量级JSON Schema智能验证与测试引擎

A zero-dependency CLI tool for JSON Schema validation, API response testing,
and batch data quality verification.

Author: SchemaPilot Team
License: MIT
Version: 1.0.0
"""

import json
import re
import sys
import os
import argparse
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional, Union, Tuple
from enum import Enum
from datetime import datetime

__version__ = "1.0.0"
__author__ = "SchemaPilot Team"


class ValidationError:
    """Validation error details"""
    def __init__(self, path: str, message: str, error_type: str = "error"):
        self.path = path
        self.message = message
        self.error_type = error_type

    def to_dict(self) -> Dict[str, str]:
        return {
            "path": self.path,
            "message": self.message,
            "type": self.error_type
        }

    def __str__(self) -> str:
        return f"[{self.error_type.upper()}] {self.path}: {self.message}"


class ValidationResult:
    """Validation result container"""
    def __init__(self, is_valid: bool = True):
        self.is_valid = is_valid
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationError] = []
        self.stats = {
            "total_checks": 0,
            "passed": 0,
            "failed": 0,
            "warnings": 0
        }

    def add_error(self, path: str, message: str):
        self.errors.append(ValidationError(path, message, "error"))
        self.stats["failed"] += 1
        self.is_valid = False

    def add_warning(self, path: str, message: str):
        self.warnings.append(ValidationError(path, message, "warning"))
        self.stats["warnings"] += 1

    def increment_check(self, passed: bool = True):
        self.stats["total_checks"] += 1
        if passed:
            self.stats["passed"] += 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "valid": self.is_valid,
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [w.to_dict() for w in self.warnings],
            "stats": self.stats
        }


class SchemaGenerator:
    """Generate JSON Schema from sample data"""

    @staticmethod
    def infer_type(value: Any) -> str:
        """Infer JSON Schema type from value"""
        if value is None:
            return "null"
        elif isinstance(value, bool):
            return "boolean"
        elif isinstance(value, int):
            return "integer"
        elif isinstance(value, float):
            return "number"
        elif isinstance(value, str):
            return "string"
        elif isinstance(value, list):
            return "array"
        elif isinstance(value, dict):
            return "object"
        return "string"

    @staticmethod
    def generate(data: Any, title: str = "Generated Schema") -> Dict[str, Any]:
        """Generate JSON Schema from data"""
        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": title,
            "type": SchemaGenerator.infer_type(data)
        }

        if isinstance(data, dict):
            schema["properties"] = {}
            required = []
            for key, value in data.items():
                schema["properties"][key] = SchemaGenerator._generate_for_value(value)
                if value is not None:
                    required.append(key)
            if required:
                schema["required"] = required

        elif isinstance(data, list):
            if data:
                # Infer items schema from first element
                schema["items"] = SchemaGenerator._generate_for_value(data[0])
            else:
                schema["items"] = {"type": "string"}

        return schema

    @staticmethod
    def _generate_for_value(value: Any) -> Dict[str, Any]:
        """Generate schema for a single value"""
        value_type = SchemaGenerator.infer_type(value)
        result = {"type": value_type}

        if value_type == "string" and isinstance(value, str):
            # Detect common patterns
            if re.match(r'^\d{4}-\d{2}-\d{2}$', value):
                result["format"] = "date"
            elif re.match(r'^\d{4}-\d{2}-\d{2}T', value):
                result["format"] = "date-time"
            elif re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', value):
                result["format"] = "email"
            elif re.match(r'^https?://', value):
                result["format"] = "uri"
            if len(value) > 0:
                result["minLength"] = 1

        elif value_type == "integer" and isinstance(value, int):
            result["minimum"] = value if value < 0 else 0

        elif value_type == "number" and isinstance(value, float):
            result["minimum"] = value if value < 0 else 0

        elif value_type == "array" and isinstance(value, list):
            if value:
                result["items"] = SchemaGenerator._generate_for_value(value[0])
            else:
                result["items"] = {"type": "string"}

        elif value_type == "object" and isinstance(value, dict):
            result["properties"] = {}
            required = []
            for k, v in value.items():
                result["properties"][k] = SchemaGenerator._generate_for_value(v)
                if v is not None:
                    required.append(k)
            if required:
                result["required"] = required

        return result


class SchemaValidator:
    """JSON Schema validator (draft-07 compatible)"""

    def __init__(self):
        self.type_validators = {
            "string": self._validate_string,
            "integer": self._validate_integer,
            "number": self._validate_number,
            "boolean": self._validate_boolean,
            "array": self._validate_array,
            "object": self._validate_object,
            "null": self._validate_null
        }

    def validate(self, data: Any, schema: Dict[str, Any], path: str = "$") -> ValidationResult:
        """Validate data against schema"""
        result = ValidationResult()
        self._validate_value(data, schema, path, result)
        return result

    def _validate_value(self, data: Any, schema: Dict[str, Any], path: str, result: ValidationResult):
        """Validate a value against schema"""
        result.increment_check()

        # Handle type validation
        if "type" in schema:
            expected_type = schema["type"]
            if isinstance(expected_type, list):
                type_matched = any(self._check_type(data, t) for t in expected_type)
                if not type_matched:
                    result.add_error(path, f"Expected one of types {expected_type}, got {type(data).__name__}")
                    return
            else:
                if not self._check_type(data, expected_type):
                    result.add_error(path, f"Expected type '{expected_type}', got {type(data).__name__}")
                    return

            # Run type-specific validation
            if not isinstance(expected_type, list) and expected_type in self.type_validators:
                self.type_validators[expected_type](data, schema, path, result)

        # Validate enum
        if "enum" in schema:
            if data not in schema["enum"]:
                result.add_error(path, f"Value must be one of: {schema['enum']}")

        # Validate const
        if "const" in schema:
            if data != schema["const"]:
                result.add_error(path, f"Value must be: {schema['const']}")

        # Validate allOf
        if "allOf" in schema:
            for i, subschema in enumerate(schema["allOf"]):
                self._validate_value(data, subschema, f"{path}.allOf[{i}]", result)

        # Validate anyOf
        if "anyOf" in schema:
            any_valid = False
            for subschema in schema["anyOf"]:
                sub_result = ValidationResult()
                self._validate_value(data, subschema, path, sub_result)
                if sub_result.is_valid:
                    any_valid = True
                    break
            if not any_valid:
                result.add_error(path, "Value does not match any of the anyOf schemas")

        # Validate oneOf
        if "oneOf" in schema:
            valid_count = 0
            for subschema in schema["oneOf"]:
                sub_result = ValidationResult()
                self._validate_value(data, subschema, path, sub_result)
                if sub_result.is_valid:
                    valid_count += 1
            if valid_count != 1:
                result.add_error(path, f"Value must match exactly one schema, matched {valid_count}")

        # Validate not
        if "not" in schema:
            sub_result = ValidationResult()
            self._validate_value(data, schema["not"], path, sub_result)
            if sub_result.is_valid:
                result.add_error(path, "Value should not match the 'not' schema")

    def _check_type(self, data: Any, expected: str) -> bool:
        """Check if data matches expected type"""
        type_map = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict,
            "null": type(None)
        }
        expected_class = type_map.get(expected)
        if expected_class is None:
            return True
        if isinstance(expected_class, tuple):
            return isinstance(data, expected_class) and not isinstance(data, bool)
        return isinstance(data, expected_class) and (expected != "integer" or not isinstance(data, bool))

    def _validate_string(self, data: str, schema: Dict[str, Any], path: str, result: ValidationResult):
        """Validate string constraints"""
        if not isinstance(data, str):
            return

        # minLength
        if "minLength" in schema:
            if len(data) < schema["minLength"]:
                result.add_error(path, f"String length {len(data)} is less than minimum {schema['minLength']}")

        # maxLength
        if "maxLength" in schema:
            if len(data) > schema["maxLength"]:
                result.add_error(path, f"String length {len(data)} exceeds maximum {schema['maxLength']}")

        # pattern
        if "pattern" in schema:
            pattern = schema["pattern"]
            if not re.search(pattern, data):
                result.add_error(path, f"String does not match pattern: {pattern}")

        # format (basic support)
        if "format" in schema:
            fmt = schema["format"]
            format_patterns = {
                "email": r'^[^@\s]+@[^@\s]+\.[^@\s]+$',
                "uri": r'^https?://',
                "date": r'^\d{4}-\d{2}-\d{2}$',
                "date-time": r'^\d{4}-\d{2}-\d{2}T'
            }
            if fmt in format_patterns:
                if not re.match(format_patterns[fmt], data):
                    result.add_warning(path, f"String may not match format '{fmt}'")

    def _validate_integer(self, data: int, schema: Dict[str, Any], path: str, result: ValidationResult):
        """Validate integer constraints"""
        if not isinstance(data, int) or isinstance(data, bool):
            return

        self._validate_number(data, schema, path, result)

        # multipleOf
        if "multipleOf" in schema:
            if data % schema["multipleOf"] != 0:
                result.add_error(path, f"Value {data} is not a multiple of {schema['multipleOf']}")

    def _validate_number(self, data: Union[int, float], schema: Dict[str, Any], path: str, result: ValidationResult):
        """Validate number constraints"""
        if not isinstance(data, (int, float)) or isinstance(data, bool):
            return

        # minimum
        if "minimum" in schema:
            if data < schema["minimum"]:
                result.add_error(path, f"Value {data} is less than minimum {schema['minimum']}")

        # maximum
        if "maximum" in schema:
            if data > schema["maximum"]:
                result.add_error(path, f"Value {data} exceeds maximum {schema['maximum']}")

        # exclusiveMinimum
        if "exclusiveMinimum" in schema:
            if data <= schema["exclusiveMinimum"]:
                result.add_error(path, f"Value {data} must be greater than {schema['exclusiveMinimum']}")

        # exclusiveMaximum
        if "exclusiveMaximum" in schema:
            if data >= schema["exclusiveMaximum"]:
                result.add_error(path, f"Value {data} must be less than {schema['exclusiveMaximum']}")

    def _validate_boolean(self, data: bool, schema: Dict[str, Any], path: str, result: ValidationResult):
        """Boolean has no additional constraints in draft-07"""
        pass

    def _validate_array(self, data: list, schema: Dict[str, Any], path: str, result: ValidationResult):
        """Validate array constraints"""
        if not isinstance(data, list):
            return

        # minItems
        if "minItems" in schema:
            if len(data) < schema["minItems"]:
                result.add_error(path, f"Array has {len(data)} items, minimum is {schema['minItems']}")

        # maxItems
        if "maxItems" in schema:
            if len(data) > schema["maxItems"]:
                result.add_error(path, f"Array has {len(data)} items, maximum is {schema['maxItems']}")

        # uniqueItems
        if schema.get("uniqueItems", False):
            seen = []
            for item in data:
                item_str = json.dumps(item, sort_keys=True)
                if item_str in seen:
                    result.add_error(path, "Array contains duplicate items")
                    break
                seen.append(item_str)

        # items
        if "items" in schema:
            items_schema = schema["items"]
            for i, item in enumerate(data):
                self._validate_value(item, items_schema, f"{path}[{i}]", result)

        # contains (draft-06+)
        if "contains" in schema:
            contains_schema = schema["contains"]
            found = False
            for i, item in enumerate(data):
                sub_result = ValidationResult()
                self._validate_value(item, contains_schema, f"{path}[{i}]", sub_result)
                if sub_result.is_valid:
                    found = True
                    break
            if not found:
                result.add_error(path, "Array does not contain an item matching the 'contains' schema")

    def _validate_object(self, data: dict, schema: Dict[str, Any], path: str, result: ValidationResult):
        """Validate object constraints"""
        if not isinstance(data, dict):
            return

        # minProperties
        if "minProperties" in schema:
            if len(data) < schema["minProperties"]:
                result.add_error(path, f"Object has {len(data)} properties, minimum is {schema['minProperties']}")

        # maxProperties
        if "maxProperties" in schema:
            if len(data) > schema["maxProperties"]:
                result.add_error(path, f"Object has {len(data)} properties, maximum is {schema['maxProperties']}")

        # required
        if "required" in schema:
            for req in schema["required"]:
                if req not in data:
                    result.add_error(path, f"Missing required property: '{req}'")

        # properties
        if "properties" in schema:
            for prop, prop_schema in schema["properties"].items():
                if prop in data:
                    self._validate_value(data[prop], prop_schema, f"{path}.{prop}", result)

        # patternProperties
        if "patternProperties" in schema:
            for pattern, pat_schema in schema["patternProperties"].items():
                regex = re.compile(pattern)
                for prop, value in data.items():
                    if regex.match(prop):
                        self._validate_value(value, pat_schema, f"{path}.{prop}", result)

        # additionalProperties
        if "additionalProperties" in schema:
            add_props = schema["additionalProperties"]
            known_props = set(schema.get("properties", {}).keys())
            for pattern in schema.get("patternProperties", {}):
                regex = re.compile(pattern)
                known_props.update(p for p in data if regex.match(p))

            for prop in data:
                if prop not in known_props:
                    if add_props is False:
                        result.add_error(path, f"Additional property not allowed: '{prop}'")
                    elif isinstance(add_props, dict):
                        self._validate_value(data[prop], add_props, f"{path}.{prop}", result)

        # propertyNames (draft-06+)
        if "propertyNames" in schema:
            names_schema = schema["propertyNames"]
            for prop in data:
                self._validate_value(prop, names_schema, f"{path}(propertyName: {prop})", result)

    def _validate_null(self, data: Any, schema: Dict[str, Any], path: str, result: ValidationResult):
        """Null has no additional constraints"""
        pass


class APITester:
    """Test API endpoints and validate responses"""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.validator = SchemaValidator()

    def fetch(self, url: str, method: str = "GET", headers: Optional[Dict] = None,
              data: Optional[Any] = None) -> Tuple[int, Dict[str, Any], str]:
        """Fetch data from API endpoint"""
        req_headers = headers or {}
        req_headers.setdefault("User-Agent", f"SchemaPilot/{__version__}")
        req_headers.setdefault("Accept", "application/json")

        req_data = None
        if data is not None:
            req_data = json.dumps(data).encode('utf-8')
            req_headers.setdefault("Content-Type", "application/json")

        req = urllib.request.Request(
            url,
            data=req_data,
            headers=req_headers,
            method=method
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                body = response.read().decode('utf-8')
                status = response.status
                resp_headers = dict(response.headers)
                return status, resp_headers, body
        except urllib.error.HTTPError as e:
            body = e.read().decode('utf-8') if e.fp else ""
            return e.code, dict(e.headers), body
        except urllib.error.URLError as e:
            raise ConnectionError(f"Failed to connect: {e.reason}")

    def test_endpoint(self, url: str, schema: Optional[Dict] = None, method: str = "GET",
                     headers: Optional[Dict] = None, data: Optional[Any] = None) -> Dict[str, Any]:
        """Test API endpoint and optionally validate response against schema"""
        result = {
            "url": url,
            "method": method,
            "timestamp": datetime.now().isoformat(),
            "status": None,
            "headers": {},
            "response": None,
            "validation": None,
            "error": None
        }

        try:
            status, resp_headers, body = self.fetch(url, method, headers, data)
            result["status"] = status
            result["headers"] = resp_headers

            # Try to parse JSON response
            try:
                result["response"] = json.loads(body)
            except json.JSONDecodeError:
                result["response"] = body

            # Validate against schema if provided
            if schema and result["response"] is not None:
                if isinstance(result["response"], dict):
                    validation = self.validator.validate(result["response"], schema)
                    result["validation"] = validation.to_dict()
                else:
                    result["validation"] = {
                        "valid": False,
                        "errors": [{"path": "$", "message": "Response is not a JSON object", "type": "error"}],
                        "warnings": [],
                        "stats": {"total_checks": 1, "passed": 0, "failed": 1, "warnings": 0}
                    }

        except Exception as e:
            result["error"] = str(e)

        return result


class BatchValidator:
    """Batch validate multiple JSON files against schemas"""

    def __init__(self):
        self.validator = SchemaValidator()

    def validate_files(self, files: List[str], schema_path: str) -> Dict[str, Any]:
        """Validate multiple files against a schema"""
        results = {
            "schema": schema_path,
            "total_files": len(files),
            "passed": 0,
            "failed": 0,
            "results": []
        }

        # Load schema
        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = json.load(f)
        except Exception as e:
            results["error"] = f"Failed to load schema: {e}"
            return results

        for file_path in files:
            file_result = {
                "file": file_path,
                "valid": False,
                "errors": []
            }

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                validation = self.validator.validate(data, schema)
                file_result["valid"] = validation.is_valid
                file_result["errors"] = [e.to_dict() for e in validation.errors]

                if validation.is_valid:
                    results["passed"] += 1
                else:
                    results["failed"] += 1

            except json.JSONDecodeError as e:
                file_result["errors"].append({
                    "path": "$",
                    "message": f"Invalid JSON: {e}",
                    "type": "error"
                })
                results["failed"] += 1
            except Exception as e:
                file_result["errors"].append({
                    "path": "$",
                    "message": str(e),
                    "type": "error"
                })
                results["failed"] += 1

            results["results"].append(file_result)

        return results


class ReportGenerator:
    """Generate validation reports in various formats"""

    @staticmethod
    def generate_html(report_data: Dict[str, Any], title: str = "Validation Report") -> str:
        """Generate HTML report"""
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        .header h1 {{ font-size: 2.5em; margin-bottom: 10px; }}
        .header p {{ opacity: 0.9; font-size: 1.1em; }}
        .content {{ padding: 40px; }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: #f8f9fa;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            border-left: 4px solid #667eea;
        }}
        .stat-card.success {{ border-left-color: #28a745; }}
        .stat-card.error {{ border-left-color: #dc3545; }}
        .stat-card.warning {{ border-left-color: #ffc107; }}
        .stat-value {{ font-size: 2em; font-weight: bold; color: #333; }}
        .stat-label {{ color: #666; margin-top: 5px; }}
        .section {{ margin-bottom: 30px; }}
        .section h2 {{
            color: #333;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #eee;
        }}
        .error-list {{ list-style: none; }}
        .error-item {{
            background: #fff5f5;
            border-left: 4px solid #dc3545;
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 0 8px 8px 0;
        }}
        .error-item.warning {{
            background: #fffbeb;
            border-left-color: #ffc107;
        }}
        .error-path {{ font-weight: bold; color: #dc3545; }}
        .error-item.warning .error-path {{ color: #856404; }}
        .error-message {{ color: #666; margin-top: 5px; }}
        .success-message {{
            background: #d4edda;
            color: #155724;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            font-size: 1.2em;
        }}
        .timestamp {{
            text-align: center;
            color: #999;
            margin-top: 30px;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 {title}</h1>
            <p>Generated by SchemaPilot</p>
        </div>
        <div class="content">
"""

        # Add stats if available
        if "stats" in report_data:
            stats = report_data["stats"]
            html += f"""
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-value">{stats.get('total_checks', 0)}</div>
                    <div class="stat-label">Total Checks</div>
                </div>
                <div class="stat-card success">
                    <div class="stat-value">{stats.get('passed', 0)}</div>
                    <div class="stat-label">Passed</div>
                </div>
                <div class="stat-card error">
                    <div class="stat-value">{stats.get('failed', 0)}</div>
                    <div class="stat-label">Failed</div>
                </div>
                <div class="stat-card warning">
                    <div class="stat-value">{stats.get('warnings', 0)}</div>
                    <div class="stat-label">Warnings</div>
                </div>
            </div>
"""

        # Add validation status
        is_valid = report_data.get("valid", True)
        if is_valid and not report_data.get("errors"):
            html += '<div class="section"><div class="success-message">✅ All validations passed!</div></div>'
        else:
            # Add errors
            if report_data.get("errors"):
                html += '<div class="section"><h2>❌ Errors</h2><ul class="error-list">'
                for error in report_data["errors"]:
                    html += f'''
                    <li class="error-item">
                        <div class="error-path">{error.get("path", "$")}</div>
                        <div class="error-message">{error.get("message", "")}</div>
                    </li>'''
                html += '</ul></div>'

            # Add warnings
            if report_data.get("warnings"):
                html += '<div class="section"><h2>⚠️ Warnings</h2><ul class="error-list">'
                for warning in report_data["warnings"]:
                    html += f'''
                    <li class="error-item warning">
                        <div class="error-path">{warning.get("path", "$")}</div>
                        <div class="error-message">{warning.get("message", "")}</div>
                    </li>'''
                html += '</ul></div>'

        html += f'''
            <div class="timestamp">
                Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            </div>
        </div>
    </div>
</body>
</html>'''

        return html

    @staticmethod
    def generate_markdown(report_data: Dict[str, Any], title: str = "Validation Report") -> str:
        """Generate Markdown report"""
        md = f"# 🔍 {title}\n\n"
        md += f"Generated by SchemaPilot v{__version__}\n\n"

        # Add stats
        if "stats" in report_data:
            stats = report_data["stats"]
            md += "## 📊 Statistics\n\n"
            md += f"- **Total Checks**: {stats.get('total_checks', 0)}\n"
            md += f"- **✅ Passed**: {stats.get('passed', 0)}\n"
            md += f"- **❌ Failed**: {stats.get('failed', 0)}\n"
            md += f"- **⚠️ Warnings**: {stats.get('warnings', 0)}\n\n"

        # Add validation status
        is_valid = report_data.get("valid", True)
        if is_valid and not report_data.get("errors"):
            md += "## ✅ Result\n\nAll validations passed!\n\n"
        else:
            # Add errors
            if report_data.get("errors"):
                md += "## ❌ Errors\n\n"
                for error in report_data["errors"]:
                    md += f"- **{error.get('path', '$')}**: {error.get('message', '')}\n"
                md += "\n"

            # Add warnings
            if report_data.get("warnings"):
                md += "## ⚠️ Warnings\n\n"
                for warning in report_data["warnings"]:
                    md += f"- **{warning.get('path', '$')}**: {warning.get('message', '')}\n"
                md += "\n"

        md += f"\n---\n*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
        return md


def print_colored(text: str, color: str = ""):
    """Print colored text to terminal"""
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "magenta": "\033[95m",
        "cyan": "\033[96m",
        "bold": "\033[1m",
        "reset": "\033[0m"
    }
    if color in colors:
        print(f"{colors[color]}{text}{colors['reset']}")
    else:
        print(text)


def print_banner():
    """Print application banner"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   🔍 SchemaPilot - JSON Schema Validation & Testing Engine   ║
║                                                              ║
║   Lightweight • Zero Dependencies • Developer Friendly       ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """
    print_colored(banner, "cyan")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="SchemaPilot - JSON Schema Intelligent Validation & Testing Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate JSON file against schema
  schemapilot validate -d data.json -s schema.json

  # Generate schema from JSON data
  schemapilot generate -d data.json -o schema.json

  # Test API endpoint
  schemapilot test -u https://api.example.com/users

  # Batch validate multiple files
  schemapilot batch -f "*.json" -s schema.json

  # Generate HTML report
  schemapilot validate -d data.json -s schema.json -o report.html --format html
        """
    )

    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate JSON against schema")
    validate_parser.add_argument("-d", "--data", required=True, help="JSON data file to validate")
    validate_parser.add_argument("-s", "--schema", required=True, help="JSON Schema file")
    validate_parser.add_argument("-o", "--output", help="Output file for report")
    validate_parser.add_argument("--format", choices=["json", "html", "markdown"], default="json",
                                help="Report format (default: json)")

    # Generate command
    generate_parser = subparsers.add_parser("generate", help="Generate schema from JSON data")
    generate_parser.add_argument("-d", "--data", required=True, help="JSON data file")
    generate_parser.add_argument("-o", "--output", help="Output schema file")
    generate_parser.add_argument("-t", "--title", default="Generated Schema", help="Schema title")

    # Test command
    test_parser = subparsers.add_parser("test", help="Test API endpoint")
    test_parser.add_argument("-u", "--url", required=True, help="API URL to test")
    test_parser.add_argument("-s", "--schema", help="Schema file for response validation")
    test_parser.add_argument("-m", "--method", default="GET", help="HTTP method (default: GET)")
    test_parser.add_argument("-H", "--header", action="append", help="HTTP headers (format: 'Key: Value')")
    test_parser.add_argument("-b", "--body", help="Request body (JSON string or @file.json)")
    test_parser.add_argument("-o", "--output", help="Output file for results")
    test_parser.add_argument("--format", choices=["json", "html", "markdown"], default="json",
                            help="Report format")

    # Batch command
    batch_parser = subparsers.add_parser("batch", help="Batch validate multiple files")
    batch_parser.add_argument("-f", "--files", required=True, help="File pattern (e.g., '*.json')")
    batch_parser.add_argument("-s", "--schema", required=True, help="Schema file")
    batch_parser.add_argument("-o", "--output", help="Output file for report")
    batch_parser.add_argument("--format", choices=["json", "html", "markdown"], default="json",
                             help="Report format")

    args = parser.parse_args()

    if not args.command:
        print_banner()
        parser.print_help()
        sys.exit(0)

    if args.verbose:
        print_banner()

    # Execute command
    if args.command == "validate":
        cmd_validate(args)
    elif args.command == "generate":
        cmd_generate(args)
    elif args.command == "test":
        cmd_test(args)
    elif args.command == "batch":
        cmd_batch(args)


def cmd_validate(args):
    """Handle validate command"""
    try:
        # Load data
        with open(args.data, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Load schema
        with open(args.schema, 'r', encoding='utf-8') as f:
            schema = json.load(f)

        print_colored(f"🔍 Validating {args.data} against {args.schema}...", "blue")

        # Validate
        validator = SchemaValidator()
        result = validator.validate(data, schema)

        # Output results
        report_data = result.to_dict()

        if args.output:
            if args.format == "html":
                report = ReportGenerator.generate_html(report_data, "Validation Report")
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(report)
            elif args.format == "markdown":
                report = ReportGenerator.generate_markdown(report_data, "Validation Report")
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(report)
            else:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(report_data, f, indent=2)
            print_colored(f"✅ Report saved to {args.output}", "green")
        else:
            # Print to console
            print(f"\n{'='*60}")
            print(f"Validation Result: {'✅ PASSED' if result.is_valid else '❌ FAILED'}")
            print(f"{'='*60}")
            print(f"Total Checks: {result.stats['total_checks']}")
            print_colored(f"✅ Passed: {result.stats['passed']}", "green")
            print_colored(f"❌ Failed: {result.stats['failed']}", "red" if result.stats['failed'] > 0 else "")
            print_colored(f"⚠️ Warnings: {result.stats['warnings']}", "yellow" if result.stats['warnings'] > 0 else "")

            if result.errors:
                print(f"\n❌ Errors:")
                for error in result.errors:
                    print_colored(f"  • [{error.path}] {error.message}", "red")

            if result.warnings:
                print(f"\n⚠️ Warnings:")
                for warning in result.warnings:
                    print_colored(f"  • [{warning.path}] {warning.message}", "yellow")

        sys.exit(0 if result.is_valid else 1)

    except FileNotFoundError as e:
        print_colored(f"❌ File not found: {e}", "red")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print_colored(f"❌ Invalid JSON: {e}", "red")
        sys.exit(1)
    except Exception as e:
        print_colored(f"❌ Error: {e}", "red")
        sys.exit(1)


def cmd_generate(args):
    """Handle generate command"""
    try:
        # Load data
        with open(args.data, 'r', encoding='utf-8') as f:
            data = json.load(f)

        print_colored(f"📝 Generating schema from {args.data}...", "blue")

        # Generate schema
        schema = SchemaGenerator.generate(data, args.title)

        # Output
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(schema, f, indent=2)
            print_colored(f"✅ Schema saved to {args.output}", "green")
        else:
            print("\nGenerated Schema:")
            print(json.dumps(schema, indent=2))

    except FileNotFoundError:
        print_colored(f"❌ File not found: {args.data}", "red")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print_colored(f"❌ Invalid JSON: {e}", "red")
        sys.exit(1)


def cmd_test(args):
    """Handle test command"""
    try:
        # Load schema if provided
        schema = None
        if args.schema:
            with open(args.schema, 'r', encoding='utf-8') as f:
                schema = json.load(f)

        # Parse headers
        headers = {}
        if args.header:
            for header in args.header:
                if ':' in header:
                    key, value = header.split(':', 1)
                    headers[key.strip()] = value.strip()

        # Parse body
        body = None
        if args.body:
            if args.body.startswith('@'):
                with open(args.body[1:], 'r', encoding='utf-8') as f:
                    body = json.load(f)
            else:
                body = json.loads(args.body)

        print_colored(f"🌐 Testing {args.method} {args.url}...", "blue")

        # Test endpoint
        tester = APITester()
        result = tester.test_endpoint(args.url, schema, args.method, headers, body)

        # Output results
        if args.output:
            if args.format == "html":
                report = ReportGenerator.generate_html(result, "API Test Report")
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(report)
            elif args.format == "markdown":
                report = ReportGenerator.generate_markdown(result, "API Test Report")
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(report)
            else:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2)
            print_colored(f"✅ Report saved to {args.output}", "green")
        else:
            # Print to console
            print(f"\n{'='*60}")
            status = result.get("status")
            if status:
                color = "green" if 200 <= status < 300 else "yellow" if 300 <= status < 400 else "red"
                print_colored(f"Status: {status}", color)
            if result.get("error"):
                print_colored(f"Error: {result['error']}", "red")

            if result.get("response"):
                print(f"\nResponse:")
                print(json.dumps(result["response"], indent=2))

            if result.get("validation"):
                validation = result["validation"]
                print(f"\n{'='*60}")
                print(f"Validation: {'✅ PASSED' if validation['valid'] else '❌ FAILED'}")
                if validation.get("errors"):
                    for error in validation["errors"]:
                        print_colored(f"  • [{error['path']}] {error['message']}", "red")

    except Exception as e:
        print_colored(f"❌ Error: {e}", "red")
        sys.exit(1)


def cmd_batch(args):
    """Handle batch command"""
    try:
        import glob

        # Find files
        files = glob.glob(args.files)
        if not files:
            print_colored(f"❌ No files found matching: {args.files}", "red")
            sys.exit(1)

        print_colored(f"📁 Found {len(files)} files to validate", "blue")
        print_colored(f"📋 Using schema: {args.schema}", "blue")

        # Batch validate
        validator = BatchValidator()
        results = validator.validate_files(files, args.schema)

        # Output results
        if args.output:
            if args.format == "html":
                # Create a combined HTML report for batch
                html = f"""<!DOCTYPE html>
<html><head><title>Batch Validation Report</title>
                <style>
                    body {{ font-family: sans-serif; margin: 20px; }}
                    .success {{ color: green; }}
                    .fail {{ color: red; }}
                    table {{ border-collapse: collapse; width: 100%; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background: #667eea; color: white; }}
                    tr:nth-child(even) {{ background: #f2f2f2; }}
                </style></head><body>
                <h1>📁 Batch Validation Report</h1>
                <p>Schema: {results['schema']}</p>
                <p>Total: {results['total_files']} | ✅ Passed: {results['passed']} | ❌ Failed: {results['failed']}</p>
                <table>
                <tr><th>File</th><th>Status</th><th>Errors</th></tr>"""

                for r in results["results"]:
                    status = "✅ PASSED" if r["valid"] else "❌ FAILED"
                    css_class = "success" if r["valid"] else "fail"
                    errors = "<br>".join([f"{e['path']}: {e['message']}" for e in r["errors"]])
                    html += f'<tr><td>{r["file"]}</td><td class="{css_class}">{status}</td><td>{errors}</td></tr>'

                html += f"</table><p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p></body></html>"

                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(html)
            elif args.format == "markdown":
                md = f"# 📁 Batch Validation Report\n\n"
                md += f"**Schema**: {results['schema']}\n\n"
                md += f"**Total**: {results['total_files']} | **✅ Passed**: {results['passed']} | **❌ Failed**: {results['failed']}\n\n"
                md += "| File | Status | Errors |\n"
                md += "|------|--------|--------|\n"
                for r in results["results"]:
                    status = "✅ PASSED" if r["valid"] else "❌ FAILED"
                    errors = "; ".join([f"{e['path']}: {e['message']}" for e in r["errors"]]) if r["errors"] else "-"
                    md += f"| {r['file']} | {status} | {errors} |\n"
                md += f"\n*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(md)
            else:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2)
            print_colored(f"✅ Report saved to {args.output}", "green")
        else:
            # Print to console
            print(f"\n{'='*60}")
            print(f"Batch Validation Results")
            print(f"{'='*60}")
            print(f"Total Files: {results['total_files']}")
            print_colored(f"✅ Passed: {results['passed']}", "green")
            print_colored(f"❌ Failed: {results['failed']}", "red" if results['failed'] > 0 else "")

            for r in results["results"]:
                status_icon = "✅" if r["valid"] else "❌"
                color = "green" if r["valid"] else "red"
                print_colored(f"{status_icon} {r['file']}", color)
                if r["errors"]:
                    for error in r["errors"]:
                        print_colored(f"   └─ [{error['path']}] {error['message']}", "red")

    except Exception as e:
        print_colored(f"❌ Error: {e}", "red")
        sys.exit(1)


if __name__ == "__main__":
    main()
