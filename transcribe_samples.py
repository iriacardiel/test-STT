import requests
import pandas as pd
from pathlib import Path
import re
import json

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
    """Extract sample number and SNRdb from filename."""
    match = re.match(r'sample_(\d+)_noise_(\d+)\.wav', filename)
    if match:
        sample_num = int(match.group(1))
        sample_noise_rate = int(match.group(2))
        return sample_num, sample_noise_rate
    return None, None

def exact_match(transcription, gold_standard):
    """Check if transcription matches gold standard (case-insensitive)."""
    if transcription == "ERROR" or gold_standard is None:
        return False
    return transcription.lower().strip().strip(".") == gold_standard.lower().strip().strip(".")

def transcribe_folder(folder_path="test_samples", gold_standard_path="gold_standard.json"):
    """Transcribe all .wav files and create Excel report with gold standard comparison."""
    # Load gold standard
    GOLD_STANDARD = load_gold_standard(gold_standard_path)
    
    if not GOLD_STANDARD:
        print("Cannot proceed without gold standard.")
        return
    
    print(f"✓ Loaded {len(GOLD_STANDARD)} gold standard utterances\n")
    
    folder = Path(folder_path)
    wav_files = sorted(folder.glob("*.wav"))
    
    if not wav_files:
        print(f"No .wav files found in {folder_path}/")
        return
    
    print(f"Found {len(wav_files)} .wav files\n")
    
    results = []
    
    for i, wav_file in enumerate(wav_files, 1):
        sample_num, sample_noise_rate = parse_filename(wav_file.name)
        gold = GOLD_STANDARD.get(sample_num, "")
        
        print(f"[{i}/{len(wav_files)}] Processing: {wav_file.name}")
        
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
            "sample_noise_rate": sample_noise_rate,
            "gold_standard": gold,
            "transcription": transcription,
            "exact_match": is_match
        })
    
    # Create DataFrame
    df = pd.DataFrame(results)
    
    # Sort by sample number and noise level
    df = df.sort_values(by=["sample", "sample_noise_rate"])
    
    # Save to Excel
    output_file = "transcriptions_with_gold_standard.xlsx"
    df.to_excel(output_file, index=False, engine='openpyxl')
    
    print(f"\n✓ Results saved to {output_file}")
    
    # Print statistics
    total = len(df)
    matches = df['exact_match'].sum()
    accuracy = (matches / total) * 100 if total > 0 else 0
    
    print(f"\nOverall Statistics:")
    print(f"  Total transcriptions: {total}")
    print(f"  Exact matches: {matches}")
    print(f"  Accuracy: {accuracy:.2f}%")
    
    # Accuracy by noise level
    print(f"\nAccuracy by Noise Level:")
    noise_stats = df.groupby('sample_noise_rate').agg({
        'exact_match': ['sum', 'count', lambda x: (x.sum() / len(x) * 100)]
    }).round(2)
    noise_stats.columns = ['Matches', 'Total', 'Accuracy (%)']
    print(noise_stats)
    
    return df

if __name__ == "__main__":

    # Process all files
    df = transcribe_folder("test_samples")