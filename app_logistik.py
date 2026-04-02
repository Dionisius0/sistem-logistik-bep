import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import os
import json
from datetime import datetime

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
    hasil = terbilang(n).replace("  ", " ").strip()
    return f"{hasil} RUPIAH".upper()

# --- FUNGSI PEMBUAT GAMBAR INVOICE FORMAL (B2B) ---
def buat_invoice_formal(no_invoice, tgl_invoice, nama_klien, alamat_klien, keterangan, harga_kg, banyak_kg):
    # Ukuran kanvas resolusi tinggi
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

    # 3. KEPADA (ALAMAT)
    d.text((30, 120), "Kepada", fill="black", font=f_bold)
    d.text((30, 135), nama_klien, fill="black", font=f_bold)
    
    y_alamat = 155
    for baris in alamat_klien.split('\n'):
        d.text((30, y_alamat), baris, fill="black", font=f_text)
        y_alamat += 15

    # 4. TABEL UTAMA
    y_tabel = 220
    d.rectangle([30, y_tabel, 970, y_tabel + 100], outline="black", width=2)
    d.line([(30, y_tabel + 30), (970, y_tabel + 30)], fill="black", width=2) # Header line
    
    # Garis Vertikal Tabel
    x_col1 = 550
    x_col2 = 720
    x_col3 = 850
    d.line([(x_col1, y_tabel), (x_col1, y_tabel + 100)], fill="black", width=1)
    d.line([(x_col2, y_tabel), (x_col2, y_tabel + 100)], fill="black", width=1)
    d.line([(x_col3, y_tabel), (x_col3, y_tabel + 100)], fill="black", width=1)

    # Header Teks
    draw_centered_text([30, y_tabel, x_col1, y_tabel + 30], "KETERANGAN", f_bold)
    draw_centered_text([x_col1, y_tabel, x_col2, y_tabel + 30], "HARGA / KG", f_bold)
    draw_centered_text([x_col2, y_tabel, x_col3, y_tabel + 30], "BANYAKNYA / KG", f_bold)
    draw_centered_text([x_col3, y_tabel, 970, y_tabel + 30], "JUMLAH", f_bold)

    # Matematika
    jumlah = harga_kg * banyak_kg
    ppn = jumlah * 0.11
    total = jumlah + ppn

    # Data Teks
    draw_centered_text([30, y_tabel+30, x_col1, y_tabel+100], keterangan, f_text)
    d.text((x_col1 + 10, y_tabel + 40), f"Rp", fill="black", font=f_text)
    d.text((x_col2 - 60, y_tabel + 40), f"{harga_kg:,.2f}", fill="black", font=f_text)
    
    draw_centered_text([x_col2, y_tabel+30, x_col3, y_tabel+100], f"{banyak_kg:,.0f}", f_text)
    
    d.text((x_col3 + 10, y_tabel + 40), f"Rp", fill="black", font=f_text)
    d.text((970 - 90, y_tabel + 40), f"{jumlah:,.0f}", fill="black", font=f_text)

    # 5. SUBTOTAL, PPN, TOTAL
    y_sub = y_tabel + 105
    d.text((x_col2 + 10, y_sub), "Sub Total", fill="black", font=f_text)
    d.text((x_col3 + 10, y_sub), "Rp", fill="black", font=f_text)
    d.text((970 - 90, y_sub), f"{jumlah:,.0f}", fill="black", font=f_text)

    d.text((x_col2 + 10, y_sub + 20), "PPN", fill="black", font=f_text)
    d.text((x_col3 + 10, y_sub + 20), "Rp", fill="black", font=f_text)
    d.text((970 - 90, y_sub + 20), f"{ppn:,.0f}", fill="black", font=f_text)

    d.line([(x_col2, y_sub + 40), (970, y_sub + 40)], fill="black", width=1)

    d.text((x_col2 + 10, y_sub + 45), "Total", fill="black", font=f_bold)
    d.text((x_col3 + 10, y_sub + 45), "Rp", fill="black", font=f_bold)
    d.text((970 - 90, y_sub + 45), f"{total:,.0f}", fill="black", font=f_bold)

    # 6. TERBILANG
    y_terbilang = 400
    d.text((30, y_terbilang), "Terbilang :", fill="black", font=f_text)
    d.rectangle([30, y_terbilang + 20, 650, y_terbilang + 60], outline="black", width=2)
    d.text((40, y_terbilang + 30), format_terbilang(total), fill="black", font=f_bold)

    # 7. TANDA TANGAN
    d.text((800, y_terbilang + 50), "Hormat Kami,", fill="black", font=f_text)
    d.text((790, y_terbilang + 140), "ANTONIUS", fill="black", font=f_bold)
    d.text((790, y_terbilang + 155), "Direktur", fill="black", font=f_text)

    # 8. INFO BANK
    y_bank = 580
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

# --- BAGIAN 1: Judul dan Tampilan Dasar ---
st.set_page_config(page_title="Tango Logistik - Dasbor Operasional", layout="wide")
st.title("🚚 Sistem Manajemen Ekspedisi (Tango Logistik)")
st.write("Aplikasi Pintar Pengendalian Biaya, Target Laba, dan KPI Armada.")

# --- DATABASE LOKAL & SISTEM AUTO-SAVE ---
NAMA_FILE_DB = "database_invoice_formal.csv"
NAMA_FILE_JADWAL = "database_jadwal.csv"
STATE_FILE_INPUTS = "auto_save_inputs.json"

if not os.path.exists(NAMA_FILE_DB):
    pd.DataFrame(columns=["Waktu_Input", "No_Invoice", "Nama_Klien", "Keterangan", "Harga_KG", "Banyaknya_KG", "Jumlah", "PPN", "Total_Akhir"]).to_csv(NAMA_FILE_DB, index=False)

if not os.path.exists(NAMA_FILE_JADWAL):
    pd.DataFrame(columns=["Waktu_Simpan", "Hari", "Armada", "Rute", "Jml_Trip", "Pendapatan_Utama", "Pendapatan_Backhaul", "Total_Biaya"]).to_csv(NAMA_FILE_JADWAL, index=False)

# Mengambil ingatan kotak isian sebelumnya
if os.path.exists(STATE_FILE_INPUTS):
    try:
        with open(STATE_FILE_INPUTS, "r") as f:
            saved_state = json.load(f)
    except:
        saved_state = {}
else:
    saved_state = {}

current_state = {}

def get_val(key, default):
    return saved_state.get(key, default)

existing_data = pd.read_csv(NAMA_FILE_DB)

try:
    # --- BAGIAN 2: Membaca Semua Data CSV Lokal ---
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

    # --- BAGIAN 3: NAVIGASI ---
    st.sidebar.title("🧭 Menu Navigasi")
    opsi_menu = ["📊 Kalkulator BEP (Utama)", "🎯 Target Laba & Jadwal Operasi", "📈 Dashboard Eksekutif & KPI", "⚖️ Analisis Kinerja & Kapasitas (Ton-KM)", "🏦 Keuangan Lanjutan & Aset"]
    def_menu = get_val('menu_halaman', opsi_menu[0])
    if def_menu not in opsi_menu: def_menu = opsi_menu[0]
    menu_halaman = st.sidebar.radio("Pilih Halaman Analisis:", opsi_menu, index=opsi_menu.index(def_menu))
    current_state['menu_halaman'] = menu_halaman
    st.sidebar.markdown("---")

    # =====================================================================
    # HALAMAN 1: KALKULATOR BEP
    # =====================================================================
    if menu_halaman == "📊 Kalkulator BEP (Utama)":
        st.sidebar.header("⚙️ Pengaturan Data Rute")
        pilihan_mobil_list = data_mobil['Tipe Mobil'].dropna().unique().tolist()
        
        def_mobil_bep = get_val('mobil_terpilih_bep', pilihan_mobil_list[0])
        if def_mobil_bep not in pilihan_mobil_list: def_mobil_bep = pilihan_mobil_list[0]
        mobil_terpilih_bep = st.sidebar.selectbox("Pilih Armada (Spesifikasi):", pilihan_mobil_list, index=pilihan_mobil_list.index(def_mobil_bep))
        current_state['mobil_terpilih_bep'] = mobil_terpilih_bep
        
        data_rute_spesifik = data_rute.copy()
        if 'tronton' in str(mobil_terpilih_bep).lower() and 'tujuan' in kolom_rute_lower:
            mask_pontianak = data_rute_spesifik[nama_tujuan].astype(str).str.lower().str.contains('pontianak')
            if mask_pontianak.any(): data_rute_spesifik = data_rute_spesifik[mask_pontianak]
        
        pilihan_berangkat = sorted(data_rute_spesifik['Titik Keberangkatan Bersih'].unique().tolist())
        if not pilihan_berangkat: pilihan_berangkat = sorted(data_rute['Titik Keberangkatan Bersih'].unique().tolist())
        
        def_brgkt = get_val('berangkat_terpilih', pilihan_berangkat[0])
        if def_brgkt not in pilihan_berangkat: def_brgkt = pilihan_berangkat[0]
        berangkat_terpilih = st.sidebar.selectbox("Titik Keberangkatan:", pilihan_berangkat, index=pilihan_berangkat.index(def_brgkt))
        current_state['berangkat_terpilih'] = berangkat_terpilih

        rute_terfilter = data_rute_spesifik[data_rute_spesifik['Titik Keberangkatan Bersih'] == berangkat_terpilih]
        
        if 'tujuan' in kolom_rute_lower:
            pilihan_tujuan = rute_terfilter[nama_tujuan].dropna().unique().tolist()
            def_tjn = get_val('tujuan_terpilih', pilihan_tujuan[0]) if pilihan_tujuan else None
            if def_tjn not in pilihan_tujuan and pilihan_tujuan: def_tjn = pilihan_tujuan[0]
            tujuan_terpilih = st.sidebar.selectbox("Rute Tujuan:", pilihan_tujuan, index=pilihan_tujuan.index(def_tjn) if def_tjn else 0)
            current_state['tujuan_terpilih'] = tujuan_terpilih
            rute_tujuan_saja = rute_terfilter[rute_terfilter[nama_tujuan] == tujuan_terpilih]
        else:
            tujuan_terpilih = "Semua Rute"
            rute_tujuan_saja = rute_terfilter

        if nama_kol_tipe and not rute_tujuan_saja.empty:
            pilihan_kategori = rute_tujuan_saja[nama_kol_tipe].dropna().unique().tolist()
            def_kat = get_val('kategori_terpilih', pilihan_kategori[0])
            if def_kat not in pilihan_kategori: def_kat = pilihan_kategori[0]
            kategori_terpilih = st.sidebar.selectbox("Kategori Kendaraan:", pilihan_kategori, index=pilihan_kategori.index(def_kat))
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
                        if def_rute not in rute_terfilter_mobil_ini: def_rute = rute_terfilter_mobil_ini[0]
                        rute_dipilih = st.selectbox("Tentukan Rute:", rute_terfilter_mobil_ini, index=rute_terfilter_mobil_ini.index(def_rute), key=f"rute_{hari}_{mobil}")
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
            if def_armada_cek not in daftar_armada_fisik: def_armada_cek = daftar_armada_fisik[0]
            armada_diperiksa = st.selectbox("Pilih Pelat Nomor:", daftar_armada_fisik, index=daftar_armada_fisik.index(def_armada_cek))
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
            status_pajak = "Data tidak ditemukan"
            status_susut = "Data tidak ditemukan"
            nilai_susut = 0.0
            
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
            if def_spj not in daftar_semua_rute: def_spj = daftar_semua_rute[0]
            rute_spj = st.selectbox("Pilih Rute untuk SPJ:", daftar_semua_rute, index=daftar_semua_rute.index(def_spj))
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
            
            st.write("---")
            st.write("💵 **Rincian Uang yang Dibawa Supir:**")
            st.write(f"- Uang Solar: **Rp {(cost_rute_spj * pct_solar / 100):,.0f}**")
            st.write(f"- Uang Makan: **Rp {(cost_rute_spj * pct_makan / 100):,.0f}**")
            st.write(f"- Parkir/Tol: **Rp {(cost_rute_spj * pct_parkir / 100):,.0f}**")
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
            if def_armada_ton not in pilihan_mobil_list: def_armada_ton = pilihan_mobil_list[0]
            armada_ton = st.selectbox("Pilih Tipe Armada:", pilihan_mobil_list, index=pilihan_mobil_list.index(def_armada_ton))
            current_state['armada_ton'] = armada_ton
            
            tm_lower = str(armada_ton).lower()
            if 'pu' in tm_lower or 'pick' in tm_lower or 'l300' in tm_lower: 
                kategori_rute = 'pick up'
                default_tonase = 1.5
            elif '71' in tm_lower or '100' in tm_lower or 'engkel' in tm_lower: 
                kategori_rute = 'engkel'
                default_tonase = 2.5
            elif 'tronton' in tm_lower: 
                kategori_rute = 'tronton'
                default_tonase = 15.0
            else: 
                kategori_rute = 'truk standar'
                default_tonase = 5.0
            
            kapasitas_ton = st.number_input(f"Kapasitas Maksimal (Ton):", min_value=0.5, value=float(get_val('kapasitas_ton', default_tonase)), step=0.5)
            current_state['kapasitas_ton'] = kapasitas_ton

        with col_ton2:
            st.info("🛣️ 2. Parameter Rute & Jarak")
            rute_terfilter_ton = [r for r in daftar_semua_rute if kategori_rute in str(r).lower()]
            if not rute_terfilter_ton: 
                rute_terfilter_ton = daftar_semua_rute
                
            def_rute_ton = get_val('rute_ton', rute_terfilter_ton[0]) if rute_terfilter_ton else None
            if def_rute_ton not in rute_terfilter_ton: def_rute_ton = rute_terfilter_ton[0] if rute_terfilter_ton else None
            rute_ton = st.selectbox("Pilih Rute Analisis:", rute_terfilter_ton, index=rute_terfilter_ton.index(def_rute_ton) if def_rute_ton else 0)
            current_state['rute_ton'] = rute_ton

            if rute_ton:
                cost_rute_ton = df_rute_unik[df_rute_unik['Label_Rute'] == rute_ton]['Cost_Bersih'].values[0]
                harga_rute_ton = df_rute_unik[df_rute_unik['Label_Rute'] == rute_ton]['Harga_Bersih'].values[0]
            else:
                cost_rute_ton, harga_rute_ton = 0, 0
                
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
                st.success(f"💡 **Kesimpulan Bisnis:** Untuk setiap 1 Ton barang dipindahkan 1 Kilometer menggunakan {armada_ton}, modal yang keluar **Rp {biaya_per_ton_km:,.0f}** dan laba bersih **Rp {margin_per_ton_km:,.0f}**.")
            else:
                col_res3.metric("🚨 Margin per Ton-KM (RUGI)", f"Rp {margin_per_ton_km:,.0f}")
                st.error("⚠️ **Peringatan:** Armada ini terlalu boros untuk jarak sejauh ini dengan kapasitas tersebut.")

    # =====================================================================
    # HALAMAN 5: KEUANGAN LANJUTAN & ASET (INVOICE FORMAL)
    # =====================================================================
    elif menu_halaman == "🏦 Keuangan Lanjutan & Aset":
        st.subheader("🏦 Manajemen Keuangan Lanjutan")
        
        tab1, tab2, tab3 = st.tabs(["🛞 Kalkulator Pemeliharaan Aset", "💸 Simulator Arus Kas", "🧾 Cetak Invoice Formal"])
        
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
                if def_top not in top_options: def_top = top_options[2]
                top_klien = st.selectbox("Rata-rata Klien Membayar Invoice (TOP):", top_options, index=top_options.index(def_top))
                current_state['top_klien'] = top_klien
            
            angka_hari = int(top_klien.split(' ')[0])
            
            with col_cash2:
                kebutuhan_modal_kerja = (proyeksi_biaya_bulanan / 30) * angka_hari
                st.metric("Dana Tunai (Modal Kerja) yang Harus Disiapkan", f"Rp {kebutuhan_modal_kerja:,.0f}")
                if angka_hari == 0: st.success("✅ Bisnis yang sangat sehat! Klien membayar tunai.")
                elif angka_hari > 30: st.error(f"🚨 Siapkan minimal **Rp {kebutuhan_modal_kerja:,.0f}** di rekening untuk talangan.")
                else: st.info(f"💡 Pastikan arus kas memiliki penyangga setidaknya **Rp {kebutuhan_modal_kerja:,.0f}**.")

        with tab3:
            st.markdown("### 🧾 Form Cetak Invoice Profesional")
            st.info("⚡ Setiap huruf dan angka yang diketik di kotak ini otomatis tersimpan (Auto-Save).")
            
            col_inv1, col_inv2 = st.columns(2)
            with col_inv1:
                tgl_default = datetime.now().strftime("%d %B %Y")
                tgl_invoice = st.text_input("Tanggal Invoice:", value=get_val('tgl_invoice', tgl_default))
                current_state['tgl_invoice'] = tgl_invoice
                
                no_default = f"INV{datetime.now().strftime('%y')}-001"
                no_invoice = st.text_input("No. Invoice:", value=get_val('no_invoice', no_default))
                current_state['no_invoice'] = no_invoice
                
            with col_inv2:
                nama_klien = st.text_input("Kepada (Nama Klien / PT):", value=get_val('nama_klien_formal', "PT. SARI AGROTAMA PERSADA"))
                current_state['nama_klien_formal'] = nama_klien
                
                alamat_klien = st.text_area("Alamat Klien:", value=get_val('alamat_klien_formal', "GEDUNG MULTIVISION TOWER, LT. 15\nJL KUNINGAN MULIA LOT 9B\nJAKARTA SELATAN DKI JAKARTA 00000"), height=100)
                current_state['alamat_klien_formal'] = alamat_klien

            st.markdown("#### 📝 Detail Tagihan")
            col_tag1, col_tag2, col_tag3 = st.columns([2, 1, 1])
            with col_tag1:
                keterangan = st.text_input("Keterangan Pekerjaan:", value=get_val('keterangan_formal', "Biaya angkut barang Fortune Pillow Pack 500 ml x 24 Bags (SPK No.2080744206)"))
                current_state['keterangan_formal'] = keterangan
            with col_tag2:
                harga_kg = st.number_input("Harga / KG (Rp):", min_value=0.0, value=float(get_val('harga_kg', 325.0)), step=10.0)
                current_state['harga_kg'] = harga_kg
            with col_tag3:
                banyak_kg = st.number_input("Banyaknya / KG:", min_value=0.0, value=float(get_val('banyak_kg', 11440.0)), step=100.0)
                current_state['banyak_kg'] = banyak_kg

            jumlah = harga_kg * banyak_kg
            ppn = jumlah * 0.11
            total_akhir = jumlah + ppn

            st.markdown("---")
            st.markdown("#### 🧮 Hasil Perhitungan Otomatis")
            col_res1, col_res2, col_res3 = st.columns(3)
            col_res1.metric("Sub Total", f"Rp {jumlah:,.0f}")
            col_res2.metric("PPN (11%)", f"Rp {ppn:,.0f}")
            col_res3.metric("Total Tagihan", f"Rp {total_akhir:,.0f}")
            
            terbilang_teks = format_terbilang(total_akhir)
            st.info(f"**Terbilang:** {terbilang_teks}")
            
            st.markdown("---")
            
            # FITUR DATABASE CSV
            if st.button("🚀 MENCETAK INVOICE KE BUKU BESAR (CSV)", type="primary"):
                try:
                    new_data = pd.DataFrame([{
                        "Waktu_Input": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "No_Invoice": no_invoice, "Nama_Klien": nama_klien,
                        "Keterangan": keterangan, "Harga_KG": harga_kg, "Banyaknya_KG": banyak_kg,
                        "Jumlah": jumlah, "PPN": ppn, "Total_Akhir": total_akhir
                    }])
                    updated_df = pd.concat([existing_data, new_data], ignore_index=True)
                    updated_df.to_csv(NAMA_FILE_DB, index=False)
                    st.success("✅ BERHASIL! Invoice telah dicatat ke Laporan Database Lokal.")
                    st.balloons()
                except Exception as e:
                    st.error(f"❌ Gagal menyimpan data: {e}")

            st.markdown("#### 🖨️ Cetak & Unduh Invoice Klien (Format Gambar PNG)")
            img_formal = buat_invoice_formal(no_invoice, tgl_invoice, nama_klien, alamat_klien, keterangan, harga_kg, banyak_kg)
            st.download_button(label="🖨️ UNDUH GAMBAR INVOICE (SIAP CETAK)", data=img_formal, file_name=f"{no_invoice.replace('/','_')}_{nama_klien}.png", mime="image/png", type="primary")

except Exception as e:
    st.error(f"Waduh, ada masalah internal dengan file lokal: {e}")

# --- EKSEKUSI AUTO-SAVE DI BELAKANG LAYAR ---
saved_state.update(current_state)
try:
    with open(STATE_FILE_INPUTS, "w") as f:
        json.dump(saved_state, f)
except:
    pass