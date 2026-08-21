"""
Diff Analyzer - Analyzes script changes for differential processing
Only processes modified sections when scripts are updated
"""

import hashlib
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import difflib

logger = logging.getLogger(__name__)


class DiffAnalyzer:
    """
    Analyzes differences between script versions
    Enables efficient re-processing of only changed content
    """
    
    def __init__(self):
        self.script_hashes = {}  # Store hashes of previous versions
        self.script_sections = {}  # Store sectioned versions
        
    def analyze_changes(
        self, 
        script_text: str, 
        script_id: str,
        previous_version: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze changes between script versions
        
        Args:
            script_text: Current script content
            script_id: Unique identifier for the script
            previous_version: Previous version of script (if available)
            
        Returns:
            Change analysis with sections that need reprocessing
        """
        
        current_hash = self._calculate_script_hash(script_text)
        current_sections = self._split_into_sections(script_text)
        
        # Check if we have a previous version
        previous_hash = self.script_hashes.get(script_id)
        previous_sections = self.script_sections.get(script_id, {})
        
        if not previous_hash:
            # First time processing this script
            analysis = {
                "is_new_script": True,
                "change_type": "new",
                "changed_sections": list(range(len(current_sections))),
                "unchanged_sections": [],
                "total_sections": len(current_sections),
                "sections_to_process": current_sections,
                "change_summary": f"New script with {len(current_sections)} sections"
            }
        else:
            # Compare with previous version
            analysis = self._compare_versions(
                current_sections, 
                previous_sections,
                script_id
            )
        
        # Store current version for future comparisons
        self.script_hashes[script_id] = current_hash
        self.script_sections[script_id] = current_sections
        
        logger.info(f"Script diff analysis for {script_id}: {analysis['change_summary']}")
        return analysis
    
    def _compare_versions(
        self, 
        current_sections: List[Dict[str, Any]], 
        previous_sections: Dict[int, Dict[str, Any]],
        script_id: str
    ) -> Dict[str, Any]:
        """Compare current and previous script versions"""
        
        changed_sections = []
        unchanged_sections = []
        sections_to_process = []
        
        # Convert previous sections dict to list format
        prev_sections_list = [previous_sections.get(i, {}) for i in range(len(previous_sections))]
        
        # Compare section by section
        max_sections = max(len(current_sections), len(prev_sections_list))
        
        for i in range(max_sections):
            current_section = current_sections[i] if i < len(current_sections) else None
            previous_section = prev_sections_list[i] if i < len(prev_sections_list) else None
            
            if not current_section:
                # Section was deleted
                continue
            elif not previous_section:
                # New section added
                changed_sections.append(i)
                sections_to_process.append(current_section)
            elif self._sections_differ(current_section, previous_section):
                # Section was modified
                changed_sections.append(i)
                sections_to_process.append(current_section)
            else:
                # Section unchanged
                unchanged_sections.append(i)
        
        # Determine change type
        if len(changed_sections) == len(current_sections):
            change_type = "major_rewrite"
        elif len(changed_sections) > len(current_sections) * 0.5:
            change_type = "significant_changes"
        elif len(changed_sections) > 0:
            change_type = "minor_changes"
        else:
            change_type = "no_changes"
        
        return {
            "is_new_script": False,
            "change_type": change_type,
            "changed_sections": changed_sections,
            "unchanged_sections": unchanged_sections,
            "total_sections": len(current_sections),
            "sections_to_process": sections_to_process,
            "change_summary": f"{change_type}: {len(changed_sections)}/{len(current_sections)} sections changed"
        }
    
    def _split_into_sections(self, script_text: str) -> List[Dict[str, Any]]:
        """Split script into logical sections for diff analysis"""
        
        sections = []
        lines = script_text.split('\n')
        
        current_section = []
        section_type = "content"
        scene_number = 1
        
        for i, line in enumerate(lines):
            line_upper = line.strip().upper()
            
            # Detect scene boundaries
            if any(indicator in line_upper for indicator in ['EXT.', 'INT.', 'FADE IN:', 'FADE OUT']):
                # Save previous section if it exists
                if current_section:
                    sections.append({
                        "section_id": len(sections),
                        "type": section_type,
                        "scene_number": scene_number - 1,
                        "content": '\n'.join(current_section),
                        "hash": self._calculate_text_hash('\n'.join(current_section)),
                        "start_line": i - len(current_section),
                        "end_line": i - 1,
                        "line_count": len(current_section)
                    })
                
                # Start new section
                current_section = [line]
                section_type = "scene"
                scene_number += 1
            else:
                current_section.append(line)
        
        # Add final section
        if current_section:
            sections.append({
                "section_id": len(sections),
                "type": section_type,
                "scene_number": scene_number - 1,
                "content": '\n'.join(current_section),
                "hash": self._calculate_text_hash('\n'.join(current_section)),
                "start_line": len(lines) - len(current_section),
                "end_line": len(lines) - 1,
                "line_count": len(current_section)
            })
        
        return sections
    
    def _sections_differ(
        self, 
        section1: Dict[str, Any], 
        section2: Dict[str, Any]
    ) -> bool:
        """Check if two sections are different"""
        
        # Compare hashes first (fast)
        if section1.get("hash") != section2.get("hash"):
            return True
        
        # If hashes match, sections are identical
        return False
    
    def _calculate_script_hash(self, script_text: str) -> str:
        """Calculate hash of entire script"""
        return hashlib.md5(script_text.encode('utf-8')).hexdigest()
    
    def _calculate_text_hash(self, text: str) -> str:
        """Calculate hash of text section"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def get_detailed_diff(
        self, 
        current_text: str, 
        previous_text: str
    ) -> List[Dict[str, Any]]:
        """Get detailed line-by-line diff between versions"""
        
        current_lines = current_text.splitlines()
        previous_lines = previous_text.splitlines()
        
        # Use difflib for detailed comparison
        differ = difflib.unified_diff(
            previous_lines, 
            current_lines, 
            lineterm='',
            n=3  # Context lines
        )
        
        diff_lines = []
        for line in differ:
            if line.startswith('@@'):
                # Parse hunk header
                continue
            elif line.startswith('+'):
                diff_lines.append({"type": "added", "content": line[1:]})
            elif line.startswith('-'):
                diff_lines.append({"type": "removed", "content": line[1:]})
            elif line.startswith(' '):
                diff_lines.append({"type": "context", "content": line[1:]})
        
        return diff_lines
    
    def should_reprocess_full_script(self, analysis: Dict[str, Any]) -> bool:
        """Determine if full script reprocessing is needed"""
        
        change_type = analysis.get("change_type", "new")
        
        # Reprocess full script for major changes
        if change_type in ["new", "major_rewrite"]:
            return True
        
        # Reprocess if more than 70% of sections changed
        changed_ratio = len(analysis.get("changed_sections", [])) / max(analysis.get("total_sections", 1), 1)
        if changed_ratio > 0.7:
            return True
        
        return False
    
    def get_processing_strategy(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Get recommended processing strategy based on changes"""
        
        if self.should_reprocess_full_script(analysis):
            return {
                "strategy": "full_reprocess",
                "reason": "Major changes detected",
                "sections_to_process": "all",
                "estimated_time": "full"
            }
        else:
            return {
                "strategy": "differential_process",
                "reason": f"Only {len(analysis.get('changed_sections', []))} sections changed",
                "sections_to_process": analysis.get("changed_sections", []),
                "estimated_time": "partial"
            }
    
    def clear_script_history(self, script_id: str) -> bool:
        """Clear stored history for a script"""
        
        removed = False
        if script_id in self.script_hashes:
            del self.script_hashes[script_id]
            removed = True
        
        if script_id in self.script_sections:
            del self.script_sections[script_id]
            removed = True
        
        return removed