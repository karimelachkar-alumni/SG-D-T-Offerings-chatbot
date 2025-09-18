"""
Baseline Estimates Manager

Simple direct lookup for baseline estimates without RAG searches.
"""

import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class BaselineEstimatesManager:
    """Simple manager for baseline estimates lookup."""
    
    def __init__(self):
        """Initialize the baseline estimates manager."""
        self.estimates_data = self._load_estimates()
    
    def _load_estimates(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load baseline estimates from the data file."""
        try:
            import sys
            from pathlib import Path
            
            # Add the project root to the path
            project_root = Path(__file__).parent.parent.parent
            sys.path.insert(0, str(project_root))
            
            from data.baseline_estimates import BASELINE_ESTIMATES
            logger.info(f"Loaded baseline estimates for {len(BASELINE_ESTIMATES)} services")
            return BASELINE_ESTIMATES
        except ImportError as e:
            logger.error(f"Failed to load baseline estimates: {e}")
            return {}
    
    def get_baseline_estimates(self, service_name: str) -> Optional[List[Dict[str, Any]]]:
        """Get baseline estimates for a specific service.
        
        Args:
            service_name: Name of the service (e.g., "Execution: ERP")
            
        Returns:
            List of baseline estimates for the service, or None if not found
        """
        return self.estimates_data.get(service_name)
    
    def get_all_services(self) -> List[str]:
        """Get list of all available service names."""
        return list(self.estimates_data.keys())
    
    def search_services(self, query: str) -> List[str]:
        """Search for services by name (case-insensitive partial match)."""
        query_lower = query.lower()
        matches = []
        
        for service_name in self.estimates_data.keys():
            if query_lower in service_name.lower():
                matches.append(service_name)
        
        return matches


# Global instance
baseline_estimates_manager = BaselineEstimatesManager()
