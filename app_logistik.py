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
        "📈 Dashboard Eksekutif & KPI",
        "⚖️ Analisis Kinerja & Kapasitas (Ton-KM)",
        "🏦 Keuangan Lanjutan & Aset"
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
            st.info("💡 Input Data Keuangan")
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
        pendapatan_backhaul_mingguan = 0.0
        data_laporan_jadwal = []

        for i, hari in enumerate(hari_kerja):
            with kolom_hari[i % 3]:
                st.markdown(f"### 🗓️ {hari}")
                mobil_pilihan = st.multiselect(f"Pilih Armada:", daftar_armada_fisik, key=f"mobil_{hari}")
                
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
                        rute_dipilih = st.selectbox("Tentukan Rute:", rute_terfilter_mobil_ini, key=f"rute_{hari}_{mobil}")
                        jml_trip = st.number_input("Jml Trip:", min_value=1, value=1, step=1, key=f"trip_{hari}_{mobil}")
                        
                        ada_muatan_balik = st.checkbox("📦 Ada Muatan Balik?", key=f"backhaul_{hari}_{mobil}")
                        pendapatan_ekstra_bersih = 0.0
                        if ada_muatan_balik:
                            pendapatan_ekstra_kotor = st.number_input("Harga Borongan Muatan Balik (Rp):", min_value=0.0, value=500000.0, step=100000.0, key=f"uang_balik_{hari}_{mobil}")
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

        if len(data_laporan_jadwal) > 0:
            df_laporan = pd.DataFrame(data_laporan_jadwal)
            csv_data = df_laporan.to_csv(index=False).encode('utf-8')
            st.download_button(label="📥 Unduh Laporan Jadwal (CSV)", data=csv_data, file_name="Jadwal_Logistik_Tango.csv", mime="text/csv")

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
            armada_diperiksa = st.selectbox("Pilih Pelat Nomor:", daftar_armada_fisik)
            pelat_saja = armada_diperiksa.split(' - ')[0] if ' - ' in armada_diperiksa else armada_diperiksa
            
            st.markdown("### 📊 Fleet Utilization")
            hari_kerja_sebulan = 26
            trip_aktual = st.number_input("Total Trip armada ini bulan lalu:", min_value=0, value=20, step=1)
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
            rute_spj = st.selectbox("Pilih Rute untuk SPJ:", daftar_semua_rute)
            cost_rute_spj = df_rute_unik[df_rute_unik['Label_Rute'] == rute_spj]['Cost_Bersih'].values[0]
            st.metric("Total Biaya Variabel (Per Trip)", f"Rp {cost_rute_spj:,.0f}")
            
        with col_spj2:
            st.write("**Alokasi Persentase Uang Jalan:**")
            pct_solar = st.slider("Solar / BBM (%)", 0, 100, 45)
            pct_makan = st.slider("Uang Jajan Sopir & Kernet (%)", 0, 100, 25)
            pct_parkir = st.slider("Parkir & Retribusi (%)", 0, 100, 10)
            
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
            armada_ton = st.selectbox("Pilih Tipe Armada:", pilihan_mobil_list)
            
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
            
            kapasitas_ton = st.number_input(f"Kapasitas Maksimal (Ton):", min_value=0.5, value=float(default_tonase), step=0.5)

        with col_ton2:
            st.info("🛣️ 2. Parameter Rute & Jarak")
            rute_terfilter_ton = [r for r in daftar_semua_rute if kategori_rute in str(r).lower()]
            if not rute_terfilter_ton: 
                rute_terfilter_ton = daftar_semua_rute
                
            rute_ton = st.selectbox("Pilih Rute Analisis:", rute_terfilter_ton)
            
            if rute_ton:
                cost_rute_ton = df_rute_unik[df_rute_unik['Label_Rute'] == rute_ton]['Cost_Bersih'].values[0]
                harga_rute_ton = df_rute_unik[df_rute_unik['Label_Rute'] == rute_ton]['Harga_Bersih'].values[0]
            else:
                cost_rute_ton, harga_rute_ton = 0, 0
                
            jarak_km = st.number_input("Jarak Tempuh Rute (Kilometer):", min_value=1.0, value=150.0, step=10.0)

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
                st.success(f"💡 **Kesimpulan Bisnis:** Untuk setiap 1 Ton barang yang dipindahkan sejauh 1 Kilometer menggunakan {armada_ton}, perusahaan mengeluarkan modal **Rp {biaya_per_ton_km:,.0f}** dan menikmati laba bersih **Rp {margin_per_ton_km:,.0f}**.")
            else:
                col_res3.metric("🚨 Margin per Ton-KM (RUGI)", f"Rp {margin_per_ton_km:,.0f}")
                st.error("⚠️ **Peringatan:** Armada ini terlalu mahal/boros untuk jarak sejauh ini dengan kapasitas tersebut.")

    # =====================================================================
    # HALAMAN 5: KEUANGAN LANJUTAN & ASET (UPDATE: VOLUME CM3 & ARMADA)
    # =====================================================================
    elif menu_halaman == "🏦 Keuangan Lanjutan & Aset":
        st.subheader("🏦 Manajemen Keuangan Lanjutan")
        st.write("Gunakan menu ini untuk menghitung tabungan pemeliharaan aset, simulasi modal kerja, dan pembagian invoice konsolidasi.")
        
        tab1, tab2, tab3 = st.tabs(["🛞 Kalkulator Pemeliharaan Aset", "💸 Simulator Arus Kas", "🧾 Invoice LTL (Konsolidasi Muatan)"])
        
        with tab1:
            st.markdown("### 🛞 Manajemen Keausan Ban & Suku Cadang")
            col_ban1, col_ban2 = st.columns(2)
            with col_ban1:
                harga_set_ban = st.number_input("Harga 1 Set Ban (Rp):", min_value=1000000.0, value=15000000.0, step=500000.0)
                umur_ban_km = st.number_input("Estimasi Umur Ban (Kilometer):", min_value=1000.0, value=60000.0, step=5000.0)
            
            with col_ban2:
                jarak_rute_trip = st.number_input("Jarak Tempuh Rute yang Sering Dilalui (KM per Trip PP):", min_value=10.0, value=300.0, step=10.0)
                
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
                proyeksi_biaya_bulanan = st.number_input("Estimasi Total Biaya Operasional Sebulan (Rp):", min_value=1000000.0, value=250000000.0, step=10000000.0)
                top_klien = st.selectbox("Rata-rata Klien Membayar Invoice (TOP):", [
                    "0 Hari (Cash / Tunai Keras)", "14 Hari", "30 Hari (1 Bulan)", "60 Hari (2 Bulan)", "90 Hari (3 Bulan)"
                ], index=2)
            
            angka_hari = int(top_klien.split(' ')[0])
            
            with col_cash2:
                kebutuhan_modal_kerja = (proyeksi_biaya_bulanan / 30) * angka_hari
                st.metric("Dana Tunai (Modal Kerja) yang Harus Disiapkan", f"Rp {kebutuhan_modal_kerja:,.0f}")
                if angka_hari == 0: st.success("✅ Bisnis yang sangat sehat! Klien membayar tunai.")
                elif angka_hari > 30: st.error(f"🚨 Siapkan minimal **Rp {kebutuhan_modal_kerja:,.0f}** di rekening untuk talangan.")
                else: st.info(f"💡 Pastikan arus kas memiliki penyangga setidaknya **Rp {kebutuhan_modal_kerja:,.0f}**.")

        # --- ISI TAB 3 (BARU): INVOICE KONSOLIDASI (LTL) DENGAN VOLUME CM3 ---
        with tab3:
            st.markdown("### 🧾 Kalkulator Tagihan Pro-rata (Sistem Pecah Muatan Volume)")
            st.info("Fitur ini membagi Harga Trip secara adil kepada klien berdasarkan persentase volume muatan (cm³), sehingga pendapatan tetap utuh meskipun ada ruang kosong di bak truk.")
            
            col_inv1, col_inv2, col_inv3 = st.columns(3)
            with col_inv1:
                # Mengambil daftar armada dari data excel
                pilihan_mobil_list_inv = data_mobil['Tipe Mobil'].dropna().unique().tolist() if 'Tipe Mobil' in data_mobil.columns else ["Truk Default"]
                armada_inv = st.selectbox("Pilih Armada yang Berangkat:", pilihan_mobil_list_inv, key="armada_inv")
            with col_inv2:
                harga_target_trip = st.number_input("Target Total Harga 1 Trip (Rp):", min_value=100000.0, value=3000000.0, step=100000.0)
            with col_inv3:
                # Default 12 Juta cm3 (12 CBM) untuk estimasi truk engkel standar
                kapasitas_truk_inv = st.number_input("Kapasitas Volume Truk (cm³):", min_value=1.0, value=12000000.0, step=500000.0, format="%.0f")
            
            st.markdown(f"**📝 Masukkan Rincian Volume Klien yang dimuat di {armada_inv}:**")
            col_klien1, col_klien2, col_klien3 = st.columns(3)
            with col_klien1:
                klien_1 = st.text_input("Nama Klien 1:", value="Perusahaan A (Pemangkat)")
                vol_1 = st.number_input("Volume Muatan Klien 1 (cm³):", min_value=0.0, value=3000000.0, step=100000.0, format="%.0f")
            with col_klien2:
                klien_2 = st.text_input("Nama Klien 2:", value="Perusahaan B (Singkawang)")
                vol_2 = st.number_input("Volume Muatan Klien 2 (cm³):", min_value=0.0, value=4000000.0, step=100000.0, format="%.0f")
            with col_klien3:
                klien_3 = st.text_input("Nama Klien 3:", value="Perusahaan C (Sambas)")
                vol_3 = st.number_input("Volume Muatan Klien 3 (cm³):", min_value=0.0, value=2500000.0, step=100000.0, format="%.0f")
            
            total_muatan_aktual = vol_1 + vol_2 + vol_3
            sisa_kapasitas = kapasitas_truk_inv - total_muatan_aktual
            
            st.markdown("---")
            if total_muatan_aktual > 0:
                if total_muatan_aktual > kapasitas_truk_inv:
                    st.error(f"🚨 OVERLOAD! Total muatan ({total_muatan_aktual:,.0f} cm³) melebihi kapasitas maksimum {armada_inv} ({kapasitas_truk_inv:,.0f} cm³).")
                else:
                    st.success(f"📊 **Analisis Kapasitas:** Truk terisi {total_muatan_aktual:,.0f} cm³. Sisa ruang kosong (Gap): {sisa_kapasitas:,.0f} cm³.")
                    
                    # Logika Prorata Murni (Membagi 100% Harga Trip ke muatan yang ada)
                    pct_1 = vol_1 / total_muatan_aktual
                    pct_2 = vol_2 / total_muatan_aktual
                    pct_3 = vol_3 / total_muatan_aktual
                    
                    tagihan_1 = pct_1 * harga_target_trip
                    tagihan_2 = pct_2 * harga_target_trip
                    tagihan_3 = pct_3 * harga_target_trip
                    
                    st.markdown("**💵 Rincian Tagihan Invoice (Pro-rata Berdasarkan Volume):**")
                    col_tag1, col_tag2, col_tag3 = st.columns(3)
                    
                    if vol_1 > 0:
                        col_tag1.metric(f"Tagihan {klien_1}", f"Rp {tagihan_1:,.0f}", f"{pct_1*100:.1f}% dari Volume Terpakai")
                    if vol_2 > 0:
                        col_tag2.metric(f"Tagihan {klien_2}", f"Rp {tagihan_2:,.0f}", f"{pct_2*100:.1f}% dari Volume Terpakai")
                    if vol_3 > 0:
                        col_tag3.metric(f"Tagihan {klien_3}", f"Rp {tagihan_3:,.0f}", f"{pct_3*100:.1f}% dari Volume Terpakai")
                        
                    st.info(f"💡 Meskipun terdapat sisa kapasitas kosong {sisa_kapasitas:,.0f} cm³, total pendapatan Anda tetap utuh di angka **Rp {tagihan_1 + tagihan_2 + tagihan_3:,.0f}**.")
            else:
                st.warning("Silakan masukkan volume muatan minimal untuk 1 klien.")

except Exception as e:
    st.error(f"Waduh, ada masalah internal: {e}")