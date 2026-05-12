# Prediksi Jumlah Pengangguran di Sulawesi Utara Menggunakan LSTM

Website ini dibuat untuk memprediksi jumlah pengangguran di Sulawesi Utara menggunakan algoritma **Long Short-Term Memory (LSTM)**.

Aplikasi memiliki dua bagian utama:

1. **User Page**
2. **Admin Page**

User dapat melihat dataset, hasil prediksi, evaluasi model, grafik prediksi, dan melakukan simulasi prediksi menggunakan dataset sendiri.

Admin dapat login, upload dataset, melakukan validasi dataset, menjadikan dataset sebagai dataset aktif, menjalankan training model LSTM, melihat evaluasi, dan mempublish hasil prediksi ke halaman user.

---

## Fitur Utama

### User Page

- Beranda informasi sistem
- Melihat dataset yang dipublish admin
- Melihat hasil prediksi resmi
- Melihat evaluasi MAE, RMSE, dan MAPE
- Melihat grafik aktual vs prediksi
- Melihat prediksi masa depan
- Melihat tabel hasil prediksi
- Download hasil prediksi dalam format CSV
- Melakukan simulasi prediksi menggunakan dataset sendiri

### Admin Page

- Login admin
- Upload dataset Excel/CSV
- Validasi dataset
- Menjadikan dataset sebagai dataset aktif
- Publish dataset ke halaman user
- Training model LSTM
- Melihat hasil evaluasi model
- Melihat grafik hasil training
- Melihat hasil prediksi masa depan
- Melihat riwayat training model
- Publish hasil training ke halaman user

---

## Metode Model

Model mengikuti alur penelitian berikut:

```txt
Dataset historis
↓
Validasi dataset
↓
Normalisasi menggunakan MinMaxScaler
↓
Seleksi fitur berdasarkan korelasi
↓
Pembentukan sequence LSTM
↓
Split data train dan test
↓
Training model LSTM
↓
Evaluasi MAE, RMSE, MAPE
↓
Prediksi data test
↓
Prediksi jumlah pengangguran masa depan