from datetime import datetime
import json
import os
import requests
from bs4 import BeautifulSoup

urunler = [
    {
        "isim": "California Gold Nutrition C Vitamini",
        "url": (
            "https://tr.iherb.com/pr/california-gold-nutrition-gold-c-sw-1-000-mg-60-veggie-capsules/61864"
        ),
    }
]

hafiza_dosyasi = "urun_durum.json"
fiyat_dosyasi = "fiyatlar.txt"


def iherb_fiyat_cek(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9", # İngilizce diline zorlayalım ki nokta(.) formatında gelsin
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            # Hem meta etiketini dene hem de sitedeki ana fiyat alanını
            meta_fiyat = soup.find("meta", property="og:price:amount")
            if meta_fiyat and meta_fiyat.get("content"):
                return float(meta_fiyat["content"])
            
            # Eğer meta boşsa fiyat alanını bul ve virgülü noktaya çevir
            fiyat_str = soup.find("span", {"data-test-id": "pricing-curated-price"}).text
            # "282,77 ₺" gibi bir metni "282.77" sayısına çeviriyoruz
            fiyat_temiz = fiyat_str.replace("₺", "").replace(".", "").replace(",", ".").strip()
            return float(fiyat_temiz)
    except Exception as e:
        print(f"Fiyat çekme hatası: {e}")
    return None

# Hafızayı oku
gecmis = {}
if os.path.exists(hafiza_dosyasi):
  try:
    with open(hafiza_dosyasi, "r", encoding="utf-8") as f:
      gecmis = json.load(f)
  except:
    gecmis = {}

bugun = datetime.now().strftime("%d.%m.%Y")
yeni_rapor = []

for urun in urunler:
  fiyat = iherb_fiyat_cek(urun["url"])
  if fiyat is not None:
    isim = urun["isim"]
    if isim in gecmis:
      eski_fiyat = gecmis[isim]["fiyat"]
      eski_tarih = gecmis[isim]["tarih"]
      if fiyat < eski_fiyat:
        kar = ((eski_fiyat - fiyat) / eski_fiyat) * 100
        yeni_rapor.append(
            f"🔥 İNDİRİM: {eski_tarih} tarihinde {eski_fiyat} TL olan {isim}"
            f" şimdi {fiyat} TL. %{kar:.2f} kar fırsatı!"
        )
    gecmis[isim] = {"fiyat": fiyat, "tarih": bugun}
  else:
    print(f"{urun['isim']} için fiyat çekilemedi.")

# Dosyaları yaz
with open(fiyat_dosyasi, "w", encoding="utf-8") as f:
  if yeni_rapor:
    f.write("\n".join(yeni_rapor) + "\n")
  else:
    f.write("Şu an için fiyatı düşen ürün bulunmuyor.\n")

with open(hafiza_dosyasi, "w", encoding="utf-8") as f:
  json.dump(gecmis, f, ensure_ascii=False, indent=4)

print("İşlem başarıyla tamamlandı.")
