#!/usr/bin/env python3
"""
Data Analysis Script

This script analyzes transformed data and generates insights.
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
logger = logging.getLogger("data-analyzer")

class DataAnalyzer:
    """Analyzes data and generates insights."""
    
    def __init__(self, analysis_depth: str = "full"):
        """
        Initialize the analyzer.
        
        Args:
            analysis_depth: Depth of analysis (full, summary, minimal)
        """
        self.analysis_depth = analysis_depth
        logger.info(f"Initialized analyzer with {analysis_depth} analysis depth")
    
    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze the transformed data.
        
        Args:
            data: The transformed data to analyze
            
        Returns:
            Analysis results
        """
        # Extract the transformed records
        records = data.get("data", [])
        transformation_type = data.get("transformation_type", "unknown")
        
        if not records:
            logger.warning("No records to analyze")
            return {
                "analyzed_at": time.time(),
                "analysis_depth": self.analysis_depth,
                "insights": [],
                "summary": {
                    "total_records": 0,
                    "message": "No data to analyze"
                }
            }
        
        logger.info(f"Analyzing {len(records)} records with {transformation_type} transformation")
        
        # Perform analysis based on transformation type and depth
        insights = []
        summary = {
            "total_records": len(records)
        }
        
        # Simulate potential transient failure for testing retry mechanism
        if os.environ.get('SIMULATE_FAILURE') == 'true' and not os.path.exists('.analysis_attempt'):
            with open('.analysis_attempt', 'w') as f:
                f.write('attempted')
            logger.error("Simulated transient failure")
            raise ConnectionError("Simulated transient failure")
        
        if transformation_type == "standard":
            insights, summary = self._analyze_standard_records(records)
        elif transformation_type == "aggregated":
            insights, summary = self._analyze_aggregated_records(records)
        elif transformation_type == "normalized":
            insights, summary = self._analyze_normalized_records(records)
        else:
            logger.warning(f"Unknown transformation type: {transformation_type}, using basic analysis")
            insights, summary = self._analyze_basic_records(records)
        
        # Apply depth filter
        if self.analysis_depth != "full":
            insights = self._filter_insights_by_depth(insights)
        
        # Construct the analysis results
        results = {
            "analyzed_at": time.time(),
            "analysis_depth": self.analysis_depth,
            "source_transformation": {
                "transformed_at": data.get("transformed_at"),
                "transformation_type": transformation_type,
                "total_records": data.get("total_records")
            },
            "insights": insights,
            "summary": summary
        }
        
        logger.info(f"Analysis complete, generated {len(insights)} insights")
        return results
    
    def _filter_insights_by_depth(self, insights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter insights based on analysis depth.
        
        Args:
            insights: List of insights
            
        Returns:
            Filtered insights
        """
        if not insights:
            return []
        
        if self.analysis_depth == "minimal":
            # Keep only high importance insights
            return [insight for insight in insights if insight.get("importance", "low") == "high"]
        elif self.analysis_depth == "summary":
            # Keep high and medium importance insights
            return [insight for insight in insights if insight.get("importance", "low") in ["high", "medium"]]
        
        # Default to returning all insights
        return insights
    
    def _analyze_standard_records(self, records: List[Dict[str, Any]]) -> tuple:
        """
        Analyze standard transformed records.
        
        Args:
            records: List of standard transformed records
            
        Returns:
            Tuple of (insights, summary)
        """
        insights = []
        
        # Extract values for analysis
        values = []
        normalized_values = []
        categories = {}
        active_count = 0
        
        for record in records:
            metrics = record.get("metrics", {})
            metadata = record.get("metadata", {})
            
            value = metrics.get("value", 0)
            values.append(value)
            
            normalized_value = metrics.get("normalized_value", 0)
            normalized_values.append(normalized_value)
            
            category = metadata.get("category")
            if category:
                categories[category] = categories.get(category, 0) + 1
            
            if metadata.get("is_active", False):
                active_count += 1
        
        # Calculate statistics
        avg_value = sum(values) / len(values) if values else 0
        max_value = max(values) if values else 0
        min_value = min(values) if values else 0
        value_range = max_value - min_value
        
        # Generate insights
        if value_range > 0 and max_value > avg_value * 2:
            insights.append({
                "type": "outlier",
                "message": f"High value outliers detected, max value ({max_value}) is more than twice the average ({avg_value:.2f})",
                "importance": "high",
                "metrics": {
                    "max_value": max_value,
                    "avg_value": avg_value,
                    "ratio": max_value / avg_value if avg_value else 0
                }
            })
        
        if len(categories) > 0:
            most_common_category = max(categories.items(), key=lambda x: x[1])
            insights.append({
                "type": "distribution",
                "message": f"Most common category is '{most_common_category[0]}' with {most_common_category[1]} records ({most_common_category[1]/len(records)*100:.1f}%)",
                "importance": "medium",
                "metrics": {
                    "category": most_common_category[0],
                    "count": most_common_category[1],
                    "percentage": most_common_category[1]/len(records)*100
                }
            })
        
        active_percentage = active_count / len(records) * 100 if records else 0
        insights.append({
            "type": "activity",
            "message": f"{active_count} out of {len(records)} records are active ({active_percentage:.1f}%)",
            "importance": "low",
            "metrics": {
                "active_count": active_count,
                "total_records": len(records),
                "active_percentage": active_percentage
            }
        })
        
        # Generate summary
        summary = {
            "total_records": len(records),
            "active_records": active_count,
            "categories": len(categories),
            "metrics": {
                "avg_value": avg_value,
                "min_value": min_value,
                "max_value": max_value,
                "value_range": value_range
            }
        }
        
        return insights, summary
    
    def _analyze_aggregated_records(self, records: List[Dict[str, Any]]) -> tuple:
        """
        Analyze aggregated transformed records.
        
        Args:
            records: List of aggregated transformed records
            
        Returns:
            Tuple of (insights, summary)
        """
        insights = []
        
        # Extract category data for analysis
        categories = {}
        total_items = 0
        
        for record in records:
            category = record.get("category", "unknown")
            count = record.get("count", 0)
            metrics = record.get("metrics", {})
            
            categories[category] = {
                "count": count,
                "total_value": metrics.get("total_value", 0),
                "average_value": metrics.get("average_value", 0),
                "min_value": metrics.get("min_value", 0),
                "max_value": metrics.get("max_value", 0)
            }
            
            total_items += count
        
        # Find highest and lowest performing categories
        if categories:
            highest_avg = max(categories.items(), key=lambda x: x[1]["average_value"])
            lowest_avg = min(categories.items(), key=lambda x: x[1]["average_value"])
            
            insights.append({
                "type": "performance",
                "message": f"Highest performing category is '{highest_avg[0]}' with average value {highest_avg[1]['average_value']:.2f}",
                "importance": "high",
                "metrics": {
                    "category": highest_avg[0],
                    "average_value": highest_avg[1]["average_value"],
                    "count": highest_avg[1]["count"]
                }
            })
            
            insights.append({
                "type": "performance",
                "message": f"Lowest performing category is '{lowest_avg[0]}' with average value {lowest_avg[1]['average_value']:.2f}",
                "importance": "medium",
                "metrics": {
                    "category": lowest_avg[0],
                    "average_value": lowest_avg[1]["average_value"],
                    "count": lowest_avg[1]["count"]
                }
            })
            
            # If the difference between highest and lowest is significant
            if highest_avg[1]["average_value"] > 0 and highest_avg[1]["average_value"] / (lowest_avg[1]["average_value"] or 1) > 2:
                insights.append({
                    "type": "comparison",
                    "message": f"Performance gap: '{highest_avg[0]}' outperforms '{lowest_avg[0]}' by {highest_avg[1]['average_value']/lowest_avg[1]['average_value']:.1f}x",
                    "importance": "high",
                    "metrics": {
                        "ratio": highest_avg[1]["average_value"]/(lowest_avg[1]["average_value"] or 1)
                    }
                })
        
        # Generate summary
        summary = {
            "total_categories": len(categories),
            "total_items": total_items,
            "metrics": {
                "category_distribution": {
                    category: data["count"] for category, data in categories.items()
                }
            }
        }
        
        return insights, summary
    
    def _analyze_normalized_records(self, records: List[Dict[str, Any]]) -> tuple:
        """
        Analyze normalized transformed records.
        
        Args:
            records: List of normalized transformed records
            
        Returns:
            Tuple of (insights, summary)
        """
        insights = []
        
        # Extract values for analysis
        original_values = []
        normalized_values = []
        categories = {}
        
        for record in records:
            original_value = record.get("original_value", 0)
            original_values.append(original_value)
            
            normalized_value = record.get("normalized_value", 0)
            normalized_values.append(normalized_value)
            
            metadata = record.get("metadata", {})
            category = metadata.get("category")
            if category:
                if category not in categories:
                    categories[category] = {
                        "count": 0,
                        "total_normalized": 0,
                        "records": []
                    }
                categories[category]["count"] += 1
                categories[category]["total_normalized"] += normalized_value
                categories[category]["records"].append(record)
        
        # Calculate distribution of normalized values
        high_performers = len([v for v in normalized_values if v > 0.8])
        mid_performers = len([v for v in normalized_values if 0.4 <= v <= 0.8])
        low_performers = len([v for v in normalized_values if v < 0.4])
        
        insights.append({
            "type": "distribution",
            "message": f"Performance distribution: {high_performers} high ({high_performers/len(normalized_values)*100:.1f}%), {mid_performers} mid ({mid_performers/len(normalized_values)*100:.1f}%), {low_performers} low ({low_performers/len(normalized_values)*100:.1f}%)",
            "importance": "high",
            "metrics": {
                "high_performers": high_performers,
                "mid_performers": mid_performers,
                "low_performers": low_performers,
                "total": len(normalized_values)
            }
        })
        
        # Find best and worst performing categories
        if categories:
            for category, data in categories.items():
                data["avg_normalized"] = data["total_normalized"] / data["count"] if data["count"] else 0
            
            best_category = max(categories.items(), key=lambda x: x[1]["avg_normalized"])
            worst_category = min(categories.items(), key=lambda x: x[1]["avg_normalized"])
            
            insights.append({
                "type": "category",
                "message": f"Best performing category: '{best_category[0]}' with average normalized value {best_category[1]['avg_normalized']:.2f}",
                "importance": "medium",
                "metrics": {
                    "category": best_category[0],
                    "avg_normalized": best_category[1]["avg_normalized"],
                    "count": best_category[1]["count"]
                }
            })
            
            insights.append({
                "type": "category",
                "message": f"Worst performing category: '{worst_category[0]}' with average normalized value {worst_category[1]['avg_normalized']:.2f}",
                "importance": "medium",
                "metrics": {
                    "category": worst_category[0],
                    "avg_normalized": worst_category[1]["avg_normalized"],
                    "count": worst_category[1]["count"]
                }
            })
        
        # Generate summary
        summary = {
            "total_records": len(records),
            "performance_distribution": {
                "high": high_performers,
                "mid": mid_performers,
                "low": low_performers
            },
            "metrics": {
                "avg_normalized_value": sum(normalized_values) / len(normalized_values) if normalized_values else 0,
                "categories": len(categories)
            }
        }
        
        return insights, summary
    
    def _analyze_basic_records(self, records: List[Dict[str, Any]]) -> tuple:
        """
        Perform basic analysis when the format is unknown.
        
        Args:
            records: List of records in unknown format
            
        Returns:
            Tuple of (insights, summary)
        """
        insights = []
        
        # Just extract whatever numerical values we can find
        numerical_values = []
        
        for record in records:
            # Recursively find numerical values
            self._extract_numerical_values(record, numerical_values)
        
        # Basic statistics if we found any numerical values
        if numerical_values:
            avg_value = sum(numerical_values) / len(numerical_values)
            max_value = max(numerical_values)
            min_value = min(numerical_values)
            
            insights.append({
                "type": "basic",
                "message": f"Found {len(numerical_values)} numerical values with average {avg_value:.2f}",
                "importance": "medium",
                "metrics": {
                    "count": len(numerical_values),
                    "avg": avg_value,
                    "min": min_value,
                    "max": max_value
                }
            })
        
        # Generate summary
        summary = {
            "total_records": len(records),
            "numerical_values": len(numerical_values),
            "metrics": {
                "avg_value": sum(numerical_values) / len(numerical_values) if numerical_values else 0
            }
        }
        
        return insights, summary
    
    def _extract_numerical_values(self, obj: Any, values: List[float]) -> None:
        """
        Recursively extract numerical values from an object.
        
        Args:
            obj: Object to extract values from
            values: List to append values to
        """
        if isinstance(obj, (int, float)) and not isinstance(obj, bool):
            values.append(float(obj))
        elif isinstance(obj, dict):
            for value in obj.values():
                self._extract_numerical_values(value, values)
        elif isinstance(obj, list):
            for item in obj:
                self._extract_numerical_values(item, values)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Analyze transformed data')
    parser.add_argument('--input', required=True, help='Input JSON file (transformed data)')
    parser.add_argument('--output', required=True, help='Output JSON file')
    parser.add_argument('--depth', default=os.environ.get('ANALYSIS_DEPTH', 'full'),
                      choices=['full', 'summary', 'minimal'],
                      help='Analysis depth')
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()
    
    # Load transformed data
    try:
        with open(args.input, 'r') as f:
            transformed_data = json.load(f)
    except Exception as e:
        logger.error(f"Error loading transformed data: {e}")
        sys.exit(1)
    
    # Create analyzer
    analyzer = DataAnalyzer(args.depth)
    
    # Analyze data
    try:
        analysis_results = analyzer.analyze(transformed_data)
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)
    
    # Write output
    try:
        with open(args.output, 'w') as f:
            json.dump(analysis_results, f, indent=2)
        
        logger.info(f"Analysis complete, output written to {args.output}")
    except Exception as e:
        logger.error(f"Error writing output: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
