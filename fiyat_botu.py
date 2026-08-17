name: Fiyat Takip Otomasyonu

on:
  schedule:
    - cron: '0 9 * * *' # Her gün sabah saat 09.00'da çalışır
  workflow_dispatch: # İstersek elle de tetikleyebilelim diye

jobs:
  run-bot:
    runs-on: ubuntu-latest
    steps:
      - name: Depoyu Indir
        uses: actions/checkout@v3

      - name: Python Kurulumu
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Botu Calistir
        run: python fiyat_botu.py

      - name: Sonuclari Kaydet ve Guncelle
        run: |
          git config --global user.name "Fiyat Botu"
          git config --global user.email "bot@users.noreply.github.com"
          git add fiyatlar.txt
          git commit -m "Otomatik fiyat kontrolu yapildi" || exit 0
          git push
