import streamlit as st
import pandas as pd

# --- BAGIAN 1: Judul dan Tampilan Dasar ---
st.set_page_config(page_title="Sistem Manajemen Logistik", layout="wide")
st.title("🚚 Sistem Manajemen Tango Logistik ")
st.write("Aplikasi Pintar untuk Menghitung BEP dan Target Laba Operasional Armada.")

try:
    # --- BAGIAN 2: Membaca & Membersihkan Data CSV ---
    data_mobil = pd.read_csv("data mobil.csv", sep=None, engine="python")
    data_rute = pd.read_csv("BEP per trip.csv", sep=None, engine="python", skiprows=1)
    
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
        if teks in ['none', 'nan', 'berangkat', 'tujuan'] or 'keberangkatan' in teks: 
            return None
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

    # --- EKSTRAKSI HARGA & BIAYA ---
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
    
    data_rute['Harga_Bersih'] = data_rute[col_harga].apply(bersihkan_rupiah) if col_harga else 1500000.0
    data_rute['Cost_Bersih'] = data_rute[col_cost].apply(bersihkan_rupiah) if col_cost else 500000.0

    if nama_kol_tipe:
        data_rute['Label_Rute'] = data_rute['Titik Keberangkatan Bersih'].astype(str) + " ➡️ " + data_rute[nama_tujuan].astype(str) + " (" + data_rute[nama_kol_tipe].astype(str) + ")"
    else:
        data_rute['Label_Rute'] = data_rute['Titik Keberangkatan Bersih'].astype(str) + " ➡️ " + data_rute[nama_tujuan].astype(str)

    df_rute_unik = data_rute.drop_duplicates(subset=['Label_Rute']).copy()
    daftar_semua_rute = sorted(df_rute_unik['Label_Rute'].dropna().tolist())

    # --- BAGIAN 3: NAVIGASI ---
    st.sidebar.title("🧭 Menu Navigasi")
    menu_halaman = st.sidebar.radio("Pilih Halaman Analisis:", ["📊 Kalkulator BEP (Utama)", "🎯 Target Laba & Jadwal Operasi"])
    st.sidebar.markdown("---")

    # =====================================================================
    # HALAMAN 1: KALKULATOR BEP
    # =====================================================================
    if menu_halaman == "📊 Kalkulator BEP (Utama)":
        st.sidebar.header("⚙️ Pengaturan Data Rute")
        pilihan_mobil_list = data_mobil['Tipe Mobil'].dropna().unique().tolist()
        mobil_terpilih_bep = st.sidebar.selectbox("Pilih Armada (Spesifikasi):", pilihan_mobil_list)
        
        data_rute_spesifik = data_rute.copy()
        if 'tronton' in str(mobil_terpilih_bep).lower() and 'tujuan' in kolom_rute_lower:
            mask_pontianak = data_rute_spesifik[nama_tujuan].astype(str).str.lower().str.contains('pontianak')
            if mask_pontianak.any(): data_rute_spesifik = data_rute_spesifik[mask_pontianak]
        
        pilihan_berangkat = sorted(data_rute_spesifik['Titik Keberangkatan Bersih'].unique().tolist())
        if not pilihan_berangkat: pilihan_berangkat = sorted(data_rute['Titik Keberangkatan Bersih'].unique().tolist())
        berangkat_terpilih = st.sidebar.selectbox("Titik Keberangkatan:", pilihan_berangkat)
        rute_terfilter = data_rute_spesifik[data_rute_spesifik['Titik Keberangkatan Bersih'] == berangkat_terpilih]
        
        if 'tujuan' in kolom_rute_lower:
            pilihan_tujuan = rute_terfilter[nama_tujuan].dropna().unique().tolist()
            tujuan_terpilih = st.sidebar.selectbox("Rute Tujuan:", pilihan_tujuan)
            rute_tujuan_saja = rute_terfilter[rute_terfilter[nama_tujuan] == tujuan_terpilih]
        else:
            tujuan_terpilih = "Semua Rute"
            rute_tujuan_saja = rute_terfilter

        if nama_kol_tipe and not rute_tujuan_saja.empty:
            pilihan_kategori = rute_tujuan_saja[nama_kol_tipe].dropna().unique().tolist()
            kategori_terpilih = st.sidebar.selectbox("Kategori Kendaraan:", pilihan_kategori)
            detail_rute_final = rute_tujuan_saja[rute_tujuan_saja[nama_kol_tipe] == kategori_terpilih]
        else:
            detail_rute_final = rute_tujuan_saja
            kategori_terpilih = "Umum"

        # Tarik biaya otomatis
        def_tetap, def_var, def_harga = 5000000.0, 500000.0, 1500000.0
        if not detail_rute_final.empty:
            baris_data = detail_rute_final.iloc[0] 
            col_f = next((c for c in detail_rute_final.columns if any(k in str(c).lower().replace('\n', ' ') for k in ['fixed', 'biaya tetap'])), None)
            if col_f: 
                v = bersihkan_rupiah(baris_data[col_f])
                if v: def_tetap = v
            def_var = baris_data['Cost_Bersih']
            def_harga = baris_data['Harga_Bersih']

        st.subheader(f"📊 Detail Operasional BEP: **{mobil_terpilih_bep}**")
        col_m, col_r = st.columns(2)
        with col_m:
            st.write("**Data Spesifikasi Kendaraan:**")
            st.dataframe(data_mobil[data_mobil['Tipe Mobil'] == mobil_terpilih_bep])
        with col_r:
            st.write(f"**Data Rute ({berangkat_terpilih} ➡️ {tujuan_terpilih}) - {kategori_terpilih}:**")
            st.dataframe(detail_rute_final.drop(columns=['Titik Keberangkatan Bersih', 'Label_Rute', 'Harga_Bersih', 'Cost_Bersih'], errors='ignore'))
        
        st.markdown("---")
        st.subheader("🧮 Kalkulator Break Even Point (BEP)")
        col1, col2 = st.columns(2)
        with col1:
            st.info("💡 Input Data Keuangan (Otomatis)")
            biaya_tetap = st.number_input("Total Biaya Tetap (Rp):", min_value=0.0, value=float(def_tetap), step=100000.0)
            biaya_variabel = st.number_input("Total Cost per Trip (Rp):", min_value=0.0, value=float(def_var), step=10000.0)
            harga_jual = st.number_input("Harga/Pendapatan per Trip (Rp):", min_value=0.0, value=float(def_harga), step=50000.0)
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
            target_laba = st.number_input("Target Laba Bulanan (Rp):", min_value=0.0, value=10000000.0, step=1000000.0)
            biaya_tetap_global = st.number_input("Total Biaya Tetap Operasional (Rp):", value=5000000.0, step=100000.0)
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
        
        # Saring armada agar tidak muncul nan-nan
        if 'No. Polisi' in data_mobil.columns:
            data_valid = data_mobil.dropna(subset=['No. Polisi', 'Tipe Mobil'])
            daftar_armada_fisik = data_valid.apply(lambda row: f"{str(row['No. Polisi']).strip()} - {str(row['Tipe Mobil']).strip()}", axis=1).tolist()
        else:
            daftar_armada_fisik = data_mobil['Tipe Mobil'].dropna().unique().tolist()
        
        hari_kerja = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu"]
        kolom_hari = st.columns(3)
        pendapatan_mingguan, biaya_var_mingguan, total_trip_mingguan = 0.0, 0.0, 0
        
        for i, hari in enumerate(hari_kerja):
            with kolom_hari[i % 3]:
                st.markdown(f"### 🗓️ {hari}")
                mobil_pilihan = st.multiselect(f"Pilih Armada:", daftar_armada_fisik, key=f"mobil_{hari}")
                
                for index, mobil in enumerate(mobil_pilihan):
                    # Penentuan warna selang-seling
                    bg_color = "#1e2129" if index % 2 == 0 else "#262b35"
                    
                    # Logika penyaringan rute
                    tipe_spesifik = mobil.split(' - ')[1] if ' - ' in mobil else mobil
                    tm_lower = str(tipe_spesifik).lower()
                    if 'pu' in tm_lower or 'pick' in tm_lower: kategori_rute = 'pick up'
                    elif '71' in tm_lower or '100' in tm_lower or 'engkel' in tm_lower: kategori_rute = 'engkel'
                    elif 'tronton' in tm_lower: kategori_rute = 'tronton'
                    else: kategori_rute = 'truk standar'
                    
                    rute_terfilter_mobil_ini = [r for r in daftar_semua_rute if kategori_rute in str(r).lower()]
                    if not rute_terfilter_mobil_ini: rute_terfilter_mobil_ini = daftar_semua_rute

                    # PEMBUNGKUS KARTU (Satu Border Mencakup Semua Input Mobil Ini)
                    # Menggunakan st.container dengan border=True (Fitur Streamlit terbaru)
                    with st.container(border=True):
                        # Kita gunakan warna background berbeda untuk selang-seling via CSS sederhana
                        st.markdown(f"""<p style="margin:0; color:#00d4ff; font-weight:bold;">↳ {mobil}</p>
                                    <p style="margin:0; font-size:0.8em; color:#888; margin-bottom:10px;">Golongan: {kategori_rute.title()}</p>""", unsafe_allow_html=True)
                        
                        rute_dipilih = st.selectbox("Tentukan Rute:", rute_terfilter_mobil_ini, key=f"rute_{hari}_{mobil}")
                        jml_trip = st.number_input("Jml Trip:", min_value=1, value=1, step=1, key=f"trip_{hari}_{mobil}")

                    # Kalkulasi
                    harga_rute_aktual = df_rute_unik[df_rute_unik['Label_Rute'] == rute_dipilih]['Harga_Bersih'].values[0]
                    cost_rute_aktual = df_rute_unik[df_rute_unik['Label_Rute'] == rute_dipilih]['Cost_Bersih'].values[0]
                    pendapatan_mingguan += (harga_rute_aktual * jml_trip)
                    biaya_var_mingguan += (cost_rute_aktual * jml_trip)
                    total_trip_mingguan += jml_trip
        
        # Proyeksi Bulanan
        total_trip_bulanan = total_trip_mingguan * 4
        pendapatan_bulanan = pendapatan_mingguan * 4
        biaya_var_bulanan = biaya_var_mingguan * 4
        biaya_total_bulanan = biaya_tetap_global + biaya_var_bulanan
        laba_rugi_aktual = pendapatan_bulanan - biaya_total_bulanan
        
        st.markdown("---")
        st.subheader("🏁 Kesimpulan Proyeksi Keuangan Nyata")
        col_k1, col_k2, col_k3 = st.columns(3)
        col_k1.metric("Proyeksi Pendapatan", f"Rp {pendapatan_bulanan:,.0f}")
        col_k2.metric("Proyeksi Total Biaya", f"Rp {biaya_total_bulanan:,.0f}")
        
        if laba_rugi_aktual >= target_laba:
            col_k3.metric("🎉 Proyeksi Laba Bersih", f"Rp {laba_rugi_aktual:,.0f}")
            st.success("✅ **Laba Sesuai Target!**")
        elif laba_rugi_aktual > 0:
            col_k3.metric("⚠️ Proyeksi Laba Bersih", f"Rp {laba_rugi_aktual:,.0f}")
            st.warning("⚠️ **Target Belum Tercapai.**")
        else:
            col_k3.metric("🚨 Proyeksi RUGI", f"Rp {laba_rugi_aktual:,.0f}")
            st.error("🚨 **Bahaya RUGI!**")

except Exception as e:
    st.error(f"Waduh, ada masalah internal: {e}")