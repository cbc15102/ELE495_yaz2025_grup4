from openai import OpenAI
from pydantic import BaseModel, ValidationError
from typing import Optional
import json
import os

# OpenAI istemcisi
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", "sk-xxxxxxxxxxxxxxxxxxxxxxxx"))

# --- Pydantic modeli ---
class RobotCommand(BaseModel):
    action: Optional[str]       = None  # e.g. "move_forward", "turn", "move_until_obstacle", "wait", "stop"
    distance_m: Optional[float] = None
    direction: Optional[str]    = None  # "left" veya "right"
    angle_deg: Optional[float]  = None  # derece ile dönmeler için
    duration_s: Optional[float] = None
    then: Optional[str]         = None
    error: Optional[str]        = None

# --- Güncellenmiş prompt açıklaması ---
COMMAND_GUIDE = """
Sen 4 tekerli bir kara robotusun. Sana doğal dilde komutlar verilecek ve bunları tek bir JSON çıktısına çevireceksin.

Desteklenen eylemler:
- Belirli bir mesafe ileri veya geri gitmek (örnek: "3 metre ileri git")
- Belirli bir süre boyunca hareket etmek (örnek: "3 saniye ileri git" → bu, 3 saniye boyunca ileri gitmek anlamına gelir. 'wait' değil!)
- Sağa veya sola dönmek (örnek: "sağa dön" → yön ve varsayılan 90 derece ile)
- Derece ile dönmek (örnek: "90 derece sola dön", "180 derece sağa dön")
- Engel görene kadar ilerlemek (örnek: "engel görene kadar ilerle")
- Durmak (örnek: "dur")
- Belirli bir süre beklemek (örnek: "5 saniye bekle")
- Zincirleme komutlar (örnek: "5 metre ileri git sonra 90 derece sola dön sonra 2 saniye bekle")

Notlar:
- Eğer kullanıcı "3 saniye ileri git" derse, bunu {"action": "move_forward", "duration_s": 3} olarak döndür.
- Tüm dönme işlemlerinde "angle_deg" alanı kullanılmalı (örnek: 90 derece).
- Her komutu ayrı bir JSON objesi olarak ve sırayla döndür. Liste formatında ver.

Geçerli JSON örnekleri:
{
  "action": "move_forward",
  "distance_m": 3
}
{
  "action": "move_forward",
  "duration_s": 3
}
{
  "action": "turn",
  "direction": "left",
  "angle_deg": 90
}
{
  "action": "move_until_obstacle"
}

Desteklenmeyen bir komut gelirse, şu yapıda açıklayıcı hata döndür:
{"error": "<neden yapılamadığı>"}

Örnek:
- "uç" → {"error": "Uçamam çünkü uçma yeteneğim yok."}
- "kamerayı aç" → {"error": "Kamera açamam çünkü kameram yok."}

SADECE JSON döndür. Başka metin veya açıklama ekleme.
"""

def komutu_jsona_cevir(komut: str) -> dict:
    prompt = COMMAND_GUIDE + f"\nKomut: {komut}\nÇıktı:"
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Sen bir robot komut çeviricisisin."},
            {"role": "user",   "content": prompt}
        ],
        temperature=0.2
    )
    json_str = response.choices[0].message.content
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        return {"error": "Geçersiz JSON çıktı"}

def komutu_dogrula(json_data: dict, dosya_yolu="komut_ciktisi.txt"):
    try:
        if isinstance(json_data, list):
            # Çoklu komut listesi varsa hepsini kontrol et
            dogru_komutlar = []
            for item in json_data:
                komut = RobotCommand(**item)
                if komut.error:
                    print(f"🚫 Robot bunu yapamaz: {komut.error}")
                else:
                    dogru_komutlar.append(komut.model_dump(exclude_none=True))
            if dogru_komutlar:
                print("✅ Geçerli komutlar alındı:")
                print(json.dumps(dogru_komutlar, indent=2, ensure_ascii=False))
                with open(dosya_yolu, "w", encoding="utf-8") as f:
                    f.write(json.dumps(dogru_komutlar, indent=2, ensure_ascii=False))
        else:
            komut = RobotCommand(**json_data)
            if komut.error:
                print(f"🚫 Robot bunu yapamaz: {komut.error}")
                with open(dosya_yolu, "w", encoding="utf-8") as f:
                    f.write(json.dumps({"error": komut.error}, indent=2, ensure_ascii=False))
            else:
                print("✅ Geçerli komut alındı:")
                veri = komut.model_dump(exclude_none=True)
                print(json.dumps(veri, indent=2, ensure_ascii=False))
                with open(dosya_yolu, "w", encoding="utf-8") as f:
                    f.write(json.dumps(veri, indent=2, ensure_ascii=False))
    except ValidationError as e:
        print("⛔ JSON doğrulanamadı:\n", e)
        with open(dosya_yolu, "w", encoding="utf-8") as f:
            f.write(json.dumps({"error": "Doğrulama hatası"}, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    while True:
        k = input("\n💬 Robot komutu gir (çıkmak için 'q'): ")
        if k.lower() == 'q':
            break
        jd = komutu_jsona_cevir(k)
        komutu_dogrula(jd, dosya_yolu="komut_ciktisi.txt")
