from datetime import datetime
import json
import os
import requests
from bs4 import BeautifulSoup

# TAKİP EDİLECEK ÜRÜNLER LİSTESİ
urunler = [
    {
        "isim": "iHerb C Vitamini Örneği",
        "url": "https://tr.iherb.com/pr/california-gold-nutrition-gold-c-sw-1-000-mg-60-veggie-capsules/61864",
    },
    # Buraya alt alta yeni ürünler ekleyebilirsiniz:
    # {"isim": "Ürün 2", "url": "LINK"}
]

hafiza_dosyasi = "urun_durum.json"
fiyat_dosyasi = "fiyatlar.txt"


def iherb_fiyat_cek(url):
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
          " like Gecko) Chrome/120.0.0.0 Safari/537.36"
      ),
      "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
  }
  try:
    response = requests.get(url, headers=headers, timeout=15)
    if response.status_code == 200:
      soup = BeautifulSoup(response.text, "html.parser")
      meta_fiyat = soup.find("meta", property="og:price:amount")
      if meta_fiyat and meta_fiyat.get("content"):
        return float(meta_fiyat["content"])
  except Exception as e:
    print(f"Hata oluştu ({url}): {e}")
  return None


# 1. Daha önceki kayıtlı fiyat hafızasını yükle (Eğer varsa)
gecmis_veriler = {}
if os.path.exists(hafiza_dosyasi):
  try:
    with open(hafiza_dosyasi, "r", encoding="utf-8") as hf:
      gecmis_veriler = json.load(hf)
  except:
    gecmis_veriler = {}

bugun_tarih = datetime.now().strftime("%d.%m.%Y %H:%M")
bugun_format_tarih = datetime.now().strftime("%d.%m.%Y")

print("Dinamik fiyat takip analizi başlatıldı...")
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

  # Eğer bu ürün daha önce hafızamıza kaydedilmişse kıyasla
  if isim in gecmis_veriler:
    eski_veri = gecmis_veriler[isim]
    eski_fiyat = eski_veri["fiyat"]
    eski_tarih = eski_veri["tarih"]

    # Eğer güncel fiyat, eski fiyattan DÜŞÜKSE (İndirim var!)
    if guncel_fiyat < eski_fiyat:
      fark = eski_fiyat - guncel_fiyat
      kar_yuzdesi = (fark / eski_fiyat) * 100

      # İstediğiniz formatta mesaj oluşturma
      mesaj = (
          f"🔥 İNDİRİM: {eski_tarih} tarihinde {eski_fiyat} lira olan {isim}"
          f" şimdi {guncel_fiyat} lira. %{kar_yuzdesi:.2f} kar fırsatı!"
          f" ({bugun_tarih})\n"
      )
      yeni_indirimler.append(mesaj)
      print(f"✅ İndirim yakalandı: {mesaj}")

      # Fiyat düştüğü için yeni yüksek referansı güncelliyoruz ki sonraki düşüşte baz alalım
      gecmis_veriler[isim] = {"fiyat": guncel_fiyat, "tarih": bugun_format_tarih}

    elif guncel_fiyat > eski_fiyat:
      # Fiyat yükseldiyse yeni referansı güncelleriz (böylece gelecekteki düşüşü bundan hesaplar)
      print(
          f"📈 Fiyat yükseldi ({eski_fiyat} -> {guncel_fiyat}), referans"
          " güncellendi."
      )
      gecmis_veriler[isim] = {"fiyat": guncel_fiyat, "tarih": bugun_format_tarih}
    else:
      print("➖ Fiyatta değişim yok.")

  else:
    # Ürün ilk defa taranıyorsa hafızaya ilk fiyatı olarak kaydediyoruz
    print("📌 İlk kez kaydedildi, referans oluşturuldu.")
    gecmis_veriler[isim] = {"fiyat": guncel_fiyat, "tarih": bugun_format_tarih}

# 3. Yakalanan indirimleri txt dosyasına alt alta ekle
if yeni_indirimler:
  with open(fiyat_dosyasi, "a", encoding="utf-8") as f:
    for indirim in yeni_indirimler:
      f.write(indirim + "\n")

# 4. Güncel hafızayı JSON dosyasına kaydet ki yarınki kıyaslama için kalsın
with open(hafiza_dosyasi, "w", encoding="utf-8") as hf:
  json.dump(gecmis_veriler, hf, ensure_ascii=False, indent=4)

print("İşlem tamamlandı.")
