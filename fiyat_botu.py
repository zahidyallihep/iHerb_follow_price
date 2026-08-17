from datetime import datetime
from zoneinfo import ZoneInfo
import json
import os
import re

import requests
from bs4 import BeautifulSoup


# ============================================================
# ÜRÜNLER
# ============================================================

urunler = [
    {
        "isim": "California Gold Nutrition C Vitamini",
        "url": (
            "https://tr.iherb.com/pr/"
            "california-gold-nutrition-gold-c-sw-1-000-mg-"
            "60-veggie-capsules/61864"
        ),
    }
]


# ============================================================
# DOSYALAR
# ============================================================

hafiza_dosyasi = "urun_durum.json"
fiyat_dosyasi = "fiyatlar.txt"


# ============================================================
# TARİH
# ============================================================

istanbul = ZoneInfo("Europe/Istanbul")
bugun = datetime.now(istanbul).strftime("%d.%m.%Y")


# ============================================================
# FİYAT TEMİZLE
# ============================================================

def fiyat_sayiya_cevir(value):

    if value is None:
        return None

    text = str(value).strip()

    text = (
        text
        .replace("TRY", "")
        .replace("TL", "")
        .replace("₺", "")
        .replace("\xa0", " ")
        .strip()
    )

    match = re.search(
        r"\d[\d\s\.,]*",
        text
    )

    if not match:
        return None

    temiz = (
        match.group(0)
        .replace(" ", "")
    )

    # Türkçe biçim:
    # 1.299,90 -> 1299.90
    if "," in temiz:

        temiz = (
            temiz
            .replace(".", "")
            .replace(",", ".")
        )

    else:

        # Birden fazla nokta varsa:
        # 1.299.90 vb. yapıları normalize et.
        if temiz.count(".") > 1:

            son_nokta = temiz.rfind(".")

            temiz = (
                temiz[:son_nokta].replace(".", "")
                + temiz[son_nokta:]
            )

    try:
        return round(float(temiz), 2)

    except ValueError:
        return None


# ============================================================
# iHERB FİYAT ÇEK
# ============================================================

def iherb_fiyat_cek(url):

    headers = {
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/131.0.0.0 "
            "Safari/537.36"
        ),

        "Accept": (
            "text/html,"
            "application/xhtml+xml,"
            "application/xml;q=0.9,"
            "image/avif,"
            "image/webp,"
            "*/*;q=0.8"
        ),

        "Accept-Language":
            "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",

        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Upgrade-Insecure-Requests": "1",
    }

    try:

        response = requests.get(
            url,
            headers=headers,
            timeout=30
        )

        # ====================================================
        # DEBUG
        # ====================================================

        print("HTTP:", response.status_code)
        print("FINAL URL:", response.url)
        print("HTML LENGTH:", len(response.text))
        print(
            "CONTENT TYPE:",
            response.headers.get("content-type")
        )
        print(
            "SERVER:",
            response.headers.get("server")
        )

        if response.status_code != 200:

            print(
                "❌ HTTP isteği başarısız:",
                response.status_code
            )

            return None


        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )


        # ====================================================
        # 1. META FİYAT
        # ====================================================

        meta_arama = [
            (
                "meta",
                {
                    "property":
                        "product:price:amount"
                }
            ),
            (
                "meta",
                {
                    "property":
                        "og:price:amount"
                }
            ),
            (
                "meta",
                {
                    "itemprop":
                        "price"
                }
            ),
        ]

        for tag_name, attrs in meta_arama:

            element = soup.find(
                tag_name,
                attrs
            )

            if not element:
                continue

            value = (
                element.get("content")
                or
                element.get("value")
            )

            fiyat = fiyat_sayiya_cevir(
                value
            )

            if fiyat is not None:

                print(
                    "✅ Meta fiyat bulundu:",
                    fiyat
                )

                return fiyat


        # ====================================================
        # 2. JSON-LD
        # ====================================================

        for script in soup.find_all(
            "script",
            type="application/ld+json"
        ):

            raw = script.string

            if not raw:
                continue

            try:
                data = json.loads(raw)

            except Exception:
                continue


            objects = (
                data
                if isinstance(data, list)
                else [data]
            )

            for obj in objects:

                if not isinstance(
                    obj,
                    dict
                ):
                    continue

                offers = obj.get(
                    "offers"
                )

                if isinstance(
                    offers,
                    dict
                ):

                    fiyat = fiyat_sayiya_cevir(
                        offers.get("price")
                    )

                    if fiyat is not None:

                        print(
                            "✅ JSON-LD fiyat bulundu:",
                            fiyat
                        )

                        return fiyat


                elif isinstance(
                    offers,
                    list
                ):

                    for offer in offers:

                        if not isinstance(
                            offer,
                            dict
                        ):
                            continue

                        fiyat = fiyat_sayiya_cevir(
                            offer.get("price")
                        )

                        if fiyat is not None:

                            print(
                                "✅ JSON-LD fiyat bulundu:",
                                fiyat
                            )

                            return fiyat


        # ====================================================
        # 3. BİLİNEN SELECTOR'LAR
        # ====================================================

        selectors = [
            '[data-test-id="pricing-curated-price"]',
            '[data-test-id="product-price"]',
            '.price',
            '.product-price',
            '.price-text',
            '[itemprop="price"]',
        ]

        for selector in selectors:

            element = soup.select_one(
                selector
            )

            if not element:
                continue

            value = (
                element.get("content")
                or
                element.get_text(
                    " ",
                    strip=True
                )
            )

            fiyat = fiyat_sayiya_cevir(
                value
            )

            if fiyat is not None:

                print(
                    f"✅ Selector fiyat bulundu "
                    f"({selector}):",
                    fiyat
                )

                return fiyat


        # ====================================================
        # 4. HTML İÇİNDE TL / ₺ ARA
        # ====================================================

        fiyat_adaylari = []

        for element in soup.find_all(
            ["span", "div"]
        ):

            text = element.get_text(
                " ",
                strip=True
            )

            if (
                "₺" not in text
                and "TL" not in text
            ):
                continue

            fiyat = fiyat_sayiya_cevir(
                text
            )

            if (
                fiyat is not None
                and fiyat > 0
            ):
                fiyat_adaylari.append(
                    fiyat
                )


        if fiyat_adaylari:

            print(
                "🧪 Fiyat adayları:",
                fiyat_adaylari[:10]
            )

            return fiyat_adaylari[0]


        # ====================================================
        # FİYAT BULUNAMADI → DEBUG HTML KAYDET
        # ====================================================

        print(
            "❌ Sayfada fiyat bulunamadı."
        )

        print(
            "HTML başlangıcı:"
        )

        print(
            response.text[:2000]
        )

        with open(
            "debug_iherb.html",
            "w",
            encoding="utf-8"
        ) as f:
            f.write(
                response.text
            )

        print(
            "🧪 debug_iherb.html kaydedildi."
        )


    except Exception as e:

        print(
            "❌ Fiyat çekme hatası:",
            repr(e)
        )


    return None


# ============================================================
# FİYAT FORMATLA
# ============================================================

def fiyat_formatla(fiyat):

    fiyat = float(fiyat)

    if fiyat.is_integer():
        return str(
            int(fiyat)
        )

    return (
        f"{fiyat:.2f}"
        .replace(".", ",")
    )


# ============================================================
# HAFIZAYI OKU
# ============================================================

gecmis = {}

if os.path.exists(
    hafiza_dosyasi
):

    try:

        with open(
            hafiza_dosyasi,
            "r",
            encoding="utf-8"
        ) as f:

            gecmis = json.load(
                f
            )

    except Exception as e:

        print(
            "⚠️ Hafıza okunamadı:",
            e
        )

        gecmis = {}


# ============================================================
# ÜRÜNLERİ KONTROL ET
# ============================================================

yeni_rapor = []


for urun in urunler:

    isim = urun["isim"]

    print()
    print(
        "================================"
    )

    print(
        "🔍 Kontrol ediliyor:",
        isim
    )


    fiyat = iherb_fiyat_cek(
        urun["url"]
    )


    if fiyat is None:

        print(
            f"❌ {isim} için "
            "fiyat çekilemedi."
        )

        # Fiyat çekilemediyse önceki
        # kayıt korunur.
        continue


    print(
        "💰 Güncel fiyat:",
        fiyat
    )


    # ========================================================
    # ÖNCEKİ FİYATLA KARŞILAŞTIR
    # ========================================================

    if isim in gecmis:

        eski_fiyat = float(
            gecmis[isim]["fiyat"]
        )

        eski_tarih = gecmis[
            isim
        ]["tarih"]


        print(
            "📌 Önceki fiyat:",
            eski_fiyat,
            "-",
            eski_tarih
        )


        if fiyat < eski_fiyat:

            indirim_orani = (
                (
                    eski_fiyat
                    - fiyat
                )
                / eski_fiyat
            ) * 100


            mesaj = (
                f"🔥 İNDİRİM: "
                f"{eski_tarih} tarihinde "
                f"{fiyat_formatla(eski_fiyat)} lira olan "
                f"{isim} şimdi "
                f"{fiyat_formatla(fiyat)} lira. "
                f"%{indirim_orani:.2f} kar fırsatı!"
            )


            yeni_rapor.append(
                mesaj
            )


            print(
                "🔥 İNDİRİM BULUNDU!"
            )

            print(
                mesaj
            )


        elif fiyat > eski_fiyat:

            print(
                "📈 Fiyat yükseldi:",
                fiyat_formatla(eski_fiyat),
                "→",
                fiyat_formatla(fiyat)
            )


        else:

            print(
                "➖ Fiyat değişmedi."
            )


    else:

        print(
            "ℹ️ İlk fiyat kaydı oluşturuluyor."
        )


    # ========================================================
    # SON BAŞARILI FİYAT BİR SONRAKİ GÜNÜN REFERANSI
    # ========================================================

    gecmis[isim] = {
        "fiyat": fiyat,
        "tarih": bugun
    }


# ============================================================
# FİYATLAR.TXT
# ============================================================

with open(
    fiyat_dosyasi,
    "w",
    encoding="utf-8"
) as f:

    if yeni_rapor:

        f.write(
            "\n\n".join(
                yeni_rapor
            )
        )

        f.write("\n")

    else:

        f.write(
            "Şu an için fiyatı düşen ürün bulunmuyor.\n"
        )


# ============================================================
# HAFIZA DOSYASI
# ============================================================

with open(
    hafiza_dosyasi,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        gecmis,
        f,
        ensure_ascii=False,
        indent=4
    )


print()
print(
    "✅ İşlem başarıyla tamamlandı."
)
