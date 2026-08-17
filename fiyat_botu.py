from datetime import datetime
import os

# Takip edilecek örnek ürünler
urunler = [
    {"isim": "Örnek Kulaklık", "hedef_fiyat": 500.0, "guncel_fiyat": 450.0},
    {"isim": "Örnek Akıllı Saat", "hedef_fiyat": 2000.0, "guncel_fiyat": 2100.0},
]

dosya_adi = "fiyatlar.txt"

print("Fiyat kontrolü başlatıldı...")

# Dosya yoksa oluştur, varsa sonuna ekle
with open(dosya_adi, "a", encoding="utf-8") as f:
  for urun in urunler:
    if urun["guncel_fiyat"] < urun["hedef_fiyat"]:
      zaman = datetime.now().strftime("%Y-%m-%d %H:%M")
      mesaj = (
          f"[{zaman}] İNDİRİM! {urun['isim']} -> Hedef: {urun['hedef_fiyat']}"
          f" TL, Şu an: {urun['guncel_fiyat']} TL\n"
      )
      f.write(mesaj)
      print(f"✅ Kaydedildi: {mesaj}")

print("Kontrol tamamlandı.")
