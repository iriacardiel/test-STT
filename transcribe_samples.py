import requests
import pandas as pd
from pathlib import Path
import re

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
    # Pattern: sample_<number>_noise_<level>.wav
    match = re.match(r'sample_(\d+)_noise_(\d+)\.wav', filename)
    if match:
        sample_num = int(match.group(1))
        noise_level = int(match.group(2))
        return sample_num, noise_level
    return None, None

def transcribe_folder(folder_path="test_samples"):
    """Transcribe all .wav files and create Excel report."""
    folder = Path(folder_path)
    wav_files = sorted(folder.glob("*.wav"))
    
    if not wav_files:
        print(f"No .wav files found in {folder_path}/")
        return
    
    print(f"Found {len(wav_files)} .wav files\n")
    
    results = []
    
    for i, wav_file in enumerate(wav_files, 1):
        sample_num, noise_level = parse_filename(wav_file.name)
        
        print(f"[{i}/{len(wav_files)}] Processing: {wav_file.name}")
        
        try:
            transcription = transcribe_audio(wav_file)
            print(f"  ✓ Success\n")
        except Exception as e:
            print(f"  ✗ Failed: {e}\n")
            transcription = "ERROR"
        
        results.append({
            "filename": wav_file.name,
            "sample": sample_num,
            "noise_level": noise_level,
            "transcription": transcription
        })
    
    # Create DataFrame and save to Excel
    df = pd.DataFrame(results)
    
    # Sort by sample number and noise level
    df = df.sort_values(by=["sample", "noise_level"])
    
    output_file = "transcriptions.xlsx"
    df.to_excel(output_file, index=False, engine='openpyxl')
    
    print(f"\n✓ Results saved to {output_file}")
    print(f"Total files processed: {len(results)}")
    
    return df

if __name__ == "__main__":
    df = transcribe_folder("test_samples")
    
    # Print summary
    print("\nSummary:")
    print(f"  Samples: {df['sample'].nunique()}")
    print(f"  Noise levels: {sorted(df['noise_level'].unique())}")
    print(f"  Total transcriptions: {len(df)}")