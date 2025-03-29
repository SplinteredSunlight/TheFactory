#!/usr/bin/env python3
"""
Data Transformation Script

This script transforms validated data into a standardized format.
"""

import argparse
import json
import logging
import os
import sys
import time
from typing import Dict, List, Any

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("data-transformer")

class DataTransformer:
    """Transforms data into a standardized format."""
    
    def __init__(self, transformation_type: str = "standard"):
        """
        Initialize the transformer.
        
        Args:
            transformation_type: Type of transformation to apply
        """
        self.transformation_type = transformation_type
        logger.info(f"Initialized transformer with {transformation_type} transformation type")
    
    def transform(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform the validated data.
        
        Args:
            data: The validated data to transform
            
        Returns:
            Transformed data
        """
        # Extract the actual data records
        records = data.get("data", [])
        
        if not records:
            logger.warning("No records to transform")
            return {
                "transformed_at": time.time(),
                "transformation_type": self.transformation_type,
                "total_records": 0,
                "data": []
            }
        
        logger.info(f"Transforming {len(records)} records")
        
        # Apply transformation based on type
        transformed_records = []
        if self.transformation_type == "standard":
            transformed_records = self._apply_standard_transformation(records)
        elif self.transformation_type == "aggregated":
            transformed_records = self._apply_aggregated_transformation(records)
        elif self.transformation_type == "normalized":
            transformed_records = self._apply_normalized_transformation(records)
        else:
            logger.warning(f"Unknown transformation type: {self.transformation_type}, using standard")
            transformed_records = self._apply_standard_transformation(records)
        
        # Construct the transformed data
        transformed_data = {
            "transformed_at": time.time(),
            "transformation_type": self.transformation_type,
            "total_records": len(transformed_records),
            "source_validation": {
                "validated_at": data.get("validated_at"),
                "validation_level": data.get("validation_level"),
                "total_records": data.get("total_records"),
                "errors": data.get("errors", [])
            },
            "data": transformed_records
        }
        
        logger.info(f"Transformation complete, {len(transformed_records)} records transformed")
        return transformed_data
    
    def _apply_standard_transformation(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Apply standard transformation to records.
        
        Args:
            records: List of data records
            
        Returns:
            Transformed records
        """
        transformed_records = []
        
        # Simulate potential transient failure for testing retry mechanism
        if os.environ.get('SIMULATE_FAILURE') == 'true' and not os.path.exists('.transformation_attempt'):
            with open('.transformation_attempt', 'w') as f:
                f.write('attempted')
            logger.error("Simulated transient failure")
            raise ConnectionError("Simulated transient failure")
        
        for record in records:
            transformed_record = {
                "id": record.get("id"),
                "name": record.get("name"),
                "metadata": {
                    "timestamp": record.get("timestamp"),
                    "category": record.get("category"),
                    "is_active": record.get("is_active", False)
                },
                "metrics": {
                    "value": record.get("value", 0),
                    "normalized_value": self._normalize_value(record.get("value", 0))
                }
            }
            transformed_records.append(transformed_record)
        
        return transformed_records
    
    def _apply_aggregated_transformation(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Apply aggregated transformation to records.
        
        Args:
            records: List of data records
            
        Returns:
            Transformed records with aggregations
        """
        # Group records by category
        categories = {}
        for record in records:
            category = record.get("category", "unknown")
            if category not in categories:
                categories[category] = []
            categories[category].append(record)
        
        transformed_records = []
        for category, category_records in categories.items():
            # Calculate aggregations
            total_value = sum(record.get("value", 0) for record in category_records)
            avg_value = total_value / len(category_records) if category_records else 0
            
            transformed_record = {
                "category": category,
                "count": len(category_records),
                "metrics": {
                    "total_value": total_value,
                    "average_value": avg_value,
                    "min_value": min((record.get("value", 0) for record in category_records), default=0),
                    "max_value": max((record.get("value", 0) for record in category_records), default=0)
                },
                "items": [
                    {
                        "id": record.get("id"),
                        "name": record.get("name"),
                        "value": record.get("value", 0)
                    }
                    for record in category_records
                ]
            }
            transformed_records.append(transformed_record)
        
        return transformed_records
    
    def _apply_normalized_transformation(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Apply normalized transformation to records.
        
        Args:
            records: List of data records
            
        Returns:
            Transformed records with normalized values
        """
        # Find min and max values for normalization
        values = [record.get("value", 0) for record in records]
        min_value = min(values) if values else 0
        max_value = max(values) if values else 1
        value_range = max_value - min_value if max_value > min_value else 1
        
        transformed_records = []
        for record in records:
            value = record.get("value", 0)
            normalized_value = (value - min_value) / value_range if value_range != 0 else 0
            
            transformed_record = {
                "id": record.get("id"),
                "name": record.get("name"),
                "original_value": value,
                "normalized_value": normalized_value,
                "metadata": {
                    "timestamp": record.get("timestamp"),
                    "category": record.get("category"),
                    "is_active": record.get("is_active", False)
                }
            }
            transformed_records.append(transformed_record)
        
        return transformed_records
    
    def _normalize_value(self, value: float) -> float:
        """
        Normalize a single value to a 0-1 scale.
        
        Args:
            value: Value to normalize
            
        Returns:
            Normalized value
        """
        # Simple normalization function, can be customized
        # This just maps any value to a 0-1 scale using a sigmoid function
        if value == 0:
            return 0.5
        return 1 / (1 + pow(0.5, value / 10))


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Transform validated data')
    parser.add_argument('--input', required=True, help='Input JSON file (validated data)')
    parser.add_argument('--output', required=True, help='Output JSON file')
    parser.add_argument('--type', default=os.environ.get('TRANSFORMATION_TYPE', 'standard'),
                      choices=['standard', 'aggregated', 'normalized'],
                      help='Transformation type')
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()
    
    # Load validated data
    try:
        with open(args.input, 'r') as f:
            validated_data = json.load(f)
    except Exception as e:
        logger.error(f"Error loading validated data: {e}")
        sys.exit(1)
    
    # Create transformer
    transformer = DataTransformer(args.type)
    
    # Transform data
    try:
        transformed_data = transformer.transform(validated_data)
    except Exception as e:
        logger.error(f"Transformation failed: {e}")
        sys.exit(1)
    
    # Write output
    try:
        with open(args.output, 'w') as f:
            json.dump(transformed_data, f, indent=2)
        
        logger.info(f"Transformation complete, output written to {args.output}")
    except Exception as e:
        logger.error(f"Error writing output: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
