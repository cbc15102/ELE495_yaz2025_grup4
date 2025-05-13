import os
from speechbrain.pretrained import SpeakerRecognition

# SpeechBrain modelini yükle
model = SpeakerRecognition.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb", savedir="tmp")

# Bilinen ses örneklerinin bulunduğu klasör
known_speakers_folder = "known_speakers"
unknown_audio_path = "unknown.wav"

# Eşik değeri (0.75'ten küçükse aynı kişi denebilir)
THRESHOLD = 0.75

results = []

# Bilinen her konuşmacıyla karşılaştır
for filename in os.listdir(known_speakers_folder):
    if filename.endswith(".wav"):
        speaker_name = os.path.splitext(filename)[0]
        known_path = os.path.join(known_speakers_folder, filename)

        # Dosyaları karşılaştır
        score, prediction = model.verify_files(known_path, unknown_audio_path)

        results.append((speaker_name, score))

# Skoru en yüksek olan kişiyi bul
most_likely_speaker = max(results, key=lambda x: x[1])

# Sonucu yazdır
print("\nTahmin edilen konuşmacı:", most_likely_speaker[0])
print("Benzerlik skoru:", most_likely_speaker[1])

# Eşik değerlendir
if most_likely_speaker[1] < THRESHOLD:
    print("⚠️ Emin değilim, eşik değerinin altında.")
