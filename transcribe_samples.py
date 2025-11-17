import requests
from pathlib import Path

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

def transcribe_folder(folder_path="base_samples"):
    """Transcribe all .wav files in the specified folder."""
    folder = Path(folder_path)
    wav_files = list(folder.glob("*.wav"))
    
    if not wav_files:
        print(f"No .wav files found in {folder_path}/")
        return
    
    print(f"Found {len(wav_files)} .wav files\n")
    
    results = {}
    for i, wav_file in enumerate(wav_files, 1):
        print(f"[{i}/{len(wav_files)}] Transcribing: {wav_file.name}")
        try:
            transcription = transcribe_audio(wav_file)
            results[wav_file.name] = transcription
            print(f"  → {transcription}\n")
        except Exception as e:
            print(f"  ✗ Failed: {e}\n")
            results[wav_file.name] = None
    
    return results

if __name__ == "__main__":
    results = transcribe_folder("base_samples")
    
    # Optional: Save results to a file
    with open("transcriptions.txt", "w") as f:
        for filename, text in results.items():
            f.write(f"{filename}:\n{text}\n\n")
    
    print(f"Results saved to transcriptions.txt")