# Cute Timer Desktop

## Pasang sekali

```powershell
powershell -ExecutionPolicy Bypass -File .\front-end\install.ps1
```

Buka melalui shortcut **Cute Timer** di Desktop. Alternatifnya, buka terminal baru lalu jalankan:

```powershell
timer
```

Kontrol keyboard: `Space` mulai, `P` jeda, `R` reset, `A` membuka menu tambah waktu, `1/2/3` menambah 10/15/20 menit, `M` membuka/menutup mode Micro, dan `Q` keluar.

## Ukuran tampilan

- **Full:** 900×620 px, seluruh kontrol timer.
- **Compact:** 480×105 px, waktu dan animasi kucing; selalu di atas aplikasi lain.
- **Micro:** langsung menjadi 240×52 logical px (sekitar 480×104 px pada scaling Windows 200%), mengikuti ukuran mini-player Spotify pada layar referensi; tanpa title bar, selalu di atas aplikasi lain, dan menampilkan kucing berlari di hamster wheel. Tarik ikon grip untuk memindahkan; tekan `M` atau klik `×` untuk kembali ke Compact.

Timer tetap berjalan saat berpindah mode. Klik **COMPACT** atau **MICRO** dari tampilan Full; membesarkan jendela Compact akan mengembalikannya ke Full.

Semua mode menampilkan `MM:SS` sampai `59:59`, lalu otomatis memakai `HH:MM:SS` mulai `01:00:00`. Di Compact dan Micro, double-click timer bergantian menjeda/melanjutkan dengan animasi `STOP`/`PLAY`; saat jeda kucing berlari di wheel. Triple-click sisi kiri mengurangi 10 menit dan sisi kanan menambah 10 menit dengan animasi `−10`/`+10`, tanpa mengubah status berjalan.

Pemeriksaan logika:

```powershell
python .\front-end\app.py --self-test
python .\front-end\app.py --ui-self-test
```
