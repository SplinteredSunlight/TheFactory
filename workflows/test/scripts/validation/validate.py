#!/usr/bin/env python3
"""
Data Validation Script

This script validates CSV data against a JSON schema.
"""

import argparse
import csv
import json
import logging
import os
import sys
import time
from typing import Dict, List, Any, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("data-validator")

class DataValidator:
    """Validates data against a schema."""
    
    def __init__(self, schema: Dict[str, Any], level: str = "strict"):
        """
        Initialize the validator.
        
        Args:
            schema: The schema to validate against
            level: Validation level (strict, moderate, relaxed)
        """
        self.schema = schema
        self.level = level
        self.errors = []
        
        logger.info(f"Initialized validator with {level} validation level")
    
    def validate_csv(self, csv_file: str) -> List[Dict[str, Any]]:
        """
        Validate a CSV file against the schema.
        
        Args:
            csv_file: Path to the CSV file
            
        Returns:
            List of validated data rows
        """
        validated_data = []
        row_num = 0
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                # Simulate potential transient failure for testing retry mechanism
                if os.environ.get('SIMULATE_FAILURE') == 'true' and not os.path.exists('.validation_attempt'):
                    with open('.validation_attempt', 'w') as f:
                        f.write('attempted')
                    logger.error("Simulated transient failure")
                    raise ConnectionError("Simulated transient failure")
                
                reader = csv.DictReader(f)
                
                # Validate header
                self._validate_header(reader.fieldnames)
                
                # Validate each row
                for row_num, row in enumerate(reader, 1):
                    validated_row = self._validate_row(row, row_num)
                    if validated_row:
                        validated_data.append(validated_row)
        
        except Exception as e:
            logger.error(f"Error validating CSV file: {e}")
            if self.level == "strict":
                raise
            else:
                self.errors.append(f"Error processing file: {e}")
        
        # Log validation summary
        total_rows = row_num
        valid_rows = len(validated_data)
        logger.info(f"Validation complete: {valid_rows}/{total_rows} rows valid")
        
        if self.errors and self.level == "strict":
            raise ValueError(f"Validation failed with {len(self.errors)} errors")
        
        return validated_data
    
    def _validate_header(self, fieldnames: List[str]) -> None:
        """
        Validate the header of the CSV file.
        
        Args:
            fieldnames: List of field names from the CSV
        """
        required_fields = self.schema.get('required_fields', [])
        
        # Check if all required fields are present
        missing_fields = [field for field in required_fields if field not in fieldnames]
        if missing_fields:
            error = f"Missing required fields: {', '.join(missing_fields)}"
            logger.error(error)
            self.errors.append(error)
            if self.level == "strict":
                raise ValueError(error)
        
        # Check for unknown fields if in strict mode
        if self.level == "strict":
            allowed_fields = self.schema.get('fields', {}).keys()
            unknown_fields = [field for field in fieldnames if field not in allowed_fields]
            if unknown_fields:
                error = f"Unknown fields: {', '.join(unknown_fields)}"
                logger.warning(error)
                self.errors.append(error)
    
    def _validate_row(self, row: Dict[str, str], row_num: int) -> Optional[Dict[str, Any]]:
        """
        Validate a single row of data.
        
        Args:
            row: Dictionary representing a row of data
            row_num: Row number for error reporting
            
        Returns:
            Validated row with proper types, or None if invalid
        """
        validated_row = {}
        
        for field_name, field_value in row.items():
            field_schema = self.schema.get('fields', {}).get(field_name)
            
            # Skip unknown fields
            if not field_schema:
                if self.level == "strict":
                    continue
                else:
                    validated_row[field_name] = field_value
                    continue
            
            # Check if field is required
            if not field_value and field_name in self.schema.get('required_fields', []):
                error = f"Row {row_num}: Missing required field '{field_name}'"
                logger.error(error)
                self.errors.append(error)
                if self.level == "strict":
                    return None
            
            # Convert and validate field value
            try:
                validated_value = self._convert_field_value(field_name, field_value, field_schema)
                validated_row[field_name] = validated_value
            except ValueError as e:
                error = f"Row {row_num}: {str(e)}"
                logger.error(error)
                self.errors.append(error)
                if self.level == "strict":
                    return None
                # Use original value in non-strict mode
                validated_row[field_name] = field_value
        
        return validated_row
    
    def _convert_field_value(self, field_name: str, field_value: str, field_schema: Dict[str, Any]) -> Any:
        """
        Convert a field value to the proper type based on the schema.
        
        Args:
            field_name: Name of the field
            field_value: Value of the field as a string
            field_schema: Schema for the field
            
        Returns:
            Converted field value
        """
        field_type = field_schema.get('type', 'string')
        
        # Handle empty values
        if not field_value:
            if field_name in self.schema.get('required_fields', []):
                raise ValueError(f"Missing required field '{field_name}'")
            return None
        
        # Convert based on type
        try:
            if field_type == 'integer':
                return int(field_value)
            elif field_type == 'number':
                return float(field_value)
            elif field_type == 'boolean':
                return field_value.lower() in ('true', 'yes', '1', 'y')
            elif field_type == 'date':
                # Simple date validation, could be enhanced
                if not (len(field_value) == 10 and field_value[4] == '-' and field_value[7] == '-'):
                    raise ValueError(f"Invalid date format for field '{field_name}': {field_value}")
                return field_value
            else:
                # Default to string
                return field_value
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid {field_type} value for field '{field_name}': {field_value}")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Validate CSV data against a schema')
    parser.add_argument('--input', required=True, help='Input CSV file')
    parser.add_argument('--schema', required=True, help='Schema JSON file')
    parser.add_argument('--output', required=True, help='Output JSON file')
    parser.add_argument('--level', default=os.environ.get('VALIDATION_LEVEL', 'strict'),
                      choices=['strict', 'moderate', 'relaxed'],
                      help='Validation level')
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()
    
    # Load schema
    try:
        with open(args.schema, 'r') as f:
            schema = json.load(f)
    except Exception as e:
        logger.error(f"Error loading schema: {e}")
        sys.exit(1)
    
    # Create validator
    validator = DataValidator(schema, args.level)
    
    # Validate data
    try:
        validated_data = validator.validate_csv(args.input)
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        sys.exit(1)
    
    # Write output
    try:
        output_data = {
            "validated_at": time.time(),
            "validation_level": args.level,
            "total_records": len(validated_data),
            "errors": validator.errors,
            "data": validated_data
        }
        
        with open(args.output, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        logger.info(f"Validation complete, output written to {args.output}")
    except Exception as e:
        logger.error(f"Error writing output: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
