"""Robustness analysis across different embedding models.

Compares geometry-hallucination correlations using:
1. Original: text-embedding-3-small (1536-dim)
2. Alternative 1: text-embedding-3-large (3072-dim)
3. Alternative 2: all-mpnet-base-v2 (768-dim, open source)
"""

import sys
import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.geometry.curvature import compute_curvature_proxy
from src.geometry.density import compute_local_density
from src.geometry.centrality import compute_distance_to_center
from src.geometry.intrinsic_dimension import compute_local_id_for_all
from src.geometry.reference_corpus import load_reference_corpus


def load_embeddings(embedding_file):
    """Load embedding file."""
    return np.load(embedding_file)


def compute_geometry_features(embeddings, reference_corpus_path="data/reference_corpus", custom_reference=None):
    """Compute geometry features for the given embeddings."""
    print(f"    Computing geometry features for {len(embeddings)} embeddings...")
    
    # Load reference corpus
    if custom_reference:
        print("      Using custom reference corpus (matched dimensionality)")
        ref_embeddings = custom_reference['embeddings']
        ref_mean = custom_reference['mean']
    else:
        ref_corpus = load_reference_corpus(Path(reference_corpus_path))
        ref_embeddings = ref_corpus['embeddings']
        ref_mean = ref_corpus['mean']
    
    n_samples = len(embeddings)
    
    # First compute local IDs (needed for curvature)
    print("      Computing local intrinsic dimensions...")
    local_ids = compute_local_id_for_all(embeddings, n_neighbors=20, metric='cosine')
    
    # Initialize features
    features = {
        'curvature_score': np.zeros(n_samples),
        'density': np.zeros(n_samples),
        'centrality': np.zeros(n_samples)
    }
    
    # Compute curvature using local IDs
    print("      Computing curvature...")
    try:
        features['curvature_score'] = compute_curvature_proxy(
            embeddings, 
            local_ids, 
            n_neighbors=20, 
            metric='cosine'
        )
    except Exception as e:
        print(f"      Warning: Curvature computation failed: {e}")
        features['curvature_score'] = np.full(n_samples, np.nan)
    
    # Compute density
    print("      Computing density...")
    try:
        features['density'] = compute_local_density(
            embeddings, 
            ref_embeddings, 
            k=20, 
            metric='cosine'
        )
    except Exception as e:
        print(f"      Warning: Density computation failed: {e}")
        features['density'] = np.full(n_samples, np.nan)
    
    # Compute centrality
    print("      Computing centrality...")
    try:
        features['centrality'] = compute_distance_to_center(
            embeddings, 
            ref_mean, 
            metric='cosine'
        )
    except Exception as e:
        print(f"      Warning: Centrality computation failed: {e}")
        features['centrality'] = np.full(n_samples, np.nan)
    
    # Return as DataFrame
    return pd.DataFrame(features)


def compute_correlation(results_df, geometry_feature='curvature_score'):
    """Compute Spearman correlation between geometry and hallucination."""
    try:
        # Extract values as arrays to avoid index issues
        geom_vals = results_df[geometry_feature].values
        hall_vals = results_df['is_hallucinated'].values
        
        # Remove NaN values
        valid_mask = ~(pd.isna(geom_vals) | pd.isna(hall_vals))
        geom_valid = geom_vals[valid_mask]
        hall_valid = hall_vals[valid_mask]
        
        if len(geom_valid) < 10:
            return np.nan, 1.0
        
        correlation, p_value = stats.spearmanr(
            geom_valid,
            hall_valid,
            nan_policy='omit'
        )
        return correlation, p_value
    except Exception as e:
        print(f"      Warning: Correlation computation failed: {e}")
        return np.nan, 1.0


def analyze_robustness(original_results, alternative_embeddings_dir, output_dir):
    """Compare correlations across embedding models."""
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Load original results (from V2 or V3)
    df = pd.read_csv(original_results)
    
    # Deduplicate by id and model_name, keep first occurrence
    if 'id' in df.columns and 'model_name' in df.columns:
        df = df.drop_duplicates(subset=['id', 'model_name'], keep='first')
    elif 'id' in df.columns:
        df = df.drop_duplicates(subset=['id'], keep='first')
    
    # Reset index to avoid duplicate index issues
    df = df.reset_index(drop=True)
    
    print(f"Loaded {len(df)} unique samples for robustness analysis\n")
    
    # Load prompts to get IDs (crucial for alignment)
    import json
    prompts_file = "data/prompts/prompts.jsonl"
    prompt_ids = []
    with open(prompts_file, 'r') as f:
        for line in f:
            if line.strip():
                prompt_ids.append(json.loads(line)['id'])
    
    print(f"Loaded {len(prompt_ids)} prompt IDs for alignment")
    
    # Models to test
    embedding_models = [
        {
            'name': 'text-embedding-3-small (Original)',
            'file': 'data/processed/question_embeddings.npy',
            'color': 'blue'
        },
        {
            'name': 'text-embedding-3-large',
            'file': f'{alternative_embeddings_dir}/embeddings_openai_large.npy',
            'color': 'green'
        },
        {
            'name': 'all-mpnet-base-v2 (Open Source)',
            'file': f'{alternative_embeddings_dir}/embeddings_mpnet.npy',
            'color': 'orange'
        }
    ]
    
    results = []
    
    for model_info in embedding_models:
        print(f"\nAnalyzing: {model_info['name']}")
        
        if not Path(model_info['file']).exists():
            print(f"  Skipping (file not found: {model_info['file']})")
            continue
        
        # Load embeddings
        embeddings = load_embeddings(model_info['file'])
        print(f"  Loaded embeddings: {embeddings.shape}")
        
        if len(embeddings) != len(prompt_ids):
            print(f"  Warning: Embedding count ({len(embeddings)}) != Prompt count ({len(prompt_ids)})")
            # Truncate to match
            min_len = min(len(embeddings), len(prompt_ids))
            embeddings = embeddings[:min_len]
            current_ids = prompt_ids[:min_len]
        else:
            current_ids = prompt_ids
            
        # Determine reference corpus
        custom_ref = None
        if 'Original' not in model_info['name']:
            # For alternative models, use the embeddings themselves as reference
            # to avoid dimensionality mismatch
            print("  Generating self-reference stats for alternative model...")
            custom_ref = {
                'embeddings': embeddings,
                'mean': np.mean(embeddings, axis=0)
            }
            
        # Compute geometry
        print("  Computing geometry features...")
        geometry_df = compute_geometry_features(embeddings, custom_reference=custom_ref)
        
        # Add IDs to geometry dataframe
        geometry_df['id'] = current_ids
        
        # Ensure ID types match for merge
        geometry_df['id'] = geometry_df['id'].astype(str)
        if 'id' in df.columns:
            df['id'] = df['id'].astype(str)
            
        # Drop existing geometry columns from df to avoid duplicates
        cols_to_drop = [col for col in ['curvature_score', 'density', 'centrality'] if col in df.columns]
        if cols_to_drop:
            df_clean = df.drop(columns=cols_to_drop)
        else:
            df_clean = df
            
        # Merge on ID
        merged_df = df_clean.merge(geometry_df, on='id', how='inner')
        print(f"  Merged data: {len(merged_df)} rows (from {len(df)} results and {len(geometry_df)} embeddings)")
        
        # Compute correlations for each feature
        for feature in ['curvature_score', 'density', 'centrality']:
            if feature in merged_df.columns:
                corr, p_val = compute_correlation(merged_df, feature)
                
                results.append({
                    'embedding_model': model_info['name'],
                    'geometry_feature': feature,
                    'correlation': corr,
                    'p_value': p_val
                })
                
                print(f"    {feature}: r={corr:.3f}, p={p_val:.4f}")
    
    # Save results
    results_df = pd.DataFrame(results)
    results_df.to_csv(f"{output_dir}/embedding_robustness_results.csv", index=False)
    
    # Create visualization
    pivot = results_df.pivot(index='geometry_feature', columns='embedding_model', values='correlation')
    # Clean up feature names for display
    pivot.index = [name.replace('_', ' ').title() for name in pivot.index]

    plt.figure(figsize=(10, 6))
    pivot.plot(kind='bar', rot=0)
    plt.title('Geometry-Hallucination Correlation Across Embedding Models', fontsize=14, fontweight='bold')
    plt.ylabel('Spearman Correlation (r)', fontsize=12)
    plt.xlabel('Geometry Feature', fontsize=12)
    plt.legend(title='Embedding Model')
    plt.tight_layout()
    plt.savefig(f"{output_dir}/embedding_robustness_comparison.png", dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"\n✅ Robustness analysis complete!")
    print(f"Results saved to: {output_dir}/")
    
    return results_df


def main():
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-file", default="results/v3/multi_model/all_models_results.csv")
    parser.add_argument("--alt-embeddings-dir", default="data/processed/alternative_embeddings")
    parser.add_argument("--output-dir", default="results/v3/robustness")
    
    args = parser.parse_args()
    
    analyze_robustness(args.results_file, args.alt_embeddings_dir, args.output_dir)


if __name__ == "__main__":
    main()
