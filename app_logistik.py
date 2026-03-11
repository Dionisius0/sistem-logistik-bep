import streamlit as st
import pandas as pd

# --- BAGIAN 1: Judul dan Tampilan Dasar ---
st.set_page_config(page_title="Tango Logistik - Dasbor Operasional", layout="wide")
st.title("🚚 Sistem Manajemen Ekspedisi (Tango Logistik)")
st.write("Aplikasi Pintar Pengendalian Biaya, Target Laba, dan KPI Armada.")

try:
    # --- BAGIAN 2: Membaca Semua Data CSV ---
    data_mobil = pd.read_csv("data mobil.csv", sep=None, engine="python")
    data_rute = pd.read_csv("BEP per trip.csv", sep=None, engine="python", skiprows=1)
    
    # Mencoba membaca data baru (Pajak & Penyusutan)
    try:
        data_pajak = pd.read_csv("pajak mobil.csv", sep=None, engine="python")
        data_susut = pd.read_csv("penyusutan kendaraan.csv", sep=None, engine="python")
    except:
        data_pajak = pd.DataFrame()
        data_susut = pd.DataFrame()
        st.warning("Data 'pajak mobil.csv' atau 'penyusutan kendaraan.csv' belum ditemukan di folder. Dasbor Halaman 3 mungkin tidak tampil penuh.")

    # Pembersihan Data Rute
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
    menu_halaman = st.sidebar.radio("Pilih Halaman Analisis:", [
        "📊 Kalkulator BEP (Utama)", 
        "🎯 Target Laba & Jadwal Operasi",
        "📈 Dashboard Eksekutif & KPI"
    ])
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
            st.info("💡 Input Data Keuangan (Terhubung dengan Data Excel)")
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
            st.write("*Biaya tetap ditarik otomatis dari data global Excel.*")
            biaya_tetap_global = st.number_input("Total Biaya Tetap Operasional (Rp):", value=float(estimasi_total_fixed), step=1000000.0)
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
        data_laporan_jadwal = []

        for i, hari in enumerate(hari_kerja):
            with kolom_hari[i % 3]:
                st.markdown(f"### 🗓️ {hari}")
                mobil_pilihan = st.multiselect(f"Pilih Armada:", daftar_armada_fisik, key=f"mobil_{hari}")
                
                for index, mobil in enumerate(mobil_pilihan):
                    bg_color = "#1e2129" if index % 2 == 0 else "#262b35"
                    tipe_spesifik = mobil.split(' - ')[1] if ' - ' in mobil else mobil
                    tm_lower = str(tipe_spesifik).lower()
                    if 'pu' in tm_lower or 'pick' in tm_lower: kategori_rute = 'pick up'
                    elif '71' in tm_lower or '100' in tm_lower or 'engkel' in tm_lower: kategori_rute = 'engkel'
                    elif 'tronton' in tm_lower: kategori_rute = 'tronton'
                    else: kategori_rute = 'truk standar'
                    
                    rute_terfilter_mobil_ini = [r for r in daftar_semua_rute if kategori_rute in str(r).lower()]
                    if not rute_terfilter_mobil_ini: rute_terfilter_mobil_ini = daftar_semua_rute

                    with st.container(border=True):
                        st.markdown(f"""<p style="margin:0; color:#00d4ff; font-weight:bold;">↳ {mobil}</p>
                                    <p style="margin:0; font-size:0.8em; color:#888; margin-bottom:10px;">Golongan: {kategori_rute.title()}</p>""", unsafe_allow_html=True)
                        rute_dipilih = st.selectbox("Tentukan Rute:", rute_terfilter_mobil_ini, key=f"rute_{hari}_{mobil}")
                        jml_trip = st.number_input("Jml Trip:", min_value=1, value=1, step=1, key=f"trip_{hari}_{mobil}")

                    harga_rute_aktual = df_rute_unik[df_rute_unik['Label_Rute'] == rute_dipilih]['Harga_Bersih'].values[0]
                    cost_rute_aktual = df_rute_unik[df_rute_unik['Label_Rute'] == rute_dipilih]['Cost_Bersih'].values[0]
                    
                    pendapatan_mingguan += (harga_rute_aktual * jml_trip)
                    biaya_var_mingguan += (cost_rute_aktual * jml_trip)
                    total_trip_mingguan += jml_trip
                    
                    data_laporan_jadwal.append({
                        "Hari Beroperasi": hari, "Armada": mobil, "Rute Tujuan": rute_dipilih,
                        "Jumlah Trip": jml_trip, "Estimasi Pendapatan": harga_rute_aktual * jml_trip
                    })
        
        st.markdown("---")
        st.subheader("⛽ Analisis Sensitivitas & Proyeksi Akhir")
        simulasi_persen = st.slider("Kenaikan/Penurunan Biaya Variabel (%)", min_value=-20, max_value=50, value=0, step=5)

        total_trip_bulanan = total_trip_mingguan * 4
        pendapatan_bulanan = pendapatan_mingguan * 4
        biaya_var_bulanan = biaya_var_mingguan * 4
        biaya_var_setelah_simulasi = biaya_var_bulanan * (1 + (simulasi_persen / 100.0))
        biaya_total_bulanan = biaya_tetap_global + biaya_var_setelah_simulasi
        laba_rugi_aktual = pendapatan_bulanan - biaya_total_bulanan
        
        col_k1, col_k2, col_k3 = st.columns(3)
        col_k1.metric("Proyeksi Pendapatan", f"Rp {pendapatan_bulanan:,.0f}")
        if simulasi_persen != 0: col_k2.metric("Total Biaya (Simulasi)", f"Rp {biaya_total_bulanan:,.0f}", f"{simulasi_persen}%", delta_color="inverse")
        else: col_k2.metric("Total Biaya", f"Rp {biaya_total_bulanan:,.0f}")
        
        if laba_rugi_aktual >= target_laba: col_k3.metric("🎉 Laba Bersih", f"Rp {laba_rugi_aktual:,.0f}")
        elif laba_rugi_aktual > 0: col_k3.metric("⚠️ Laba Bersih", f"Rp {laba_rugi_aktual:,.0f}")
        else: col_k3.metric("🚨 RUGI", f"Rp {laba_rugi_aktual:,.0f}")

    # =====================================================================
    # HALAMAN 3: DASHBOARD EKSEKUTIF & KPI ARMADA (FITUR BARU)
    # =====================================================================
    elif menu_halaman == "📈 Dashboard Eksekutif & KPI":
        st.subheader("📈 Pusat Kendali Operasional (Dashboard Eksekutif)")
        st.write("Ruang kontrol untuk memantau utilitas aset, status peremajaan kendaraan, dan manajemen biaya jalan supir.")
        
        # Saring armada berdasarkan No. Polisi
        if 'No. Polisi' in data_mobil.columns:
            data_valid = data_mobil.dropna(subset=['No. Polisi', 'Tipe Mobil'])
            daftar_armada_fisik = data_valid.apply(lambda row: f"{str(row['No. Polisi']).strip()} - {str(row['Tipe Mobil']).strip()}", axis=1).tolist()
        else:
            daftar_armada_fisik = ["Data pelat nomor tidak ditemukan"]

        col_nav1, col_nav2 = st.columns([1, 2])
        with col_nav1:
            st.info("🔍 Pilih Armada untuk Dievaluasi:")
            armada_diperiksa = st.selectbox("Pilih Pelat Nomor:", daftar_armada_fisik)
            pelat_saja = armada_diperiksa.split(' - ')[0] if ' - ' in armada_diperiksa else armada_diperiksa
            
            # FITUR 1: Utilitas Armada (Asumsi 26 Hari Kerja)
            st.markdown("### 📊 Fleet Utilization")
            hari_kerja_sebulan = 26
            trip_aktual = st.number_input("Total Trip armada ini bulan lalu:", min_value=0, value=20, step=1)
            utilitas = (trip_aktual / hari_kerja_sebulan) * 100
            
            if utilitas >= 80: st.success(f"Tingkat Utilitas: **{utilitas:.1f}%** (Sangat Baik)")
            elif utilitas >= 50: st.warning(f"Tingkat Utilitas: **{utilitas:.1f}%** (Perlu Ditingkatkan)")
            else: st.error(f"Tingkat Utilitas: **{utilitas:.1f}%** (Aset Menganggur!)")

        with col_nav2:
            st.success("💼 Profil Aset & Total Cost of Ownership (TCO)")
            
            # Mencari data Pajak & Penyusutan berdasarkan Pelat Nomor
            status_pajak = "Data tidak ditemukan"
            status_susut = "Data tidak ditemukan"
            nilai_susut = 0.0
            
            if not data_pajak.empty:
                # Cari baris yang mengandung pelat nomor ini
                baris_pajak = data_pajak[data_pajak.astype(str).apply(lambda x: x.str.contains(pelat_saja, case=False, na=False)).any(axis=1)]
                if not baris_pajak.empty:
                    # Ambil kolom terakhir yang biasanya berisi total pajak
                    col_total_pajak = baris_pajak.columns[-1]
                    total_pajak = bersihkan_rupiah(baris_pajak.iloc[0][col_total_pajak])
                    status_pajak = f"Rp {total_pajak:,.0f} / Tahun"
            
            if not data_susut.empty:
                baris_susut = data_susut[data_susut.astype(str).apply(lambda x: x.str.contains(pelat_saja, case=False, na=False)).any(axis=1)]
                if not baris_susut.empty:
                    # Ambil keterangan Lunas/Aktif
                    col_ket = next((c for c in baris_susut.columns if 'keterangan' in str(c).lower()), None)
                    col_dep = next((c for c in baris_susut.columns if 'depresiasi' in str(c).lower()), None)
                    
                    if col_ket: status_susut = str(baris_susut.iloc[0][col_ket])
                    if col_dep: nilai_susut = bersihkan_rupiah(baris_susut.iloc[0][col_dep])

            st.write(f"**Status Kendaraan:** {status_susut}")
            st.write(f"**Beban Penyusutan Tahunan:** Rp {nilai_susut:,.0f}")
            st.write(f"**Estimasi Pajak Tahunan:** {status_pajak}")
            
            if 'lunas' in status_susut.lower() or 'mati' in status_susut.lower():
                st.info("💡 **Rekomendasi Manajerial:** Nilai buku kendaraan ini sudah habis (Lunas). Pertimbangkan anggaran untuk peremajaan unit (beli baru) agar biaya pemeliharaan (*maintenance*) tidak membengkak di masa depan.")

        st.markdown("---")
        st.subheader("🧾 Kalkulator Surat Perintah Jalan (SPJ) & Kas Bon Supir")
        st.write("Pecah *Total Variable Cost* dari rute menjadi uang jalan (Kas Bon) yang riil untuk supir.")
        
        col_spj1, col_spj2 = st.columns([1, 1])
        with col_spj1:
            rute_spj = st.selectbox("Pilih Rute untuk SPJ:", daftar_semua_rute)
            cost_rute_spj = df_rute_unik[df_rute_unik['Label_Rute'] == rute_spj]['Cost_Bersih'].values[0]
            st.metric("Total Biaya Variabel (Per Trip)", f"Rp {cost_rute_spj:,.0f}")
            
        with col_spj2:
            st.write("**Alokasi Persentase Uang Jalan:**")
            st.write("*(Sesuaikan persentase di bawah ini dengan kebijakan operasional perusahaan)*")
            pct_solar = st.slider("Solar / BBM (%)", 0, 100, 45)
            pct_makan = st.slider("Uang Jajan Sopir & Kernet (%)", 0, 100, 25)
            pct_parkir = st.slider("Parkir & Retribusi (%)", 0, 100, 10)
            
            # Sisa persentase untuk pemeliharaan/keausan (ditahan perusahaan)
            pct_sisa = 100 - (pct_solar + pct_makan + pct_parkir)
            
            st.write("---")
            st.write("💵 **Rincian Uang yang Dibawa Supir:**")
            st.write(f"- Uang Solar: **Rp {(cost_rute_spj * pct_solar / 100):,.0f}**")
            st.write(f"- Uang Makan: **Rp {(cost_rute_spj * pct_makan / 100):,.0f}**")
            st.write(f"- Parkir/Tol: **Rp {(cost_rute_spj * pct_parkir / 100):,.0f}**")
            st.write(f"💰 **Total Kas Bon Supir: Rp {(cost_rute_spj * (pct_solar+pct_makan+pct_parkir) / 100):,.0f}**")
            if pct_sisa > 0:
                st.caption(f"*Sisa Rp {(cost_rute_spj * pct_sisa / 100):,.0f} ({pct_sisa}%) ditahan perusahaan untuk pemeliharaan berkala dan keausan ban.*")
            elif pct_sisa < 0:
                st.error("Total persentase melebihi 100%! Silakan kurangi slider.")

except Exception as e:
    st.error(f"Waduh, ada masalah internal: {e}")