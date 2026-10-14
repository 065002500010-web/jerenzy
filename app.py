
import streamlit as st
import pandas as pd

# ==========================================
# 1. KONFIGURASI APLIKASI
# ==========================================

st.set_page_config(
    page_title="Automotive Production Forecasting",
    page_icon="🚗",
    layout="wide"
)

st.title("🚗 Automotive Production Forecasting System")
st.subheader("Peramalan Permintaan Produksi Suku Cadang Kendaraan")

st.write(
    """
    Aplikasi ini membantu PT AutoPart Indonesia memperkirakan
    permintaan kampas rem berdasarkan data periode sebelumnya.
    Hasil peramalan dapat digunakan sebagai bahan pertimbangan
    dalam menyusun rencana produksi.
    """
)

st.info(
    "Studi kasus dan data pada aplikasi ini bersifat simulasi "
    "untuk keperluan pembelajaran."
)

# ==========================================
# 2. DATA PERMINTAAN
# ==========================================

data_awal = pd.DataFrame({
    "Periode": [
        "Jan", "Feb", "Mar", "Apr",
        "Mei", "Jun", "Jul", "Agu",
        "Sep", "Okt", "Nov", "Des"
    ],
    "Permintaan": [
        1200, 1350, 1280, 1450,
        1500, 1420, 1600, 1550,
        1700, 1650, 1800, 1900
    ]
})

st.header("1. Data Permintaan Kampas Rem")

st.write(
    "Masukkan data permintaan kampas rem atau unggah file CSV. "
    "Nilai permintaan menunjukkan jumlah unit yang diminta pelanggan "
    "setiap periode."
)

file_upload = st.file_uploader(
    "Unggah data CSV (opsional)",
    type=["csv"]
)

if file_upload is not None:
    try:
        data = pd.read_csv(file_upload)

        if not {"Periode", "Permintaan"}.issubset(data.columns):
            st.error(
                "File CSV harus memiliki kolom "
                "'Periode' dan 'Permintaan'."
            )
            st.stop()

        data = data[["Periode", "Permintaan"]].copy()
        data["Permintaan"] = pd.to_numeric(
            data["Permintaan"], errors="coerce"
        )
        data = data.dropna().reset_index(drop=True)

    except Exception as e:
        st.error(f"File tidak dapat dibaca: {e}")
        st.stop()
else:
    data = data_awal.copy()

data = st.data_editor(
    data,
    num_rows="dynamic",
    use_container_width=True,
    hide_index=True,
    key="data_permintaan"
)

data["Periode"] = data["Periode"].astype(str).str.strip()
data["Permintaan"] = pd.to_numeric(
    data["Permintaan"], errors="coerce"
)

data = data.dropna().reset_index(drop=True)

if (
    len(data) < 5
    or (data["Permintaan"] < 0).any()
    or (data["Periode"] == "").any()
    or data["Periode"].duplicated().any()
):
    st.warning(
        "Masukkan minimal 5 periode, nama periode harus unik, "
        "dan permintaan tidak boleh negatif."
    )
    st.stop()

if not data["Permintaan"].apply(
    lambda x: float(x).is_integer()
).all():
    st.warning("Jumlah permintaan harus berupa bilangan bulat.")
    st.stop()

data["Permintaan"] = data["Permintaan"].astype(int)

aktual = data["Permintaan"].tolist()
periode = data["Periode"].tolist()
n = len(data)

# ==========================================
# 3. PILIH METODE FORECASTING
# ==========================================

st.header("2. Pengaturan Forecasting")

metode = st.selectbox(
    "Pilih metode peramalan",
    [
        "Simple Moving Average (SMA)",
        "Weighted Moving Average (WMA)",
        "Exponential Smoothing"
    ]
)

if metode == "Simple Moving Average (SMA)":
    window = st.slider(
        "Jumlah periode sebelumnya",
        min_value=2,
        max_value=min(6, n - 1),
        value=min(3, n - 1)
    )

elif metode == "Weighted Moving Average (WMA)":
    st.write(
        "Menggunakan 4 periode terakhir dengan bobot "
        "0,1; 0,2; 0,3; dan 0,4. "
        "Bobot terbesar diberikan kepada periode terbaru."
    )

else:
    alpha = st.slider(
        "Nilai alpha (α)",
        min_value=0.1,
        max_value=0.9,
        value=0.3,
        step=0.1
    )

# ==========================================
# 4. PERHITUNGAN SMA
# ==========================================

sma = [None] * n

for i in range(window if metode == "Simple Moving Average (SMA)" else 2, n):
    panjang = window if metode == "Simple Moving Average (SMA)" else 3

    sma[i] = sum(aktual[i-panjang:i]) / panjang

if metode == "Simple Moving Average (SMA)":
    prediksi_sma = sum(aktual[-window:]) / window
else:
    prediksi_sma = sum(aktual[-3:]) / 3

# ==========================================
# 5. PERHITUNGAN WMA
# ==========================================

wma = [None] * n
bobot = [0.1, 0.2, 0.3, 0.4]

for i in range(4, n):
    empat_periode = aktual[i-4:i]
    wma[i] = sum(
        empat_periode[j] * bobot[j]
        for j in range(4)
    )

prediksi_wma = sum(
    aktual[-4+j] * bobot[j]
    for j in range(4)
)

# ==========================================
# 6. PERHITUNGAN EXPONENTIAL SMOOTHING
# ==========================================

# Nilai alpha dipakai sesuai pilihan pengguna.
# Inisialisasi ramalan pertama menggunakan aktual periode pertama.

alpha_es = alpha if metode == "Exponential Smoothing" else 0.3

es = [None] * n
es[0] = float(aktual[0])

for i in range(1, n):
    es[i] = (
        alpha_es * aktual[i-1]
        + (1-alpha_es) * es[i-1]
    )

prediksi_es = (
    alpha_es * aktual[-1]
    + (1-alpha_es) * es[-1]
)

# ==========================================
# 7. TABEL PERBANDINGAN
# ==========================================

hasil = pd.DataFrame({
    "Periode": periode,
    "Permintaan Aktual": aktual,
    "SMA": sma,
    "WMA": wma,
    "Exponential Smoothing": es
})

if metode == "Simple Moving Average (SMA)":
    prediksi_berikutnya = prediksi_sma
elif metode == "Weighted Moving Average (WMA)":
    prediksi_berikutnya = prediksi_wma
else:
    prediksi_berikutnya = prediksi_es

st.header("3. Hasil Peramalan")

col1, col2, col3 = st.columns(3)

col1.metric(
    "Total permintaan",
    f"{sum(aktual):,} unit"
)

col2.metric(
    "Rata-rata per periode",
    f"{sum(aktual) / n:,.1f} unit"
)

col3.metric(
    "Prediksi periode berikutnya",
    f"{prediksi_berikutnya:,.1f} unit"
)

st.dataframe(
    hasil.round(2),
    use_container_width=True,
    hide_index=True
)

# ==========================================
# 8. GRAFIK
# ==========================================

st.header("4. Grafik Permintaan dan Forecasting")

grafik = hasil.set_index("Periode")[
    [
        "Permintaan Aktual",
        "SMA",
        "WMA",
        "Exponential Smoothing"
    ]
]

if metode == "Simple Moving Average (SMA)":
    kolom_prediksi = "SMA"
elif metode == "Weighted Moving Average (WMA)":
    kolom_prediksi = "WMA"
else:
    kolom_prediksi = "Exponential Smoothing"

st.line_chart(
    grafik[["Permintaan Aktual", kolom_prediksi]]
)

# ==========================================
# 9. EVALUASI MAE
# ==========================================

st.header("5. Evaluasi Akurasi Metode")

st.write(
    "MAE (Mean Absolute Error) mengukur rata-rata selisih "
    "absolut antara hasil prediksi dan permintaan aktual. "
    "Nilai MAE yang lebih kecil menunjukkan prediksi lebih dekat "
    "dengan data aktual pada periode yang diuji."
)

# Membandingkan semua metode pada periode yang sama,
# yaitu setelah empat periode pertama.
evaluasi = []

metode_prediksi = {
    "SMA": sma,
    "WMA": wma,
    "Exponential Smoothing": es
}

for nama, nilai_prediksi in metode_prediksi.items():
    pasangan = [
        (aktual[i], nilai_prediksi[i])
        for i in range(4, n)
        if nilai_prediksi[i] is not None
    ]

    if pasangan:
        mae = sum(
            abs(a - p) for a, p in pasangan
        ) / len(pasangan)

        evaluasi.append({
            "Metode": nama,
            "MAE": round(mae, 2)
        })

df_evaluasi = pd.DataFrame(evaluasi)

st.dataframe(
    df_evaluasi,
    use_container_width=True,
    hide_index=True
)

if not df_evaluasi.empty:
    terbaik = df_evaluasi.loc[
        df_evaluasi["MAE"].idxmin()
    ]

    st.success(
        f"Metode dengan MAE terkecil pada data simulasi ini "
        f"adalah {terbaik['Metode']}, dengan MAE "
        f"{terbaik['MAE']:,.2f} unit."
    )

# ==========================================
# 10. REKOMENDASI PRODUKSI
# ==========================================

st.header("6. Rekomendasi Perencanaan Produksi")

jumlah_produksi = max(0, round(prediksi_berikutnya))

st.metric(
    "Estimasi kebutuhan produksi",
    f"{jumlah_produksi:,} unit kampas rem"
)

st.write(
    f"Berdasarkan metode {metode}, permintaan periode berikutnya "
    f"diperkirakan sekitar {prediksi_berikutnya:,.1f} unit."
)

st.write(
    "Perkiraan ini dapat dijadikan dasar awal untuk menyusun "
    "target produksi. Sebelum menentukan jumlah produksi akhir, "
    "perusahaan perlu mempertimbangkan stok yang tersedia, "
    "pesanan pelanggan, kapasitas mesin, dan bahan baku."
)

st.caption(
    "Catatan: hasil peramalan adalah estimasi, bukan jaminan "
    "permintaan aktual. Data pada aplikasi ini bersifat simulasi."
)
