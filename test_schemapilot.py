#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SchemaPilot - Unit Tests
"""

import json
import unittest
import tempfile
import os
from schemapilot import (
    SchemaValidator, SchemaGenerator, ValidationResult,
    APITester, BatchValidator, ReportGenerator
)


class TestSchemaGenerator(unittest.TestCase):
    """Test schema generation"""

    def test_generate_string(self):
        data = "hello"
        schema = SchemaGenerator.generate(data, "Test")
        self.assertEqual(schema["type"], "string")
        self.assertEqual(schema["title"], "Test")

    def test_generate_integer(self):
        data = 42
        schema = SchemaGenerator.generate(data)
        self.assertEqual(schema["type"], "integer")

    def test_generate_number(self):
        data = 3.14
        schema = SchemaGenerator.generate(data)
        self.assertEqual(schema["type"], "number")

    def test_generate_boolean(self):
        data = True
        schema = SchemaGenerator.generate(data)
        self.assertEqual(schema["type"], "boolean")

    def test_generate_null(self):
        data = None
        schema = SchemaGenerator.generate(data)
        self.assertEqual(schema["type"], "null")

    def test_generate_array(self):
        data = [1, 2, 3]
        schema = SchemaGenerator.generate(data)
        self.assertEqual(schema["type"], "array")
        self.assertIn("items", schema)

    def test_generate_object(self):
        data = {"name": "John", "age": 30}
        schema = SchemaGenerator.generate(data)
        self.assertEqual(schema["type"], "object")
        self.assertIn("properties", schema)
        self.assertIn("name", schema["properties"])
        self.assertIn("age", schema["properties"])
        self.assertIn("required", schema)

    def test_generate_nested_object(self):
        data = {"user": {"name": "John", "email": "john@example.com"}}
        schema = SchemaGenerator.generate(data)
        self.assertEqual(schema["type"], "object")
        self.assertIn("user", schema["properties"])
        self.assertEqual(schema["properties"]["user"]["type"], "object")

    def test_detect_email_format(self):
        data = {"email": "test@example.com"}
        schema = SchemaGenerator.generate(data)
        self.assertEqual(schema["properties"]["email"].get("format"), "email")

    def test_detect_date_format(self):
        data = {"date": "2025-01-15"}
        schema = SchemaGenerator.generate(data)
        self.assertEqual(schema["properties"]["date"].get("format"), "date")

    def test_detect_uri_format(self):
        data = {"url": "https://example.com"}
        schema = SchemaGenerator.generate(data)
        self.assertEqual(schema["properties"]["url"].get("format"), "uri")


class TestSchemaValidator(unittest.TestCase):
    """Test schema validation"""

    def setUp(self):
        self.validator = SchemaValidator()

    def test_validate_string(self):
        schema = {"type": "string"}
        result = self.validator.validate("hello", schema)
        self.assertTrue(result.is_valid)

    def test_validate_string_wrong_type(self):
        schema = {"type": "string"}
        result = self.validator.validate(123, schema)
        self.assertFalse(result.is_valid)
        self.assertEqual(len(result.errors), 1)

    def test_validate_integer(self):
        schema = {"type": "integer"}
        result = self.validator.validate(42, schema)
        self.assertTrue(result.is_valid)

    def test_validate_number(self):
        schema = {"type": "number"}
        result = self.validator.validate(3.14, schema)
        self.assertTrue(result.is_valid)

    def test_validate_boolean(self):
        schema = {"type": "boolean"}
        result = self.validator.validate(True, schema)
        self.assertTrue(result.is_valid)

    def test_validate_null(self):
        schema = {"type": "null"}
        result = self.validator.validate(None, schema)
        self.assertTrue(result.is_valid)

    def test_validate_array(self):
        schema = {"type": "array"}
        result = self.validator.validate([1, 2, 3], schema)
        self.assertTrue(result.is_valid)

    def test_validate_object(self):
        schema = {"type": "object"}
        result = self.validator.validate({"key": "value"}, schema)
        self.assertTrue(result.is_valid)

    def test_validate_string_minlength(self):
        schema = {"type": "string", "minLength": 5}
        result = self.validator.validate("hello", schema)
        self.assertTrue(result.is_valid)

        result = self.validator.validate("hi", schema)
        self.assertFalse(result.is_valid)

    def test_validate_string_maxlength(self):
        schema = {"type": "string", "maxLength": 5}
        result = self.validator.validate("hello", schema)
        self.assertTrue(result.is_valid)

        result = self.validator.validate("hello world", schema)
        self.assertFalse(result.is_valid)

    def test_validate_string_pattern(self):
        schema = {"type": "string", "pattern": "^[a-z]+$"}
        result = self.validator.validate("hello", schema)
        self.assertTrue(result.is_valid)

        result = self.validator.validate("Hello123", schema)
        self.assertFalse(result.is_valid)

    def test_validate_number_minimum(self):
        schema = {"type": "number", "minimum": 0}
        result = self.validator.validate(5, schema)
        self.assertTrue(result.is_valid)

        result = self.validator.validate(-1, schema)
        self.assertFalse(result.is_valid)

    def test_validate_number_maximum(self):
        schema = {"type": "number", "maximum": 100}
        result = self.validator.validate(50, schema)
        self.assertTrue(result.is_valid)

        result = self.validator.validate(150, schema)
        self.assertFalse(result.is_valid)

    def test_validate_array_minitems(self):
        schema = {"type": "array", "minItems": 2}
        result = self.validator.validate([1, 2, 3], schema)
        self.assertTrue(result.is_valid)

        result = self.validator.validate([1], schema)
        self.assertFalse(result.is_valid)

    def test_validate_array_maxitems(self):
        schema = {"type": "array", "maxItems": 3}
        result = self.validator.validate([1, 2], schema)
        self.assertTrue(result.is_valid)

        result = self.validator.validate([1, 2, 3, 4], schema)
        self.assertFalse(result.is_valid)

    def test_validate_array_uniqueitems(self):
        schema = {"type": "array", "uniqueItems": True}
        result = self.validator.validate([1, 2, 3], schema)
        self.assertTrue(result.is_valid)

        result = self.validator.validate([1, 2, 2], schema)
        self.assertFalse(result.is_valid)

    def test_validate_object_required(self):
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            },
            "required": ["name"]
        }
        result = self.validator.validate({"name": "John"}, schema)
        self.assertTrue(result.is_valid)

        result = self.validator.validate({"age": 30}, schema)
        self.assertFalse(result.is_valid)

    def test_validate_object_properties(self):
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            }
        }
        result = self.validator.validate({"name": "John", "age": 30}, schema)
        self.assertTrue(result.is_valid)

        result = self.validator.validate({"name": 123, "age": "thirty"}, schema)
        self.assertFalse(result.is_valid)
        self.assertEqual(len(result.errors), 2)

    def test_validate_enum(self):
        schema = {"enum": ["red", "green", "blue"]}
        result = self.validator.validate("red", schema)
        self.assertTrue(result.is_valid)

        result = self.validator.validate("yellow", schema)
        self.assertFalse(result.is_valid)

    def test_validate_const(self):
        schema = {"const": "hello"}
        result = self.validator.validate("hello", schema)
        self.assertTrue(result.is_valid)

        result = self.validator.validate("world", schema)
        self.assertFalse(result.is_valid)

    def test_validate_multiple_types(self):
        schema = {"type": ["string", "null"]}
        result = self.validator.validate("hello", schema)
        self.assertTrue(result.is_valid)

        result = self.validator.validate(None, schema)
        self.assertTrue(result.is_valid)

        result = self.validator.validate(123, schema)
        self.assertFalse(result.is_valid)


class TestValidationResult(unittest.TestCase):
    """Test validation result"""

    def test_initial_state(self):
        result = ValidationResult()
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.errors), 0)
        self.assertEqual(len(result.warnings), 0)

    def test_add_error(self):
        result = ValidationResult()
        result.add_error("$.name", "Required field missing")
        self.assertFalse(result.is_valid)
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.stats["failed"], 1)

    def test_add_warning(self):
        result = ValidationResult()
        result.add_warning("$.email", "Invalid format")
        self.assertTrue(result.is_valid)  # Warnings don't invalidate
        self.assertEqual(len(result.warnings), 1)
        self.assertEqual(result.stats["warnings"], 1)

    def test_to_dict(self):
        result = ValidationResult()
        result.add_error("$.name", "Error message")
        result.add_warning("$.email", "Warning message")

        data = result.to_dict()
        self.assertIn("valid", data)
        self.assertIn("errors", data)
        self.assertIn("warnings", data)
        self.assertIn("stats", data)


class TestReportGenerator(unittest.TestCase):
    """Test report generation"""

    def test_generate_html(self):
        report_data = {
            "valid": False,
            "stats": {
                "total_checks": 10,
                "passed": 7,
                "failed": 2,
                "warnings": 1
            },
            "errors": [
                {"path": "$.name", "message": "Required field", "type": "error"}
            ],
            "warnings": [
                {"path": "$.email", "message": "Invalid format", "type": "warning"}
            ]
        }
        html = ReportGenerator.generate_html(report_data, "Test Report")
        self.assertIn("Test Report", html)
        self.assertIn("10", html)  # total_checks
        self.assertIn("$.name", html)

    def test_generate_markdown(self):
        report_data = {
            "valid": True,
            "stats": {
                "total_checks": 5,
                "passed": 5,
                "failed": 0,
                "warnings": 0
            },
            "errors": [],
            "warnings": []
        }
        md = ReportGenerator.generate_markdown(report_data, "Test Report")
        self.assertIn("# 🔍 Test Report", md)
        self.assertIn("✅ Passed", md)


class TestBatchValidator(unittest.TestCase):
    """Test batch validation"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.schema_path = os.path.join(self.temp_dir, "schema.json")
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            },
            "required": ["name"]
        }
        with open(self.schema_path, 'w') as f:
            json.dump(schema, f)

        # Create test data files
        self.valid_file = os.path.join(self.temp_dir, "valid.json")
        with open(self.valid_file, 'w') as f:
            json.dump({"name": "John", "age": 30}, f)

        self.invalid_file = os.path.join(self.temp_dir, "invalid.json")
        with open(self.invalid_file, 'w') as f:
            json.dump({"age": 30}, f)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_validate_files(self):
        validator = BatchValidator()
        files = [self.valid_file, self.invalid_file]
        results = validator.validate_files(files, self.schema_path)

        self.assertEqual(results["total_files"], 2)
        self.assertEqual(results["passed"], 1)
        self.assertEqual(results["failed"], 1)


class TestIntegration(unittest.TestCase):
    """Integration tests"""

    def test_full_workflow(self):
        """Test complete workflow: generate -> validate"""
        # Generate schema from data
        data = {"name": "John", "age": 30, "email": "john@example.com"}
        schema = SchemaGenerator.generate(data, "User Schema")

        # Validate same data against generated schema
        validator = SchemaValidator()
        result = validator.validate(data, schema)

        self.assertTrue(result.is_valid)

    def test_validation_with_nested_objects(self):
        """Test validation of nested objects"""
        schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "address": {
                            "type": "object",
                            "properties": {
                                "city": {"type": "string"},
                                "zip": {"type": "string"}
                            },
                            "required": ["city"]
                        }
                    },
                    "required": ["name"]
                }
            },
            "required": ["user"]
        }

        data = {
            "user": {
                "name": "John",
                "address": {
                    "city": "New York",
                    "zip": "10001"
                }
            }
        }

        validator = SchemaValidator()
        result = validator.validate(data, schema)
        self.assertTrue(result.is_valid)

    def test_validation_with_arrays(self):
        """Test validation of arrays with items"""
        schema = {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "minItems": 2
                }
            }
        }

        data = {"items": [1, 2, 3]}

        validator = SchemaValidator()
        result = validator.validate(data, schema)
        self.assertTrue(result.is_valid)


if __name__ == "__main__":
    unittest.main(verbosity=2)
