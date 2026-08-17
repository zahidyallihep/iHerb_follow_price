from datetime import datetime
import json
import os
import requests
from bs4 import BeautifulSoup

# TAKİP EDİLECEK ÜRÜNLER LİSTESİ
# Linkleri buraya eklemen yeterli. İsim ve URL'yi düzgün girmen önemli.
urunler = [
    {
        "isim": "California Gold Nutrition C Vitamini",
        "url": "https://tr.iherb.com/pr/california-gold-nutrition-gold-c-sw-1-000-mg-60-veggie-capsules/61864",
    },
    # Yeni ürün eklemek istersen şu formatta ekle:
    # {"isim": "Ürün Adı", "url": "Link"},
]

hafiza_dosyasi = "urun_durum.json"
fiyat_dosyasi = "fiyatlar.txt"

def iherb_fiyat_cek(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            # Fiyatı iHerb meta etiketinden çekiyoruz
            meta_fiyat = soup.find("meta", property="og:price:amount")
            if meta_fiyat and meta_fiyat.get("content"):
                return float(meta_fiyat["content"])
    except Exception as e:
        print(f"Hata oluştu ({url}): {e}")
    return None

# 1. Hafızayı yükle
gecmis_veriler = {}
if os.path.exists(hafiza_dosyasi):
    try:
        with open(hafiza_dosyasi, "r", encoding="utf-8") as hf:
            gecmis_veriler = json.load(hf)
    except:
        gecmis_veriler = {}

bugun_tarih = datetime.now().strftime("%d.%m.%Y %H:%M")
bugun_format_tarih = datetime.now().strftime("%d.%m.%Y")

print("Analiz başlatıldı...")
yeni_indirimler = []

# 2. Ürünleri kontrol et
for urun in urunler:
    isim = urun["isim"]
    url = urun["url"]
    
    print(f"Kontrol ediliyor: {isim}...")
    guncel_fiyat = iherb_fiyat_cek(url)

    if guncel_fiyat is None:
        print("-> Fiyat çekilemedi.")
        continue

    print(f"-> Güncel Fiyat: {guncel_fiyat} TL")

    # Kıyaslama yap
    if isim in gecmis_veriler:
        eski_veri = gecmis_veriler[isim]
        eski_fiyat = eski_veri["fiyat"]
        eski_tarih = eski_veri["tarih"]

        if guncel_fiyat < eski_fiyat:
            fark = eski_fiyat - guncel_fiyat
            kar_yuzdesi = (fark / eski_fiyat) * 100
            mesaj = f"🔥 İNDİRİM: {eski_tarih} tarihinde {eski_fiyat} lira olan {isim} şimdi {guncel_fiyat} lira. %{kar_yuzdesi:.2f} kar fırsatı! ({bugun_tarih})"
            yeni_indirimler.append(mesaj)
            print(f"✅ İndirim yakalandı: {mesaj}")
            # Düşüşü yeni baz olarak kaydet
            gecmis_veriler[isim] = {"fiyat": guncel_fiyat, "tarih": bugun_format_tarih}
        elif guncel_fiyat > eski_fiyat:
            print("📈 Fiyat yükseldi, yeni baz belirlendi.")
            gecmis_veriler[isim] = {"fiyat": guncel_fiyat, "tarih": bugun_format_tarih}
    else:
        print("📌 İlk kayıt, referans oluşturuldu.")
        gecmis_veriler[isim] = {"fiyat": guncel_fiyat, "tarih": bugun_format_tarih}

# 3. İndirimleri dosyaya ekle
if yeni_indirimler:
    with open(fiyat_dosyasi, "a", encoding="utf-8") as f:
        for indirim in yeni_indirimler:
            f.write(indirim + "\n")

# 4. JSON hafızasını güncelle
with open(hafiza_dosyasi, "w", encoding="utf-8") as hf:
    json.dump(gecmis_veriler, hf, ensure_ascii=False, indent=4)

print("İşlem tamamlandı.")
