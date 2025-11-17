import os
from pydub import AudioSegment
import numpy as np

# -----------------------------
# Función para añadir ruido blanco
# -----------------------------
def add_white_noise(audio_path, output_path, snr_db):
    audio = AudioSegment.from_file(audio_path)
    samples = np.array(audio.get_array_of_samples()).astype(np.float32)

    # RMS del audio
    rms_audio = np.sqrt(np.mean(samples**2))

    # Convertir SNR en RMS de ruido
    rms_noise = rms_audio / (10**(snr_db / 20))

    # Generar ruido blanco
    noise = np.random.normal(0, rms_noise, samples.shape)

    # Mezclar y limitar
    noisy_samples = samples + noise
    noisy_samples = np.clip(noisy_samples, -2**15, 2**15 - 1).astype(np.int16)

    # Crear nuevo audio
    noisy_audio = audio._spawn(noisy_samples)

    # Exportar
    noisy_audio.export(output_path, format="wav")
    print(f"✔ Guardado: {output_path}")


# ---------------------------------------
# Procesar todos los audios muestraX.wav
# ---------------------------------------
input_folder = "audios"      # carpeta donde tienes tus WAVs
output_folder = "ruidos"     # carpeta de salida

os.makedirs(output_folder, exist_ok=True)

for filename in os.listdir(input_folder):
    if filename.startswith("muestra") and filename.endswith(".wav"):
        input_path = os.path.join(input_folder, filename)
        
        for snr_db in [0,5,10,15,20,25,30,35,40]: # Sound Noise Rate: 0dB ruido = señal, Casi ininteligible | 40 dB prácticamente limpio
            output_path = os.path.join(output_folder, filename.replace(".wav", f"_ruido_{snr_db}.wav"))
            add_white_noise(input_path, output_path, snr_db)

print("\n🎉 Proceso completado.")
