"""
A/B testing for feature experimentation
"""

import hashlib
from enum import Enum

class ExperimentVariant(str, Enum):
    CONTROL = "control"
    TREATMENT_A = "treatment_a"
    TREATMENT_B = "treatment_b"

class ABTestManager:
    
    async def get_variant(self, experiment_id: str, user_id: str) -> ExperimentVariant:
        """
        Get A/B test variant for user
        Uses consistent hashing to ensure same user always gets same variant
        """
        
        # Consistent hash to determine variant
        hash_value = int(hashlib.md5(
            f"{user_id}:{experiment_id}".encode()
        ).hexdigest(), 16) % 100
        
        # Get experiment config
        experiment = await self.get_experiment(experiment_id)
        
        if not experiment:
            return ExperimentVariant.CONTROL
        
        # Determine variant based on percentages
        if hash_value < experiment['control_percentage']:
            return ExperimentVariant.CONTROL
        elif hash_value < experiment['control_percentage'] + experiment['treatment_a_percentage']:
            return ExperimentVariant.TREATMENT_A
        else:
            return ExperimentVariant.TREATMENT_B
    
    async def track_event(self, experiment_id: str, user_id: str, 
                         event_type: str, value: float = 1.0):
        """
        Track experiment event (conversion, click, etc.)
        """
        
        variant = await self.get_variant(experiment_id, user_id)
        
        # Log to analytics
        await self.log_event(
            experiment_id=experiment_id,
            user_id=user_id,
            variant=variant,
            event_type=event_type,
            value=value
        )
    
    async def get_results(self, experiment_id: str) -> dict:
        """Get experiment results and statistical significance"""
        
        # Calculate metrics per variant
        results = await self.calculate_experiment_metrics(experiment_id)
        
        return {
            'control': results['control'],
            'treatment_a': results['treatment_a'],
            'treatment_b': results['treatment_b'],
            'winner': self.determine_winner(results),
            'significance': self.calculate_significance(results)
        }