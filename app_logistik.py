import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import os
import json
from datetime import datetime
import math
import time
import gspread
from google.oauth2.service_account import Credentials

# --- FUNGSI PENGUBAH ANGKA MENJADI TEKS (TERBILANG) ---
def terbilang(n):
    if n == 0: return "Nol"
    satuan = ["", "Satu", "Dua", "Tiga", "Empat", "Lima", "Enam", "Tujuh", "Delapan", "Sembilan", "Sepuluh", "Sebelas"]
    if n < 12: return satuan[int(n)]
    elif n < 20: return terbilang(n - 10) + " Belas"
    elif n < 100: return terbilang(n // 10) + " Puluh " + terbilang(n % 10)
    elif n < 200: return "Seratus " + terbilang(n - 100)
    elif n < 1000: return terbilang(n // 100) + " Ratus " + terbilang(n % 100)
    elif n < 2000: return "Seribu " + terbilang(n - 1000)
    elif n < 1000000: return terbilang(n // 1000) + " Ribu " + terbilang(n % 1000)
    elif n < 1000000000: return terbilang(n // 1000000) + " Juta " + terbilang(n % 1000000)
    elif n < 1000000000000: return terbilang(n // 1000000000) + " Miliar " + terbilang(n % 1000000000)
    return ""

def format_terbilang(n):
    hasil = terbilang(math.floor(n)).replace("  ", " ").strip()
    return f"{hasil} RUPIAH".upper()

# --- FUNGSI PEMBUAT GAMBAR INVOICE FORMAL (B2B) ---
def buat_invoice_formal(no_invoice, tgl_invoice, nama_klien, alamat_klien, keterangan, harga_vol, total_vol, jumlah, ppn, total_akhir):
    img = Image.new('RGB', (1000, 750), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    
    try:
        f_title = ImageFont.truetype("arialbd.ttf", 16)
        f_bold = ImageFont.truetype("arialbd.ttf", 13)
        f_text = ImageFont.truetype("arial.ttf", 13)
        f_small = ImageFont.truetype("arial.ttf", 11)
    except:
        f_title = f_bold = f_text = f_small = ImageFont.load_default()

    def draw_centered_text(box, text, font, fill=(0,0,0)):
        bbox = d.textbbox((0,0), text, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        x = box[0] + (box[2] - box[0] - w) / 2
        y = box[1] + (box[3] - box[1] - h) / 2
        d.text((x, y), text, font=font, fill=fill)

    # 1. KOTAK KIRI ATAS (PERUSAHAAN)
    d.rectangle([30, 30, 500, 90], outline="black", width=2)
    d.line([(30, 60), (500, 60)], fill="black", width=1)
    draw_centered_text([30, 30, 500, 60], "PT TANGO LOGISTIK SEJAHTERA", f_title)
    draw_centered_text([30, 60, 500, 90], "Jl. SEJAHTERA NO.4 RT.03 / RW.05, SAMBAS", f_text)

    # 2. KOTAK KANAN ATAS (INVOICE INFO)
    d.rectangle([650, 30, 970, 90], outline="black", width=2)
    d.line([(650, 55), (970, 55)], fill="black", width=1)
    d.line([(800, 55), (800, 90)], fill="black", width=1)
    draw_centered_text([650, 30, 970, 55], "INVOICE", f_title)
    d.text((655, 60), "Tanggal Invoice", fill="black", font=f_text)
    d.text((655, 75), "No. Invoice", fill="black", font=f_text)
    d.text((820, 60), tgl_invoice, fill="black", font=f_text)
    d.text((820, 75), no_invoice, fill="black", font=f_text)

    # 3. KEPADA
    d.text((30, 120), "Kepada", fill="black", font=f_bold)
    d.text((30, 135), nama_klien, fill="black", font=f_bold)
    y_alamat = 155
    for baris in str(alamat_klien).split('\n'):
        d.text((30, y_alamat), baris.strip(), fill="black", font=f_text)
        y_alamat += 15

    # 4. TABEL UTAMA
    y_tabel = 240
    d.rectangle([30, y_tabel, 970, y_tabel + 100], outline="black", width=2)
    d.line([(30, y_tabel + 30), (970, y_tabel + 30)], fill="black", width=2)
    
    x_col1, x_col2, x_col3 = 550, 720, 850
    d.line([(x_col1, y_tabel), (x_col1, y_tabel + 100)], fill="black", width=1)
    d.line([(x_col2, y_tabel), (x_col2, y_tabel + 100)], fill="black", width=1)
    d.line([(x_col3, y_tabel), (x_col3, y_tabel + 100)], fill="black", width=1)

    draw_centered_text([30, y_tabel, x_col1, y_tabel + 30], "KETERANGAN", f_bold)
    draw_centered_text([x_col1, y_tabel, x_col2, y_tabel + 30], "HARGA / VOL", f_bold)
    draw_centered_text([x_col2, y_tabel, x_col3, y_tabel + 30], "VOLUME", f_bold)
    draw_centered_text([x_col3, y_tabel, 970, y_tabel + 30], "JUMLAH", f_bold)

    draw_centered_text([30, y_tabel+30, x_col1, y_tabel+100], keterangan, f_text)
    d.text((x_col1 + 10, y_tabel + 40), f"Rp", fill="black", font=f_text)
    d.text((x_col2 - 70, y_tabel + 40), f"{harga_vol:,.2f}", fill="black", font=f_text)
    draw_centered_text([x_col2, y_tabel+30, x_col3, y_tabel+100], f"{total_vol:,.0f}", f_text)
    d.text((x_col3 + 10, y_tabel + 40), f"Rp", fill="black", font=f_text)
    d.text((970 - 90, y_tabel + 40), f"{jumlah:,.0f}", fill="black", font=f_text)

    # 5. SUBTOTAL, PPN, TOTAL
    y_sub = y_tabel + 105
    d.text((x_col2 + 10, y_sub), "Sub Total", fill="black", font=f_text)
    d.text((x_col3 + 10, y_sub), "Rp", fill="black", font=f_text)
    d.text((970 - 90, y_sub), f"{jumlah:,.0f}", fill="black", font=f_text)

    d.text((x_col2 + 10, y_sub + 20), "PPN (11%)", fill="black", font=f_text)
    d.text((x_col3 + 10, y_sub + 20), "Rp", fill="black", font=f_text)
    d.text((970 - 90, y_sub + 20), f"{ppn:,.0f}", fill="black", font=f_text)

    d.line([(x_col2, y_sub + 40), (970, y_sub + 40)], fill="black", width=1)
    d.text((x_col2 + 10, y_sub + 45), "Total", fill="black", font=f_bold)
    d.text((x_col3 + 10, y_sub + 45), "Rp", fill="black", font=f_bold)
    d.text((970 - 90, y_sub + 45), f"{total_akhir:,.0f}", fill="black", font=f_bold)

    # 6. TERBILANG & TTD
    y_terbilang = 420
    d.text((30, y_terbilang), "Terbilang :", fill="black", font=f_text)
    d.rectangle([30, y_terbilang + 20, 650, y_terbilang + 60], outline="black", width=2)
    d.text((40, y_terbilang + 30), format_terbilang(total_akhir), fill="black", font=f_bold)

    d.text((800, y_terbilang + 50), "Hormat Kami,", fill="black", font=f_text)
    d.text((790, y_terbilang + 140), "ANTONIUS", fill="black", font=f_bold)
    d.text((790, y_terbilang + 155), "Direktur", fill="black", font=f_text)

    # 7. INFO BANK
    y_bank = 600
    d.rectangle([30, y_bank, 500, y_bank + 80], outline="black", width=2)
    d.text((35, y_bank + 5), "Bank", fill="black", font=f_bold)
    d.text((35, y_bank + 25), "No Rekening", fill="black", font=f_bold)
    d.text((35, y_bank + 45), "Cabang", fill="black", font=f_bold)
    d.text((35, y_bank + 65), "Atas Nama", fill="black", font=f_bold)
    d.text((150, y_bank + 5), ": BCA", fill="black", font=f_bold)
    d.text((150, y_bank + 25), ": 666-5161-777", fill="black", font=f_bold)
    d.text((150, y_bank + 45), ": PEMANGKAT", fill="black", font=f_bold)
    d.text((150, y_bank + 65), ": CV.BUDIMAS EKA SENTRATAMA SEJAHTERA", fill="black", font=f_bold)

    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()


# =====================================================================
# BAGIAN 1: JUDUL & KONEKSI GOOGLE SHEETS
# =====================================================================
st.set_page_config(page_title="Tango Logistik - Dasbor Operasional", layout="wide")
st.title("🚚 Sistem Manajemen Ekspedisi (Tango Logistik)")
st.write("Aplikasi Pintar Pengendalian Biaya, Target Laba, dan KPI Armada.")

SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

sh_invoice = None
try:
    if "gcp_service_account" in st.secrets:
        kredensial_dict = dict(st.secrets["gcp_service_account"])
        if "\\n" in kredensial_dict["private_key"]:
            kredensial_dict["private_key"] = kredensial_dict["private_key"].replace("\\n", "\n")
        credentials = Credentials.from_service_account_info(kredensial_dict, scopes=SCOPES)
        gc = gspread.authorize(credentials)
        sh_invoice = gc.open("database_invoice_formal").sheet1
        st.sidebar.success("🌐 Sistem Terhubung ke Cloud (Google Sheets)")
    else:
        credentials = Credentials.from_service_account_file("kunci.json", scopes=SCOPES)
        gc = gspread.authorize(credentials)
        sh_invoice = gc.open("database_invoice_formal").sheet1
        st.sidebar.success("🌐 Sistem Terhubung ke Laptop Lokal")
except Exception as e:
    st.sidebar.error(f"❌ Gagal koneksi (Cek Secrets/JSON): {e}")

# --- DATABASE LOKAL AUTO-SAVE ---
NAMA_FILE_DB = "database_invoice_formal.csv"
NAMA_FILE_JADWAL = "database_jadwal.csv"
STATE_FILE_INPUTS = "auto_save_inputs.json"

if not os.path.exists(NAMA_FILE_DB): pd.DataFrame(columns=["Waktu_Input", "No_Invoice", "Nama_Klien", "Keterangan", "Harga_Volume", "Total_Volume", "Jumlah", "PPN", "Total_Akhir"]).to_csv(NAMA_FILE_DB, index=False)
if not os.path.exists(NAMA_FILE_JADWAL): pd.DataFrame(columns=["Waktu_Simpan", "Hari", "Armada", "Rute", "Jml_Trip", "Pendapatan_Utama", "Pendapatan_Backhaul", "Total_Biaya"]).to_csv(NAMA_FILE_JADWAL, index=False)

if os.path.exists(STATE_FILE_INPUTS):
    try:
        with open(STATE_FILE_INPUTS, "r") as f: saved_state = json.load(f)
    except: saved_state = {}
else: saved_state = {}

current_state = {}
def get_val(key, default): return saved_state.get(key, default)
existing_data = pd.read_csv(NAMA_FILE_DB)

try:
    # --- BAGIAN 2: MASTER DATA CSV LOKAL ---
    data_mobil = pd.read_csv("data mobil.csv", sep=None, engine="python")
    data_rute = pd.read_csv("BEP per trip.csv", sep=None, engine="python", skiprows=1)
    
    try:
        data_pajak = pd.read_csv("pajak mobil.csv", sep=None, engine="python")
        data_susut = pd.read_csv("penyusutan kendaraan.csv", sep=None, engine="python")
    except:
        data_pajak = pd.DataFrame()
        data_susut = pd.DataFrame()

    if 'Unnamed: 1' in data_rute.columns or 'Unnamed: 2' in data_rute.columns:
        data_rute.columns = data_rute.iloc[0] 
        data_rute = data_rute[1:].reset_index(drop=True) 

    data_rute = data_rute.ffill()

    def bersihkan_titik_awal(teks):
        teks = str(teks).lower().strip()
        if 'pemangkat' in teks: return 'Pemangkat'
        if 'sambas' in teks: return 'Sambas'
        if 'singkawang' in teks: return 'Singkawang'
        if 'pontianak' in teks: return 'Pontianak'
        if teks in ['none', 'nan', 'berangkat', 'tujuan'] or 'keberangkatan' in teks: return None
        return str(teks).title() 

    kolom_awal = data_rute.columns[0]
    data_rute['Titik Keberangkatan Bersih'] = data_rute[kolom_awal].apply(bersihkan_titik_awal)
    data_rute = data_rute.dropna(subset=['Titik Keberangkatan Bersih'])

    kolom_rute_lower = [str(col).strip().lower().replace('\n', ' ') for col in data_rute.columns]
    nama_tujuan = "Tujuan"
    if 'tujuan' in kolom_rute_lower:
        idx_tujuan = kolom_rute_lower.index('tujuan')
        nama_tujuan = data_rute.columns[idx_tujuan]
        data_rute = data_rute[data_rute[nama_tujuan].astype(str).str.lower() != 'tujuan']

    kolom_tipe_rute = [col for col in data_rute.columns if 'tipe' in str(col).lower() and 'mobil' in str(col).lower()]
    nama_kol_tipe = kolom_tipe_rute[0] if kolom_tipe_rute else None

    def bersihkan_rupiah(teks):
        if pd.isna(teks): return 0.0
        t = str(teks).lower().replace('rp', '').replace(' ', '')
        if ',' in t and '.' in t:
            if t.rfind(',') > t.rfind('.'): t = t.split(',')[0] 
            else: t = t.split('.')[0] 
        elif ',' in t:
            if len(t.split(',')[-1]) <= 2: t = t.split(',')[0]
        elif '.' in t:
            if len(t.split('.')[-1]) <= 2: t = t.split('.')[0]
        t = t.replace('.', '').replace(',', '')
        try: return float(t)
        except: return 0.0

    col_harga = next((c for c in data_rute.columns if any(k in str(c).lower().replace('\n', ' ') for k in ['harga per trip', 'pendapatan', 'harga jual'])), None)
    col_cost = next((c for c in data_rute.columns if any(k in str(c).lower().replace('\n', ' ') for k in ['total cost', 'biaya variabel', 'cost per trip'])), None)
    col_fixed = next((c for c in data_rute.columns if any(k in str(c).lower().replace('\n', ' ') for k in ['fixed', 'biaya tetap', 'fix cost'])), None)
    
    data_rute['Harga_Bersih'] = data_rute[col_harga].apply(bersihkan_rupiah) if col_harga else 1500000.0
    data_rute['Cost_Bersih'] = data_rute[col_cost].apply(bersihkan_rupiah) if col_cost else 500000.0
    data_rute['Fixed_Bersih'] = data_rute[col_fixed].apply(bersihkan_rupiah) if col_fixed else 5000000.0

    if nama_kol_tipe:
        data_rute['Label_Rute'] = data_rute['Titik Keberangkatan Bersih'].astype(str) + " ➡️ " + data_rute[nama_tujuan].astype(str) + " (" + data_rute[nama_kol_tipe].astype(str) + ")"
    else:
        data_rute['Label_Rute'] = data_rute['Titik Keberangkatan Bersih'].astype(str) + " ➡️ " + data_rute[nama_tujuan].astype(str)

    estimasi_total_fixed = data_rute['Fixed_Bersih'].max()
    if estimasi_total_fixed == 0: estimasi_total_fixed = 74898583.0

    df_rute_unik = data_rute.drop_duplicates(subset=['Label_Rute']).copy()
    daftar_semua_rute = sorted(df_rute_unik['Label_Rute'].dropna().tolist())

    # --- BAGIAN 3: NAVIGASI BARU ---
    st.sidebar.title("🧭 Menu Navigasi")
    opsi_menu = [
        "📊 Kalkulator BEP (Utama)", 
        "🎯 Target Laba & Jadwal Operasi", 
        "📈 Dashboard Eksekutif & KPI", 
        "⚖️ Analisis Kinerja & Kapasitas (Ton-KM)", 
        "🏦 Keuangan Lanjutan & Aset",
        "🧾 Pembuatan Invoice B2B (Google Sheets)"  # <--- HALAMAN BARU
    ]
    def_menu = get_val('menu_halaman', opsi_menu[0])
    menu_halaman = st.sidebar.radio("Pilih Halaman Analisis:", opsi_menu, index=opsi_menu.index(def_menu) if def_menu in opsi_menu else 0)
    current_state['menu_halaman'] = menu_halaman
    st.sidebar.markdown("---")

    # =====================================================================
    # HALAMAN 1: KALKULATOR BEP
    # =====================================================================
    if menu_halaman == "📊 Kalkulator BEP (Utama)":
        st.sidebar.header("⚙️ Pengaturan Data Rute")
        pilihan_mobil_list = data_mobil['Tipe Mobil'].dropna().unique().tolist()
        def_mobil_bep = get_val('mobil_terpilih_bep', pilihan_mobil_list[0])
        mobil_terpilih_bep = st.sidebar.selectbox("Pilih Armada (Spesifikasi):", pilihan_mobil_list, index=pilihan_mobil_list.index(def_mobil_bep) if def_mobil_bep in pilihan_mobil_list else 0)
        current_state['mobil_terpilih_bep'] = mobil_terpilih_bep
        
        data_rute_spesifik = data_rute.copy()
        if 'tronton' in str(mobil_terpilih_bep).lower() and 'tujuan' in kolom_rute_lower:
            mask_pontianak = data_rute_spesifik[nama_tujuan].astype(str).str.lower().str.contains('pontianak')
            if mask_pontianak.any(): data_rute_spesifik = data_rute_spesifik[mask_pontianak]
        
        pilihan_berangkat = sorted(data_rute_spesifik['Titik Keberangkatan Bersih'].unique().tolist())
        if not pilihan_berangkat: pilihan_berangkat = sorted(data_rute['Titik Keberangkatan Bersih'].unique().tolist())
        def_brgkt = get_val('berangkat_terpilih', pilihan_berangkat[0])
        berangkat_terpilih = st.sidebar.selectbox("Titik Keberangkatan:", pilihan_berangkat, index=pilihan_berangkat.index(def_brgkt) if def_brgkt in pilihan_berangkat else 0)
        current_state['berangkat_terpilih'] = berangkat_terpilih

        rute_terfilter = data_rute_spesifik[data_rute_spesifik['Titik Keberangkatan Bersih'] == berangkat_terpilih]
        
        if 'tujuan' in kolom_rute_lower:
            pilihan_tujuan = rute_terfilter[nama_tujuan].dropna().unique().tolist()
            def_tjn = get_val('tujuan_terpilih', pilihan_tujuan[0] if pilihan_tujuan else None)
            tujuan_terpilih = st.sidebar.selectbox("Rute Tujuan:", pilihan_tujuan, index=pilihan_tujuan.index(def_tjn) if def_tjn in pilihan_tujuan else 0)
            current_state['tujuan_terpilih'] = tujuan_terpilih
            rute_tujuan_saja = rute_terfilter[rute_terfilter[nama_tujuan] == tujuan_terpilih]
        else:
            tujuan_terpilih = "Semua Rute"
            rute_tujuan_saja = rute_terfilter

        if nama_kol_tipe and not rute_tujuan_saja.empty:
            pilihan_kategori = rute_tujuan_saja[nama_kol_tipe].dropna().unique().tolist()
            def_kat = get_val('kategori_terpilih', pilihan_kategori[0])
            kategori_terpilih = st.sidebar.selectbox("Kategori Kendaraan:", pilihan_kategori, index=pilihan_kategori.index(def_kat) if def_kat in pilihan_kategori else 0)
            current_state['kategori_terpilih'] = kategori_terpilih
            detail_rute_final = rute_tujuan_saja[rute_tujuan_saja[nama_kol_tipe] == kategori_terpilih]
        else:
            detail_rute_final = rute_tujuan_saja
            kategori_terpilih = "Umum"

        def_tetap = detail_rute_final['Fixed_Bersih'].values[0] if not detail_rute_final.empty else estimasi_total_fixed
        def_var = detail_rute_final['Cost_Bersih'].values[0] if not detail_rute_final.empty else 500000.0
        def_harga = detail_rute_final['Harga_Bersih'].values[0] if not detail_rute_final.empty else 1500000.0

        st.subheader(f"📊 Detail Operasional BEP: **{mobil_terpilih_bep}**")
        col_m, col_r = st.columns(2)
        with col_m:
            st.write("**Data Spesifikasi Kendaraan:**")
            st.dataframe(data_mobil[data_mobil['Tipe Mobil'] == mobil_terpilih_bep])
        with col_r:
            st.write(f"**Data Rute ({berangkat_terpilih} ➡️ {tujuan_terpilih}) - {kategori_terpilih}:**")
            st.dataframe(detail_rute_final.drop(columns=['Titik Keberangkatan Bersih', 'Label_Rute', 'Harga_Bersih', 'Cost_Bersih', 'Fixed_Bersih'], errors='ignore'))
        
        st.markdown("---")
        st.subheader("🧮 Kalkulator Break Even Point (BEP)")
        col1, col2 = st.columns(2)
        with col1:
            st.info("💡 Input Data Keuangan")
            biaya_tetap = st.number_input("Total Biaya Tetap (Rp):", min_value=0.0, value=float(get_val('biaya_tetap_bep', def_tetap)), step=100000.0)
            current_state['biaya_tetap_bep'] = biaya_tetap
            biaya_variabel = st.number_input("Total Cost per Trip (Rp):", min_value=0.0, value=float(get_val('biaya_var_bep', def_var)), step=10000.0)
            current_state['biaya_var_bep'] = biaya_variabel
            harga_jual = st.number_input("Harga/Pendapatan per Trip (Rp):", min_value=0.0, value=float(get_val('harga_jual_bep', def_harga)), step=50000.0)
            current_state['harga_jual_bep'] = harga_jual
        with col2:
            st.success("📈 Hasil Analisis BEP")
            if harga_jual > biaya_variabel:
                margin = harga_jual - biaya_variabel
                bep_trip = biaya_tetap / margin
                st.metric(label="Titik Impas (BEP) - Trip", value=f"{bep_trip:.1f} Trip")
            else:
                st.error("⚠️ Harga per trip harus lebih besar dari biaya (Total Cost) per trip!")

    # =====================================================================
    # HALAMAN 2: TARGET LABA & JADWAL OPERASIONAL
    # =====================================================================
    elif menu_halaman == "🎯 Target Laba & Jadwal Operasi":
        st.subheader("🎯 Analisis Patokan Target Laba")
        col_t1, col_t2 = st.columns([1, 2])
        with col_t1:
            st.info("💰 1. Tentukan Target Keuntungan")
            target_laba = st.number_input("Target Laba Bulanan (Rp):", min_value=0.0, value=float(get_val('target_laba', 10000000.0)), step=1000000.0)
            current_state['target_laba'] = target_laba
            biaya_tetap_global = st.number_input("Total Biaya Tetap Operasional (Rp):", value=float(get_val('biaya_tetap_global', estimasi_total_fixed)), step=1000000.0)
            current_state['biaya_tetap_global'] = biaya_tetap_global
        with col_t2:
            st.success("📊 2. Referensi Kebutuhan Trip per Rute")
            df_ref = df_rute_unik[['Label_Rute', 'Harga_Bersih', 'Cost_Bersih']].copy()
            df_ref['Margin'] = df_ref['Harga_Bersih'] - df_ref['Cost_Bersih']
            df_ref = df_ref[df_ref['Margin'] > 0].copy() 
            df_ref['Kebutuhan Trip/Bln'] = (biaya_tetap_global + target_laba) / df_ref['Margin']
            df_ref['Kebutuhan Trip/Bln'] = df_ref['Kebutuhan Trip/Bln'].round(1)
            st.dataframe(df_ref[['Label_Rute', 'Kebutuhan Trip/Bln']], height=200)

        st.markdown("---")
        st.subheader("🗓️ 3. Perencanaan Jadwal Aktual Multi-Rute (Senin - Sabtu)")
        
        if 'No. Polisi' in data_mobil.columns:
            data_valid = data_mobil.dropna(subset=['No. Polisi', 'Tipe Mobil'])
            daftar_armada_fisik = data_valid.apply(lambda row: f"{str(row['No. Polisi']).strip()} - {str(row['Tipe Mobil']).strip()}", axis=1).tolist()
        else:
            daftar_armada_fisik = data_mobil['Tipe Mobil'].dropna().unique().tolist()
        
        hari_kerja = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu"]
        kolom_hari = st.columns(3)
        pendapatan_mingguan, biaya_var_mingguan, total_trip_mingguan = 0.0, 0.0, 0
        pendapatan_backhaul_mingguan = 0.0
        data_laporan_jadwal = []

        for i, hari in enumerate(hari_kerja):
            with kolom_hari[i % 3]:
                st.markdown(f"### 🗓️ {hari}")
                def_mobils = get_val(f'mobil_{hari}', [])
                def_mobils = [m for m in def_mobils if m in daftar_armada_fisik]
                mobil_pilihan = st.multiselect(f"Pilih Armada:", daftar_armada_fisik, default=def_mobils, key=f"mobil_{hari}")
                current_state[f'mobil_{hari}'] = mobil_pilihan
                
                for index, mobil in enumerate(mobil_pilihan):
                    tipe_spesifik = mobil.split(' - ')[1] if ' - ' in mobil else mobil
                    tm_lower = str(tipe_spesifik).lower()
                    if 'pu' in tm_lower or 'pick' in tm_lower or 'l300' in tm_lower: kategori_rute = 'pick up'
                    elif '71' in tm_lower or '100' in tm_lower or 'engkel' in tm_lower: kategori_rute = 'engkel'
                    elif 'tronton' in tm_lower: kategori_rute = 'tronton'
                    else: kategori_rute = 'truk standar'
                    
                    rute_terfilter_mobil_ini = [r for r in daftar_semua_rute if kategori_rute in str(r).lower()]
                    if not rute_terfilter_mobil_ini: rute_terfilter_mobil_ini = daftar_semua_rute

                    with st.container(border=True):
                        st.markdown(f"""<p style="margin:0; color:#00d4ff; font-weight:bold;">↳ {mobil}</p>
                                    <p style="margin:0; font-size:0.8em; color:#888; margin-bottom:10px;">Golongan: {kategori_rute.title()}</p>""", unsafe_allow_html=True)
                        
                        def_rute = get_val(f'rute_{hari}_{mobil}', rute_terfilter_mobil_ini[0])
                        rute_dipilih = st.selectbox("Tentukan Rute:", rute_terfilter_mobil_ini, index=rute_terfilter_mobil_ini.index(def_rute) if def_rute in rute_terfilter_mobil_ini else 0, key=f"rute_{hari}_{mobil}")
                        current_state[f'rute_{hari}_{mobil}'] = rute_dipilih
                        
                        jml_trip = st.number_input("Jml Trip:", min_value=1, value=int(get_val(f'trip_{hari}_{mobil}', 1)), step=1, key=f"trip_in_{hari}_{mobil}")
                        current_state[f'trip_{hari}_{mobil}'] = jml_trip
                        
                        ada_muatan_balik = st.checkbox("📦 Ada Muatan Balik?", value=bool(get_val(f'backhaul_{hari}_{mobil}', False)), key=f"backhaul_in_{hari}_{mobil}")
                        current_state[f'backhaul_{hari}_{mobil}'] = ada_muatan_balik
                        
                        pendapatan_ekstra_bersih = 0.0
                        if ada_muatan_balik:
                            pendapatan_ekstra_kotor = st.number_input("Harga Borongan Muatan Balik (Rp):", min_value=0.0, value=float(get_val(f'uang_balik_{hari}_{mobil}', 500000.0)), step=100000.0, key=f"uang_balik_in_{hari}_{mobil}")
                            current_state[f'uang_balik_{hari}_{mobil}'] = pendapatan_ekstra_kotor
                            pendapatan_ekstra_bersih = pendapatan_ekstra_kotor * 0.55
                            st.caption(f"*Laba Bersih yang masuk: **Rp {pendapatan_ekstra_bersih:,.0f}** (55% dari borongan).*")

                    harga_rute_aktual = df_rute_unik[df_rute_unik['Label_Rute'] == rute_dipilih]['Harga_Bersih'].values[0]
                    cost_rute_aktual = df_rute_unik[df_rute_unik['Label_Rute'] == rute_dipilih]['Cost_Bersih'].values[0]
                    
                    pendapatan_mingguan += (harga_rute_aktual * jml_trip)
                    pendapatan_backhaul_mingguan += (pendapatan_ekstra_bersih * jml_trip)
                    biaya_var_mingguan += (cost_rute_aktual * jml_trip)
                    total_trip_mingguan += jml_trip
                    
                    data_laporan_jadwal.append({
                        "Hari": hari, "Armada": mobil, "Rute": rute_dipilih, "Jml Trip": jml_trip, 
                        "Pendapatan Utama": harga_rute_aktual * jml_trip, 
                        "Pendapatan Muatan Balik (Nett 55%)": pendapatan_ekstra_bersih * jml_trip,
                        "Total Biaya": cost_rute_aktual * jml_trip
                    })
        
        st.markdown("---")
        st.subheader("🏁 Kesimpulan Proyeksi Keuangan Nyata")
        total_trip_bulanan = total_trip_mingguan * 4
        pendapatan_utama_bulanan = pendapatan_mingguan * 4
        pendapatan_backhaul_bulanan = pendapatan_backhaul_mingguan * 4
        total_pendapatan_bulanan = pendapatan_utama_bulanan + pendapatan_backhaul_bulanan
        biaya_var_bulanan = biaya_var_mingguan * 4
        biaya_total_bulanan = biaya_tetap_global + biaya_var_bulanan
        laba_rugi_aktual = total_pendapatan_bulanan - biaya_total_bulanan
        
        col_k1, col_k2, col_k3 = st.columns(3)
        col_k1.metric("Proyeksi Total Pendapatan", f"Rp {total_pendapatan_bulanan:,.0f}", f"+ Rp {pendapatan_backhaul_bulanan:,.0f} (Ekstra Muatan Balik)")
        col_k2.metric("Total Biaya", f"Rp {biaya_total_bulanan:,.0f}")
        
        if laba_rugi_aktual >= target_laba: col_k3.metric("🎉 Laba Bersih", f"Rp {laba_rugi_aktual:,.0f}")
        elif laba_rugi_aktual > 0: col_k3.metric("⚠️ Laba Bersih", f"Rp {laba_rugi_aktual:,.0f}")
        else: col_k3.metric("🚨 RUGI", f"Rp {laba_rugi_aktual:,.0f}")

        # FITUR DATABASE JADWAL
        st.markdown("---")
        st.markdown("#### 💾 Simpan & Unduh Laporan Jadwal")
        col_dl, col_sv = st.columns(2)
        
        with col_dl:
            if len(data_laporan_jadwal) > 0:
                df_laporan = pd.DataFrame(data_laporan_jadwal)
                csv_data = df_laporan.to_csv(index=False).encode('utf-8')
                st.download_button(label="📥 Unduh Laporan Jadwal (CSV)", data=csv_data, file_name="Jadwal_Logistik_Tango.csv", mime="text/csv")
            else:
                st.info("Pilih armada dan rute di atas untuk memunculkan tombol unduh.")

        with col_sv:
            if st.button("🚀 MENCETAK JADWAL KE BUKU BESAR (CSV)", type="primary"):
                if len(data_laporan_jadwal) > 0:
                    try:
                        waktu_sekarang = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        data_simpan = []
                        for baris in data_laporan_jadwal:
                            data_simpan.append({
                                "Waktu_Simpan": waktu_sekarang,
                                "Hari": baris["Hari"],
                                "Armada": baris["Armada"],
                                "Rute": baris["Rute"],
                                "Jml_Trip": baris["Jml Trip"],
                                "Pendapatan_Utama": baris["Pendapatan Utama"],
                                "Pendapatan_Backhaul": baris["Pendapatan Muatan Balik (Nett 55%)"],
                                "Total_Biaya": baris["Total Biaya"]
                            })
                            
                        df_jadwal_baru = pd.DataFrame(data_simpan)
                        df_jadwal_lama = pd.read_csv(NAMA_FILE_JADWAL)
                        df_gabungan_jadwal = pd.concat([df_jadwal_lama, df_jadwal_baru], ignore_index=True)
                        df_gabungan_jadwal.to_csv(NAMA_FILE_JADWAL, index=False)
                        st.success("✅ BERHASIL! Jadwal operasional telah dicetak ke Laporan Database Lokal.")
                        st.balloons()
                    except Exception as e:
                        st.error(f"❌ Gagal merekam jadwal: {e}")
                else:
                    st.warning("⚠️ Jadwal masih kosong. Silakan atur rute terlebih dahulu.")

    # =====================================================================
    # HALAMAN 3: DASHBOARD EKSEKUTIF & KPI ARMADA
    # =====================================================================
    elif menu_halaman == "📈 Dashboard Eksekutif & KPI":
        st.subheader("📈 Pusat Kendali Operasional (Dashboard Eksekutif)")
        
        if 'No. Polisi' in data_mobil.columns:
            data_valid = data_mobil.dropna(subset=['No. Polisi', 'Tipe Mobil'])
            daftar_armada_fisik = data_valid.apply(lambda row: f"{str(row['No. Polisi']).strip()} - {str(row['Tipe Mobil']).strip()}", axis=1).tolist()
        else:
            daftar_armada_fisik = ["Data pelat nomor tidak ditemukan"]

        col_nav1, col_nav2 = st.columns([1, 2])
        with col_nav1:
            st.info("🔍 Pilih Armada untuk Dievaluasi:")
            def_armada_cek = get_val('armada_diperiksa', daftar_armada_fisik[0])
            armada_diperiksa = st.selectbox("Pilih Pelat Nomor:", daftar_armada_fisik, index=daftar_armada_fisik.index(def_armada_cek) if def_armada_cek in daftar_armada_fisik else 0)
            current_state['armada_diperiksa'] = armada_diperiksa

            pelat_saja = armada_diperiksa.split(' - ')[0] if ' - ' in armada_diperiksa else armada_diperiksa
            
            st.markdown("### 📊 Fleet Utilization")
            hari_kerja_sebulan = 26
            trip_aktual = st.number_input("Total Trip armada ini bulan lalu:", min_value=0, value=int(get_val('trip_aktual', 20)), step=1)
            current_state['trip_aktual'] = trip_aktual

            utilitas = (trip_aktual / hari_kerja_sebulan) * 100
            
            if utilitas >= 80: st.success(f"Tingkat Utilitas: **{utilitas:.1f}%** (Sangat Baik)")
            elif utilitas >= 50: st.warning(f"Tingkat Utilitas: **{utilitas:.1f}%** (Perlu Ditingkatkan)")
            else: st.error(f"Tingkat Utilitas: **{utilitas:.1f}%** (Aset Menganggur!)")

        with col_nav2:
            st.success("💼 Profil Aset & Total Cost of Ownership (TCO)")
            status_pajak, status_susut, nilai_susut = "Data tidak ditemukan", "Data tidak ditemukan", 0.0
            
            if not data_pajak.empty:
                baris_pajak = data_pajak[data_pajak.astype(str).apply(lambda x: x.str.contains(pelat_saja, case=False, na=False)).any(axis=1)]
                if not baris_pajak.empty:
                    col_total_pajak = baris_pajak.columns[-1]
                    total_pajak = bersihkan_rupiah(baris_pajak.iloc[0][col_total_pajak])
                    status_pajak = f"Rp {total_pajak:,.0f} / Tahun"
            
            if not data_susut.empty:
                baris_susut = data_susut[data_susut.astype(str).apply(lambda x: x.str.contains(pelat_saja, case=False, na=False)).any(axis=1)]
                if not baris_susut.empty:
                    col_ket = next((c for c in baris_susut.columns if 'keterangan' in str(c).lower()), None)
                    col_dep = next((c for c in baris_susut.columns if 'depresiasi' in str(c).lower()), None)
                    if col_ket: status_susut = str(baris_susut.iloc[0][col_ket])
                    if col_dep: nilai_susut = bersihkan_rupiah(baris_susut.iloc[0][col_dep])

            st.write(f"**Status Kendaraan:** {status_susut}")
            st.write(f"**Beban Penyusutan Tahunan:** Rp {nilai_susut:,.0f}")
            st.write(f"**Estimasi Pajak Tahunan:** {status_pajak}")
            if 'lunas' in status_susut.lower() or 'mati' in status_susut.lower():
                st.info("💡 **Rekomendasi Manajerial:** Nilai buku kendaraan ini sudah habis (Lunas). Pertimbangkan peremajaan unit.")

        st.markdown("---")
        st.subheader("🧾 Kalkulator Surat Perintah Jalan (SPJ) & Kas Bon Supir")
        col_spj1, col_spj2 = st.columns([1, 1])
        with col_spj1:
            def_spj = get_val('rute_spj', daftar_semua_rute[0])
            rute_spj = st.selectbox("Pilih Rute untuk SPJ:", daftar_semua_rute, index=daftar_semua_rute.index(def_spj) if def_spj in daftar_semua_rute else 0)
            current_state['rute_spj'] = rute_spj
            cost_rute_spj = df_rute_unik[df_rute_unik['Label_Rute'] == rute_spj]['Cost_Bersih'].values[0]
            st.metric("Total Biaya Variabel (Per Trip)", f"Rp {cost_rute_spj:,.0f}")
            
        with col_spj2:
            st.write("**Alokasi Persentase Uang Jalan:**")
            pct_solar = st.slider("Solar / BBM (%)", 0, 100, int(get_val('pct_solar', 45)))
            current_state['pct_solar'] = pct_solar
            pct_makan = st.slider("Uang Jajan Sopir & Kernet (%)", 0, 100, int(get_val('pct_makan', 25)))
            current_state['pct_makan'] = pct_makan
            pct_parkir = st.slider("Parkir & Retribusi (%)", 0, 100, int(get_val('pct_parkir', 10)))
            current_state['pct_parkir'] = pct_parkir
            st.write(f"💰 **Total Kas Bon Supir: Rp {(cost_rute_spj * (pct_solar+pct_makan+pct_parkir) / 100):,.0f}**")

    # =====================================================================
    # HALAMAN 4: ANALISIS UNIT ECONOMICS (TON-KM)
    # =====================================================================
    elif menu_halaman == "⚖️ Analisis Kinerja & Kapasitas (Ton-KM)":
        st.subheader("⚖️ Analisis Unit Economics (Metrik Ton-KM)")
        st.write("Mengevaluasi efisiensi rute dan armada berdasarkan jarak tempuh dan kapasitas beban maksimal.")

        col_ton1, col_ton2 = st.columns(2)
        with col_ton1:
            st.info("🚛 1. Parameter Kapasitas Armada")
            pilihan_mobil_list = data_mobil['Tipe Mobil'].dropna().unique().tolist()
            def_armada_ton = get_val('armada_ton', pilihan_mobil_list[0])
            armada_ton = st.selectbox("Pilih Tipe Armada:", pilihan_mobil_list, index=pilihan_mobil_list.index(def_armada_ton) if def_armada_ton in pilihan_mobil_list else 0)
            current_state['armada_ton'] = armada_ton
            
            tm_lower = str(armada_ton).lower()
            if 'pu' in tm_lower or 'pick' in tm_lower or 'l300' in tm_lower: kategori_rute, default_tonase = 'pick up', 1.5
            elif '71' in tm_lower or '100' in tm_lower or 'engkel' in tm_lower: kategori_rute, default_tonase = 'engkel', 2.5
            elif 'tronton' in tm_lower: kategori_rute, default_tonase = 'tronton', 15.0
            else: kategori_rute, default_tonase = 'truk standar', 5.0
            
            kapasitas_ton = st.number_input(f"Kapasitas Maksimal (Ton):", min_value=0.5, value=float(get_val('kapasitas_ton', default_tonase)), step=0.5)
            current_state['kapasitas_ton'] = kapasitas_ton

        with col_ton2:
            st.info("🛣️ 2. Parameter Rute & Jarak")
            rute_terfilter_ton = [r for r in daftar_semua_rute if kategori_rute in str(r).lower()]
            if not rute_terfilter_ton: rute_terfilter_ton = daftar_semua_rute
            def_rute_ton = get_val('rute_ton', rute_terfilter_ton[0]) if rute_terfilter_ton else None
            rute_ton = st.selectbox("Pilih Rute Analisis:", rute_terfilter_ton, index=rute_terfilter_ton.index(def_rute_ton) if def_rute_ton in rute_terfilter_ton else 0)
            current_state['rute_ton'] = rute_ton

            cost_rute_ton = df_rute_unik[df_rute_unik['Label_Rute'] == rute_ton]['Cost_Bersih'].values[0] if rute_ton else 0
            harga_rute_ton = df_rute_unik[df_rute_unik['Label_Rute'] == rute_ton]['Harga_Bersih'].values[0] if rute_ton else 0
            jarak_km = st.number_input("Jarak Tempuh Rute (Kilometer):", min_value=1.0, value=float(get_val('jarak_km', 150.0)), step=10.0)
            current_state['jarak_km'] = jarak_km

        st.markdown("---")
        st.subheader("📈 Hasil Evaluasi Kinerja (Unit Economics)")
        if rute_ton and jarak_km > 0 and kapasitas_ton > 0:
            ton_km_total = kapasitas_ton * jarak_km
            biaya_per_ton_km = cost_rute_ton / ton_km_total
            pendapatan_per_ton_km = harga_rute_ton / ton_km_total
            margin_per_ton_km = pendapatan_per_ton_km - biaya_per_ton_km

            col_res1, col_res2, col_res3 = st.columns(3)
            col_res1.metric("Biaya Operasional per Ton-KM", f"Rp {biaya_per_ton_km:,.0f}")
            col_res2.metric("Pendapatan per Ton-KM", f"Rp {pendapatan_per_ton_km:,.0f}")
            
            if margin_per_ton_km > 0:
                col_res3.metric("✅ Margin per Ton-KM", f"Rp {margin_per_ton_km:,.0f}")
                st.success(f"💡 **Kesimpulan Bisnis:** Untuk setiap 1 Ton dipindahkan 1 KM menggunakan {armada_ton}, modal yang keluar **Rp {biaya_per_ton_km:,.0f}** dan laba bersih **Rp {margin_per_ton_km:,.0f}**.")
            else:
                col_res3.metric("🚨 Margin per Ton-KM (RUGI)", f"Rp {margin_per_ton_km:,.0f}")

    # =====================================================================
    # HALAMAN 5: KEUANGAN LANJUTAN & ASET (DIPISAH DARI INVOICE)
    # =====================================================================
    elif menu_halaman == "🏦 Keuangan Lanjutan & Aset":
        st.subheader("🏦 Manajemen Keuangan Lanjutan")
        tab1, tab2 = st.tabs(["🛞 Kalkulator Pemeliharaan Aset", "💸 Simulator Arus Kas"])
        
        with tab1:
            st.markdown("### 🛞 Manajemen Keausan Ban & Suku Cadang")
            col_ban1, col_ban2 = st.columns(2)
            with col_ban1:
                harga_set_ban = st.number_input("Harga 1 Set Ban (Rp):", min_value=1000000.0, value=float(get_val('harga_set_ban', 15000000.0)), step=500000.0)
                current_state['harga_set_ban'] = harga_set_ban
                umur_ban_km = st.number_input("Estimasi Umur Ban (Kilometer):", min_value=1000.0, value=float(get_val('umur_ban_km', 60000.0)), step=5000.0)
                current_state['umur_ban_km'] = umur_ban_km
            with col_ban2:
                jarak_rute_trip = st.number_input("Jarak Tempuh Rute yang Sering Dilalui (KM per Trip PP):", min_value=10.0, value=float(get_val('jarak_rute_trip', 300.0)), step=10.0)
                current_state['jarak_rute_trip'] = jarak_rute_trip

            if umur_ban_km > 0:
                biaya_ban_per_km = harga_set_ban / umur_ban_km
                tabungan_per_trip = biaya_ban_per_km * jarak_rute_trip
                st.write("---")
                st.metric("Biaya Keausan Ban per Kilometer", f"Rp {biaya_ban_per_km:,.0f} / KM")
                st.success(f"💡 Anda wajib menyisihkan **Rp {tabungan_per_trip:,.0f}** setiap kali truk menyelesaikan rute sejauh {jarak_rute_trip} KM ini.")

        with tab2:
            st.markdown("### 💸 Simulator Kebutuhan Modal Kerja (*Working Capital*)")
            col_cash1, col_cash2 = st.columns(2)
            with col_cash1:
                proyeksi_biaya_bulanan = st.number_input("Estimasi Total Biaya Operasional Sebulan (Rp):", min_value=1000000.0, value=float(get_val('proyeksi_biaya_bulanan', 250000000.0)), step=10000000.0)
                current_state['proyeksi_biaya_bulanan'] = proyeksi_biaya_bulanan
                top_options = ["0 Hari (Cash / Tunai Keras)", "14 Hari", "30 Hari (1 Bulan)", "60 Hari (2 Bulan)", "90 Hari (3 Bulan)"]
                def_top = get_val('top_klien', top_options[2])
                top_klien = st.selectbox("Rata-rata Klien Membayar Invoice (TOP):", top_options, index=top_options.index(def_top) if def_top in top_options else 2)
                current_state['top_klien'] = top_klien
            
            angka_hari = int(top_klien.split(' ')[0])
            with col_cash2:
                kebutuhan_modal_kerja = (proyeksi_biaya_bulanan / 30) * angka_hari
                st.metric("Dana Tunai (Modal Kerja) yang Harus Disiapkan", f"Rp {kebutuhan_modal_kerja:,.0f}")

    # =====================================================================
    # HALAMAN 6: PEMBUATAN INVOICE B2B (HALAMAN BARU)
    # =====================================================================
    elif menu_halaman == "🧾 Pembuatan Invoice B2B (Google Sheets)":
        st.subheader("🧾 Sistem Pembuatan Invoice B2B (Terhubung Google Sheets)")
        
        st.markdown("### 1️⃣ Kalkulasi Pembagian Harga Trip (Pro-rata Logistik)")
        
        # --- LOGIKA SINKRONISASI ---
        def sync_all():
            v1 = float(st.session_state.get("top_vol_1", 3000000.0))
            v2 = float(st.session_state.get("top_vol_2", 4000000.0))
            v3 = float(st.session_state.get("top_vol_3", 2500000.0))
            harga_trip = float(st.session_state.get("top_harga_trip", 3000000.0))
            st.session_state.bkg1 = v1
            st.session_state.bkg2 = v2
            st.session_state.bkg3 = v3
            tot = v1 + v2 + v3
            if tot > 0:
                tarif = harga_trip / tot
                st.session_state.hkg1, st.session_state.hkg2, st.session_state.hkg3 = tarif, tarif, tarif
            else:
                st.session_state.hkg1 = st.session_state.hkg2 = st.session_state.hkg3 = 0.0

        col_inv1, col_inv2, col_inv3 = st.columns(3)
        with col_inv1:
            pilihan_mobil_list_inv = data_mobil['Tipe Mobil'].dropna().unique().tolist() if 'Tipe Mobil' in data_mobil.columns else ["Truk Default"]
            armada_inv = st.selectbox("Pilih Armada:", pilihan_mobil_list_inv, key="armada_inv")
        with col_inv2:
            harga_target_trip = st.number_input("Target Total Harga 1 Trip (Rp):", min_value=100000.0, value=float(get_val('harga_target_trip', 3000000.0)), step=100000.0, key="top_harga_trip", on_change=sync_all)
        with col_inv3:
            kapasitas_truk_inv = st.number_input("Kapasitas Volume Truk (cm³):", min_value=1.0, value=float(get_val('kapasitas_truk_inv', 12000000.0)), step=500000.0, format="%.0f")

        st.markdown(f"**📝 Masukkan Rincian Volume Klien yang dimuat di {armada_inv}:**")
        col_klien1, col_klien2, col_klien3 = st.columns(3)
        with col_klien1:
            klien_1 = st.text_input("Nama Klien 1:", value=get_val('klien_1', "cv bess"))
            vol_1 = st.number_input("Volume Muatan 1 (cm³):", min_value=0.0, value=float(get_val('vol_1', 3000000.0)), step=100.0, format="%.0f", key="top_vol_1", on_change=sync_all)
        with col_klien2:
            klien_2 = st.text_input("Nama Klien 2:", value=get_val('klien_2', "evary"))
            vol_2 = st.number_input("Volume Muatan 2 (cm³):", min_value=0.0, value=float(get_val('vol_2', 4000000.0)), step=100.0, format="%.0f", key="top_vol_2", on_change=sync_all)
        with col_klien3:
            klien_3 = st.text_input("Nama Klien 3:", value=get_val('klien_3', "msau"))
            vol_3 = st.number_input("Volume Muatan 3 (cm³):", min_value=0.0, value=float(get_val('vol_3', 2500000.0)), step=100.0, format="%.0f", key="top_vol_3", on_change=sync_all)
        
        st.markdown("---")
        if (vol_1 + vol_2 + vol_3) > 0:
            st.markdown("### 2️⃣ Formulir & Rincian Invoice per Klien")

            # --- MENGHITUNG JUMLAH BARIS REAL-TIME DARI GOOGLE SHEETS ---
            try:
                jumlah_di_db = len(sh_invoice.get_all_records()) if sh_invoice else len(existing_data)
            except:
                jumlah_di_db = len(existing_data)
            
            base_urut = jumlah_di_db + 1

            col_inv_tgl, col_inv_pref = st.columns([2, 1])
            with col_inv_tgl: tgl_invoice = st.text_input("Tanggal Invoice Global:", value=datetime.now().strftime("%d %B %Y"))
            with col_inv_pref: prefix_inv = st.text_input("Kode Prefix:", value=f"INV{datetime.now().strftime('%y')}-")

            # Menentukan angka urut secara mutlak (tidak akan loncat)
            urut_1 = base_urut
            no_inv_1 = f"{prefix_inv}{int(urut_1):03d}"
            
            urut_2 = urut_1 + (1 if vol_1 > 0 else 0)
            no_inv_2 = f"{prefix_inv}{int(urut_2):03d}"
            
            urut_3 = urut_2 + (1 if vol_2 > 0 else 0)
            no_inv_3 = f"{prefix_inv}{int(urut_3):03d}"

            tab_inv1, tab_inv2, tab_inv3 = st.tabs([f"📄 {klien_1}", f"📄 {klien_2}", f"📄 {klien_3}"])
            
            data_untuk_massal = []
            
            # --- KLIEN 1 ---
            with tab_inv1:
                if vol_1 > 0:
                    # Kotak dinonaktifkan (disabled=True) agar benar-benar auto-pilot
                    st.text_input(f"No. Invoice {klien_1} (Otomatis):", value=no_inv_1, disabled=True, key="inv_auto_1")
                    alamat_1 = st.text_area(f"Alamat {klien_1}:", value=get_val('al1', "Alamat Klien 1..."), height=80, key="al1")
                    ket_1 = st.text_input(f"Keterangan {klien_1}:", value="Biaya Jasa", key="ket1")
                    c1, c2 = st.columns(2)
                    with c1: hk_1 = st.number_input(f"Harga / Volume:", step=1.0, key="hkg1")
                    with c2: bk_1 = st.number_input(f"Total Volume:", step=1.0, key="bkg1")
                    
                    sub_1 = hk_1 * bk_1
                    ppn_1 = sub_1 * 0.11
                    tot_1 = sub_1 + ppn_1
                    
                    data_untuk_massal.append([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), no_inv_1, klien_1, ket_1, hk_1, bk_1, sub_1, ppn_1, tot_1])

                    st.info(f"**💰 Rincian Biaya {klien_1}:**\n\n"
                            f"• Harga/Volume x Total Volume = **Rp {sub_1:,.0f}**\n\n"
                            f"• PPN (11%) = **Rp {ppn_1:,.0f}**\n\n"
                            f"• **TOTAL AKHIR = Rp {tot_1:,.0f}**")
                    
                    img_1 = buat_invoice_formal(no_inv_1, tgl_invoice, klien_1, alamat_1, ket_1, hk_1, bk_1, sub_1, ppn_1, tot_1)
                    if st.download_button(label=f"🚀 CETAK & SAVE {klien_1} SAJA", data=img_1, file_name=f"{no_inv_1.replace('/','-')}.png", mime="image/png", key="dl_1", type="primary"):
                        if sh_invoice:
                            sh_invoice.append_row([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), no_inv_1, klien_1, ket_1, hk_1, bk_1, sub_1, ppn_1, tot_1])

            # --- KLIEN 2 ---
            with tab_inv2:
                if vol_2 > 0:
                    st.text_input(f"No. Invoice {klien_2} (Otomatis):", value=no_inv_2, disabled=True, key="inv_auto_2")
                    alamat_2 = st.text_area(f"Alamat {klien_2}:", value=get_val('al2', "Alamat Klien 2..."), height=80, key="al2")
                    ket_2 = st.text_input(f"Keterangan {klien_2}:", value="Biaya Jasa", key="ket2")
                    c1, c2 = st.columns(2)
                    with c1: hk_2 = st.number_input(f"Harga / Volume:", step=1.0, key="hkg2")
                    with c2: bk_2 = st.number_input(f"Total Volume:", step=1.0, key="bkg2")
                    
                    sub_2 = hk_2 * bk_2
                    ppn_2 = sub_2 * 0.11
                    tot_2 = sub_2 + ppn_2
                    
                    data_untuk_massal.append([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), no_inv_2, klien_2, ket_2, hk_2, bk_2, sub_2, ppn_2, tot_2])

                    st.info(f"**💰 Rincian Biaya {klien_2}:**\n\n"
                            f"• Harga/Volume x Total Volume = **Rp {sub_2:,.0f}**\n\n"
                            f"• PPN (11%) = **Rp {ppn_2:,.0f}**\n\n"
                            f"• **TOTAL AKHIR = Rp {tot_2:,.0f}**")
                    
                    img_2 = buat_invoice_formal(no_inv_2, tgl_invoice, klien_2, alamat_2, ket_2, hk_2, bk_2, sub_2, ppn_2, tot_2)
                    if st.download_button(label=f"🚀 CETAK & SAVE {klien_2} SAJA", data=img_2, file_name=f"{no_inv_2.replace('/','-')}.png", mime="image/png", key="dl_2", type="primary"):
                        if sh_invoice:
                            sh_invoice.append_row([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), no_inv_2, klien_2, ket_2, hk_2, bk_2, sub_2, ppn_2, tot_2])

            # --- KLIEN 3 ---
            with tab_inv3:
                if vol_3 > 0:
                    st.text_input(f"No. Invoice {klien_3} (Otomatis):", value=no_inv_3, disabled=True, key="inv_auto_3")
                    alamat_3 = st.text_area(f"Alamat {klien_3}:", value=get_val('al3', "Alamat Klien 3..."), height=80, key="al3")
                    ket_3 = st.text_input(f"Keterangan {klien_3}:", value="Biaya Jasa", key="ket3")
                    c1, c2 = st.columns(2)
                    with c1: hk_3 = st.number_input(f"Harga / Volume:", step=1.0, key="hkg3")
                    with c2: bk_3 = st.number_input(f"Total Volume:", step=1.0, key="bkg3")
                    
                    sub_3 = hk_3 * bk_3
                    ppn_3 = sub_3 * 0.11
                    tot_3 = sub_3 + ppn_3
                    
                    data_untuk_massal.append([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), no_inv_3, klien_3, ket_3, hk_3, bk_3, sub_3, ppn_3, tot_3])

                    st.info(f"**💰 Rincian Biaya {klien_3}:**\n\n"
                            f"• Harga/Volume x Total Volume = **Rp {sub_3:,.0f}**\n\n"
                            f"• PPN (11%) = **Rp {ppn_3:,.0f}**\n\n"
                            f"• **TOTAL AKHIR = Rp {tot_3:,.0f}**")
                    
                    img_3 = buat_invoice_formal(no_inv_3, tgl_invoice, klien_3, alamat_3, ket_3, hk_3, bk_3, sub_3, ppn_3, tot_3)
                    if st.download_button(label=f"🚀 CETAK & SAVE {klien_3} SAJA", data=img_3, file_name=f"{no_inv_3.replace('/','-')}.png", mime="image/png", key="dl_3", type="primary"):
                        if sh_invoice:
                            sh_invoice.append_row([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), no_inv_3, klien_3, ket_3, hk_3, bk_3, sub_3, ppn_3, tot_3])


            # --- 3. TOMBOL SIMPAN MASSAL (TANPA CETAK) ---
            st.markdown("---")
            st.markdown("### 💾 Aksi Massal Database")
            st.caption("💡 **Tips Anti-Lompat:** Gunakan tombol biru di bawah ini untuk menyimpan seluruh data klien secara bersamaan ke Google Sheets agar urutannya sempurna.")
            if st.button("📥 SIMPAN SEMUA DATA KLIEN KE DATABASE (TANPA CETAK)", use_container_width=True):
                try:
                    if sh_invoice and len(data_untuk_massal) > 0:
                        sh_invoice.append_rows(data_untuk_massal)
                        st.success("✅ Seluruh data klien berhasil dibukukan sekaligus ke Google Sheets!")
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error("🚨 Gagal menyambung ke Google Sheets atau tidak ada data yang diisi.")
                except Exception as e:
                    st.error(f"❌ Terjadi kesalahan: {e}")

            # --- 4. ZONA RESET ---
            st.markdown("---")
            st.markdown("### ⚠️ Pengaturan Database Lanjutan")
            if st.checkbox("Aktifkan Tombol Reset (Hapus Semua Data Invoice)"):
                if st.button("🚨 KOSONGKAN GOOGLE SHEETS SEKARANG"):
                    if sh_invoice:
                        sh_invoice.clear()
                        sh_invoice.append_row(["Waktu_Input", "No_Invoice", "Nama_Klien", "Keterangan", "Harga_Volume", "Total_Volume", "Jumlah", "PPN", "Total_Akhir"])
                        st.success("Database berhasil di-reset menjadi kosong!"); time.sleep(1.5); st.rerun()

    # --- AUTO SAVE INPUTS ---
    current_state.update({k: v for k, v in st.session_state.items() if isinstance(v, (str, int, float, list))})
    with open(STATE_FILE_INPUTS, "w") as f: json.dump(current_state, f)

except Exception as e:
    st.error(f"Terjadi kesalahan sistem internal: {e}")