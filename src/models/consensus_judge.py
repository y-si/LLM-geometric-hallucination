"""Consensus Judge Client.

Uses multiple models to judge answers and determines the final verdict by majority vote.
"""

import os
import json
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any

from src.models.judge_client import JudgeClient

class ConsensusJudge:
    """A judge that aggregates opinions from multiple LLMs."""
    
    def __init__(self, judges_config: List[Dict[str, str]]):
        """
        Initialize with a list of judge configurations.
        
        Args:
            judges_config: List of dicts, e.g. [{'provider': 'openai', 'model': 'gpt-4o'}]
        """
        self.judges = []
        for config in judges_config:
            judge = JudgeClient(
                model_name=config['model'],
                provider=config['provider'],
                max_retries=3,
                timeout=60
            )
            self.judges.append(judge)
            
    def judge(self, question, answer, ground_truth, meta_info=None):
        """Get judgments from all judges and aggregate."""
        
        results = []
        
        # Run judges in parallel
        with ThreadPoolExecutor(max_workers=len(self.judges)) as executor:
            futures = []
            for judge in self.judges:
                futures.append(executor.submit(
                    judge.judge, question, answer, ground_truth, meta_info
                ))
            
            for f in futures:
                try:
                    results.append(f.result())
                except Exception as e:
                    print(f"WARNING: Judge failed: {e}")
                    results.append({"label": 3, "confidence": 0.0, "justification": f"Error: {str(e)}", "failed": True})
        
        # Separate real vs failed judges
        real_results = [r for r in results if not r.get("failed", False)]
        failed_count = len(results) - len(real_results)

        if failed_count > 0:
            print(f"WARNING: {failed_count}/{len(results)} judges failed for this entry")

        # Use only real judges for consensus (fall back to all if none succeeded)
        vote_results = real_results if real_results else results

        if not vote_results:
            # All judges failed and results list is empty — should not happen but handle gracefully
            return {
                "label": 3,
                "confidence": 0.0,
                "justification": "All judges failed and produced no results",
                "individual_judgments": results,
                "agreement_rate": 0.0,
                "individual_confidence_avg": 0.0
            }

        labels = [r['label'] for r in vote_results]

        # Majority vote
        counts = Counter(labels)
        majority_label, majority_count = counts.most_common(1)[0]

        # Calculate confidence based on agreement rate
        # e.g., if 3/3 agree → 1.0, if 2/3 agree → 0.67
        total_judges = len(labels)
        agreement_rate = majority_count / total_judges

        # Weight by average individual confidence for nuance
        # Final confidence = agreement_rate * avg_individual_confidence
        avg_individual_confidence = sum(r['confidence'] for r in vote_results) / len(vote_results)
        consensus_confidence = agreement_rate * avg_individual_confidence

        # Combine justifications (use .get() to handle missing keys)
        combined_justification = " | ".join([
            f"{j.model_name}: {r.get('justification', 'No justification')}"
            for j, r in zip(self.judges, results)
        ])
        
        return {
            "label": majority_label,
            "confidence": consensus_confidence,
            "justification": combined_justification,
            "individual_judgments": results,
            "agreement_rate": agreement_rate,
            "individual_confidence_avg": avg_individual_confidence
        }
