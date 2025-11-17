import requests
import pandas as pd
from pathlib import Path
import re
import json
from time import sleep

def load_gold_standard(json_path='gold_standard.json'):
    """Load gold standard from JSON file."""
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
        # Convert string keys to integers
        return {int(k): v for k, v in data.items()}
    except FileNotFoundError:
        print(f"Error: {json_path} not found. Please create it first.")
        return {}

def transcribe_audio(file_path):
    """Send audio file to transcription service and return the text."""
    url = "http://localhost:8000/transcribe"
    
    with open(file_path, "rb") as f:
        files = {"file": (file_path.name, f, "audio/wav")}
        response = requests.post(url, files=files)
    
    if response.status_code == 200:
        return response.json()["transcription"]
    else:
        raise Exception(f"Error: {response.json()}")

def parse_filename(filename):
    """Extract sample number and noise level from filename."""
    match = re.match(r'sample_(\d+)_noise_(\d+)\.wav', filename)
    if match:
        sample_num = int(match.group(1))
        noise_level = int(match.group(2))
        return sample_num, noise_level
    return None, None

def exact_match(transcription, gold_standard):
    """Check if transcription matches gold standard (case-insensitive)."""
    if transcription == "ERROR" or gold_standard is None:
        return False
    return transcription.lower().strip() == gold_standard.lower().strip()

def transcribe_folder(folder_path="test_samples", gold_standard_path="gold_standard.json", runs=3):
    """Transcribe all .wav files multiple times and create Excel report with gold standard comparison."""
    # Load gold standard
    GOLD_STANDARD = load_gold_standard(gold_standard_path)
    
    if not GOLD_STANDARD:
        print("Cannot proceed without gold standard.")
        return
    
    print(f"✓ Loaded {len(GOLD_STANDARD)} gold standard utterances")
    print(f"✓ Each sample will be run {runs} times\n")
    
    folder = Path(folder_path)
    wav_files = sorted(folder.glob("*.wav"))
    
    if not wav_files:
        print(f"No .wav files found in {folder_path}/")
        return
    
    total_runs = len(wav_files) * runs
    print(f"Found {len(wav_files)} .wav files ({total_runs} total runs)\n")
    
    results = []
    run_count = 0
    
    for wav_file in wav_files:
        sample_num, noise_level = parse_filename(wav_file.name)
        gold = GOLD_STANDARD.get(sample_num, "")
        
        # Run each file multiple times
        for run in range(1, runs + 1):
            run_count += 1
            print(f"[{run_count}/{total_runs}] Processing: {wav_file.name} (Run {run}/{runs})")
            
            try:
                transcription = transcribe_audio(wav_file)
                is_match = exact_match(transcription, gold)
                print(f"  ✓ Transcription: {transcription}")
                print(f"  {'✓' if is_match else '✗'} Match: {is_match}\n")
            except Exception as e:
                print(f"  ✗ Failed: {e}\n")
                transcription = "ERROR"
                is_match = False
            
            results.append({
                "filename": wav_file.name,
                "sample": sample_num,
                "noise_level": noise_level,
                "run": run,
                "gold_standard": gold,
                "transcription": transcription,
                "exact_match": is_match
            })
            
            # Small delay to avoid overwhelming the service
            if run < runs:
                sleep(0.1)
    
    # Create DataFrame
    df = pd.DataFrame(results)
    
    # Sort by sample number, noise level, and run
    df = df.sort_values(by=["sample", "noise_level", "run"])
    
    # Save detailed results to Excel
    output_file = "transcriptions_detailed.xlsx"
    df.to_excel(output_file, index=False, engine='openpyxl')
    print(f"\n✓ Detailed results saved to {output_file}")
    
    # Create aggregated statistics
    agg_stats = df.groupby(['sample', 'noise_level', 'gold_standard']).agg({
        'exact_match': ['sum', 'count', 'mean'],
        'transcription': lambda x: ' | '.join(x)
    }).reset_index()
    agg_stats.columns = ['sample', 'noise_level', 'gold_standard', 'matches', 'total_runs', 'accuracy', 'all_transcriptions']
    agg_stats['accuracy'] = (agg_stats['accuracy'] * 100).round(2)
    
    output_agg_file = "transcriptions_aggregated.xlsx"
    agg_stats.to_excel(output_agg_file, index=False, engine='openpyxl')
    print(f"✓ Aggregated results saved to {output_agg_file}")
    
    # Print overall statistics
    total = len(df)
    matches = df['exact_match'].sum()
    accuracy = (matches / total) * 100 if total > 0 else 0
    
    print(f"\n{'='*60}")
    print(f"OVERALL STATISTICS (across {runs} runs)")
    print(f"{'='*60}")
    print(f"  Total transcriptions: {total}")
    print(f"  Exact matches: {matches}")
    print(f"  Overall accuracy: {accuracy:.2f}%")
    
    # Accuracy by noise level
    print(f"\n{'='*60}")
    print(f"ACCURACY BY NOISE LEVEL")
    print(f"{'='*60}")
    noise_stats = df.groupby('noise_level').agg({
        'exact_match': ['sum', 'count', lambda x: (x.sum() / len(x) * 100)]
    }).round(2)
    noise_stats.columns = ['Matches', 'Total', 'Accuracy (%)']
    print(noise_stats)
    
    # Accuracy by sample
    print(f"\n{'='*60}")
    print(f"ACCURACY BY SAMPLE")
    print(f"{'='*60}")
    sample_stats = df.groupby('sample').agg({
        'exact_match': ['sum', 'count', lambda x: (x.sum() / len(x) * 100)]
    }).round(2)
    sample_stats.columns = ['Matches', 'Total', 'Accuracy (%)']
    print(sample_stats)
    
    # Consistency analysis (samples that got different results across runs)
    print(f"\n{'='*60}")
    print(f"CONSISTENCY ANALYSIS")
    print(f"{'='*60}")
    consistency = agg_stats[agg_stats['matches'].between(1, runs-1)]
    if len(consistency) > 0:
        print(f"Found {len(consistency)} sample/noise combinations with inconsistent results:")
        print(consistency[['sample', 'noise_level', 'matches', 'total_runs', 'accuracy']])
    else:
        print("All samples produced consistent results across runs!")
    
    return df, agg_stats

if __name__ == "__main__":
    df, agg_stats = transcribe_folder("test_samples", "gold_standard.json", runs=3)