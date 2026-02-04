"""
Formatter Module - Formats validation and detection results for UI display
"""
import json
from pathlib import Path


class ResultFormatter:
    """Formats results for Streamlit display"""

    @staticmethod
    def format_detection_card(detection_result):
        """Format detection results for display card"""
        return {
            "Version": detection_result.get("version", "Unknown"),
            "Format": detection_result.get("format", "Unknown"),
            "Is Bundle": "✅ Yes" if detection_result.get("is_bundle") else "❌ No",
            "Object Count": detection_result.get("object_count", 0),
            "File Size (KB)": f"{detection_result.get('file_size_kb', 0):.2f}",
            "Status": "✅ Valid" if detection_result.get("is_valid") else "❌ Invalid"
        }

    @staticmethod
    def format_validation_summary(validation_result):
        """Format validation results summary"""
        return {
            "Status": validation_result.get("summary", "Unknown"),
            "Errors": validation_result.get("error_count", 0),
            "Warnings": validation_result.get("warning_count", 0),
            "Result": "✅ PASSED" if validation_result.get("is_valid") else "❌ FAILED"
        }

    @staticmethod
    def format_statistics_table(stats):
        """Format statistics for display table"""
        return {
            "Total Objects": stats.get("total_objects", 0),
            "Threat Indicators": stats.get("threat_indicators", 0),
            "Malware Objects": stats.get("malware_objects", 0),
            "Identity Objects": stats.get("identity_objects", 0),
            "Campaign Objects": stats.get("campaign_objects", 0),
            "Attack Pattern Objects": stats.get("attack_pattern_objects", 0),
            "Tool Objects": stats.get("tool_objects", 0),
            "Vulnerability Objects": stats.get("vulnerability_objects", 0)
        }

    @staticmethod
    def format_errors_list(errors, warnings):
        """Format errors and warnings as displayable list"""
        formatted = []
        
        if errors:
            formatted.append(("ERRORS", errors))
        if warnings:
            formatted.append(("WARNINGS", warnings))
        
        return formatted

    @staticmethod
    def get_file_preview(filepath, lines=100):
        """Get first N lines of file for preview"""
        filepath = Path(filepath)
        
        try:
            with filepath.open("r", encoding="utf-8") as f:
                content = f.read()
            
            # Try to format JSON
            try:
                data = json.loads(content)
                formatted = json.dumps(data, indent=2)
                lines_list = formatted.split("\n")[:lines]
                return "\n".join(lines_list), "json"
            except:
                # Plain text preview
                lines_list = content.split("\n")[:lines]
                return "\n".join(lines_list), "text"
        
        except Exception as e:
            return f"Error reading file: {str(e)}", "error"

    @staticmethod
    def get_conversion_preview(filepath, lines=50):
        """Get preview of converted STIX 2.1 file"""
        filepath = Path(filepath)
        
        try:
            with filepath.open("r", encoding="utf-8") as f:
                content = f.read()
            
            data = json.loads(content)
            formatted = json.dumps(data, indent=2)
            lines_list = formatted.split("\n")[:lines]
            
            return "\n".join(lines_list), True
        
        except Exception as e:
            return f"Error reading converted file: {str(e)}", False
