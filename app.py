from __future__ import annotations

import streamlit as st

from src.auth.auth_service import ensure_default_admin
from src.auth.session_manager import (
    initialize_session_state,
    is_admin_logged_in,
    logout_admin_session,
)
from src.config.settings import (
    APP_SHORT_NAME,
    LAYOUT,
    PAGE_ICON,
    PAGE_TITLE,
    create_required_directories,
)
from src.database.connection import create_tables
from src.ui.user_dataset import render_user_dataset_page
from src.ui.user_results import render_user_results_page
from src.utils.theme import (
    admin_header,
    detail_panel,
    hero,
    metric_tile,
    nav_active,
    nav_group,
    page_header,
    sidebar_status,
)
from src.utils.ui_components import render_footer, render_step_indicator


st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout=LAYOUT,
)


# ============================================================
# APP INITIALIZATION
# ============================================================

def initialize_app() -> None:
    """
    Inisialisasi aplikasi.
    """

    create_required_directories()
    create_tables()
    ensure_default_admin()
    initialize_session_state()

    from src.utils.theme import apply_theme

    apply_theme()


def go_to(page: str) -> None:
    try:
        st.query_params.clear()
    except Exception:
        pass

    st.query_params["page"] = page
    st.rerun()


def get_current_page() -> str:
    page = st.query_params.get("page", "home")

    if isinstance(page, list):
        page = page[0] if page else "home"

    page = str(page).replace("?", "").strip()

    if not page:
        return "home"

    return page


def get_admin_display_name() -> str:
    """
    Mengambil nama admin tanpa bergantung pada fungsi get_current_admin_name().
    Ini dibuat agar app.py tetap aman meskipun session_manager.py tidak memiliki
    fungsi get_current_admin_name.
    """

    possible_admin_data = [
        st.session_state.get("admin"),
        st.session_state.get("current_admin"),
        st.session_state.get("admin_data"),
        st.session_state.get("logged_in_admin"),
    ]

    for admin_data in possible_admin_data:
        if isinstance(admin_data, dict):
            return (
                admin_data.get("full_name")
                or admin_data.get("name")
                or admin_data.get("username")
                or "Administrator"
            )

    return (
        st.session_state.get("admin_full_name")
        or st.session_state.get("admin_name")
        or st.session_state.get("username")
        or "Administrator"
    )


# ============================================================
# HOME PAGE CONTENT
# ============================================================

HOME_INFO_CONTENT = {
    "bps": {
        "label": "SUMBER DATA",
        "value": "BPS",
        "title": "Sumber Data BPS Sulawesi Utara",
        "body": (
            "Badan Pusat Statistik Provinsi Sulawesi Utara menjadi sumber data "
            "resmi yang digunakan sebagai dasar dalam penyusunan dataset penelitian. "
            "Data statistik yang berasal dari BPS memiliki peran penting karena "
            "menjadi rujukan utama dalam analisis sosial, ekonomi, kependudukan, "
            "dan ketenagakerjaan di wilayah Sulawesi Utara.\n\n"
            "Pada sistem ini, data yang digunakan berfokus pada jumlah pengangguran "
            "serta indikator pendukung lain yang relevan. Data tersebut kemudian "
            "diolah menjadi dataset historis tahunan agar dapat dipelajari oleh "
            "model Long Short-Term Memory. Dengan menggunakan data yang bersumber "
            "dari lembaga resmi, sistem prediksi memiliki dasar yang lebih kuat "
            "dan dapat dipertanggungjawabkan dalam konteks penelitian skripsi.\n\n"
            "Penggunaan data BPS juga membantu menjaga kesesuaian antara sistem "
            "yang dibangun dengan kebutuhan analisis ketenagakerjaan daerah, "
            "khususnya dalam membaca pola perubahan jumlah pengangguran dari tahun "
            "ke tahun di Provinsi Sulawesi Utara."
        ),
    },
    "dataset": {
        "label": "DATASET",
        "value": "Data Historis",
        "title": "Dataset Pengangguran dan Fitur Pendukung",
        "body": (
            "Dataset merupakan komponen utama dalam sistem prediksi karena menjadi "
            "input yang digunakan oleh model LSTM. Dataset minimal harus memiliki "
            "kolom Tahun dan Total_Pengangguran. Kolom Tahun digunakan sebagai "
            "penanda periode, sedangkan Total_Pengangguran digunakan sebagai target "
            "utama yang akan diprediksi.\n\n"
            "Selain kolom utama tersebut, dataset juga dapat memiliki fitur pendukung "
            "seperti Jumlah_Penduduk, TPAK, PDRB, Inflasi, atau indikator numerik "
            "lainnya. Fitur tambahan ini tidak langsung digunakan begitu saja, tetapi "
            "akan melalui proses seleksi berdasarkan nilai korelasi terhadap target. "
            "Dengan cara ini, sistem hanya memilih fitur yang memiliki hubungan cukup "
            "relevan terhadap Total_Pengangguran.\n\n"
            "Sebelum dataset digunakan dalam proses training atau prediksi, sistem "
            "melakukan validasi terlebih dahulu. Validasi dilakukan untuk memastikan "
            "kolom wajib tersedia, tipe data sesuai, tidak terdapat nilai kosong yang "
            "mengganggu proses model, serta jumlah data mencukupi untuk pembentukan "
            "sequence LSTM."
        ),
    },
    "lstm": {
        "label": "MODEL",
        "value": "LSTM",
        "title": "Model Long Short-Term Memory",
        "body": (
            "Long Short-Term Memory atau LSTM merupakan salah satu jenis Recurrent "
            "Neural Network yang dirancang untuk mempelajari data berurutan. Model "
            "ini cocok digunakan pada data deret waktu karena mampu membaca pola "
            "historis dan mempertahankan informasi penting dari periode sebelumnya.\n\n"
            "Dalam sistem ini, LSTM digunakan untuk memprediksi jumlah pengangguran "
            "berdasarkan data historis tahunan. Sebelum masuk ke model, data akan "
            "dinormalisasi menggunakan MinMaxScaler agar setiap variabel berada pada "
            "skala yang sebanding. Setelah itu, data dibentuk menjadi sequence dengan "
            "window size tertentu.\n\n"
            "Dengan window size 5, model menggunakan lima periode sebelumnya sebagai "
            "input untuk memprediksi periode berikutnya. Arsitektur model yang digunakan "
            "terdiri dari layer LSTM, Dropout, dan Dense. Parameter utama yang digunakan "
            "mengikuti rancangan penelitian, yaitu LSTM units 32, dropout rate 0.2, "
            "epochs 300, batch size 4, train ratio 0.8, validation split 0.2, dan "
            "early stopping patience 30."
        ),
    },
    "evaluation": {
        "label": "EVALUASI",
        "value": "MAE RMSE MAPE",
        "title": "Evaluasi Model MAE, RMSE, dan MAPE",
        "body": (
            "Evaluasi model digunakan untuk mengetahui seberapa baik model LSTM dalam "
            "memprediksi data yang diuji. Pada sistem ini, evaluasi dilakukan menggunakan "
            "tiga metrik utama, yaitu MAE, RMSE, dan MAPE. Ketiga metrik tersebut membantu "
            "menilai tingkat kesalahan prediksi dari sudut pandang yang berbeda.\n\n"
            "MAE atau Mean Absolute Error menunjukkan rata-rata selisih absolut antara "
            "nilai aktual dan nilai prediksi. Nilai MAE yang lebih kecil menunjukkan bahwa "
            "rata-rata kesalahan prediksi semakin rendah. RMSE atau Root Mean Squared Error "
            "mengukur akar dari rata-rata kuadrat error, sehingga lebih sensitif terhadap "
            "kesalahan yang besar. MAPE atau Mean Absolute Percentage Error menunjukkan "
            "rata-rata persentase kesalahan prediksi terhadap nilai aktual.\n\n"
            "Dalam halaman hasil prediksi, nilai MAE, RMSE, dan MAPE ditampilkan agar "
            "pengguna dapat memahami performa model secara ringkas. Semakin kecil nilai "
            "ketiga metrik tersebut, maka semakin baik kemampuan model dalam mendekati "
            "data aktual pada periode pengujian."
        ),
    },
    "prediction": {
        "label": "OUTPUT",
        "value": "Prediksi",
        "title": "Output Prediksi Sistem",
        "body": (
            "Output utama dari sistem ini adalah hasil prediksi jumlah pengangguran. "
            "Sistem menampilkan dua jenis hasil, yaitu prediksi pada data test dan prediksi "
            "untuk periode mendatang. Prediksi pada data test digunakan untuk membandingkan "
            "hasil model dengan data aktual, sehingga performa model dapat dievaluasi secara "
            "terukur.\n\n"
            "Hasil prediksi ditampilkan dalam bentuk angka, tabel, dan grafik. Tabel "
            "memudahkan pengguna melihat nilai aktual dan nilai prediksi secara detail, "
            "sedangkan grafik membantu pengguna memahami pola perubahan data dengan lebih "
            "cepat. Selain itu, sistem juga menyediakan tombol download CSV agar hasil "
            "prediksi dapat disimpan dan digunakan kembali untuk kebutuhan analisis atau "
            "pelaporan.\n\n"
            "Pada sisi admin, hasil training dapat dipublish agar tampil sebagai hasil "
            "resmi pada halaman publik. Pada sisi user, pengguna juga dapat mengunggah "
            "dataset sendiri dan menjalankan prediksi secara langsung tanpa mengubah model "
            "resmi yang dipublish oleh admin."
        ),
    },
    "visualization": {
        "label": "VISUALISASI",
        "value": "Grafik & Tabel",
        "title": "Visualisasi Grafik dan Tabel Hasil",
        "body": (
            "Visualisasi digunakan untuk membantu pengguna memahami hasil prediksi secara "
            "lebih mudah. Sistem menampilkan grafik data aktual, grafik prediksi pada data "
            "test, serta grafik prediksi untuk periode mendatang. Dengan visualisasi ini, "
            "pengguna dapat melihat perbandingan antara nilai aktual dan nilai prediksi "
            "secara langsung.\n\n"
            "Grafik gabungan membantu memperlihatkan hubungan antara data aktual, prediksi "
            "test, dan prediksi masa depan dalam satu tampilan. Sementara itu, tab grafik "
            "terpisah memberikan fokus pada bagian tertentu, misalnya hanya prediksi data "
            "test atau hanya prediksi periode mendatang.\n\n"
            "Selain grafik, tabel hasil prediksi tetap disediakan agar pengguna dapat melihat "
            "angka secara lebih detail. Kombinasi grafik dan tabel membuat sistem lebih "
            "informatif, lebih mudah dianalisis, dan lebih siap digunakan sebagai aplikasi "
            "pendukung penelitian maupun demo sistem."
        ),
    },
}


# ============================================================
# HOME PAGE
# ============================================================

def render_home_page() -> None:
    """
    Tampilan beranda final:

    Kotak Biru Utama
    ↓
    6 Kotak Informasi
    ↓
    Kotak Penjelasan sesuai kotak yang diklik
    """

    render_main_home_hero()
    render_home_cards()
    render_selected_home_info()
    render_selected_extra_info()


def render_main_home_hero() -> None:
    """
    Kotak biru utama yang statis.
    Ini tidak berubah saat card diklik.
    """

    hero(
        title="Prediksi Jumlah Pengangguran di Sulawesi Utara",
        subtitle=(
            "Website ini digunakan untuk menampilkan dataset, hasil prediksi, "
            "evaluasi model, dan simulasi prediksi jumlah pengangguran "
            "menggunakan algoritma Long Short-Term Memory."
        ),
        label="User Page",
    )


def get_selected_home_info() -> str:
    """
    Mengambil card informasi yang sedang dipilih.
    Default: bps.
    """

    selected = st.query_params.get("info", "bps")

    if isinstance(selected, list):
        selected = selected[0]

    if selected not in HOME_INFO_CONTENT:
        selected = "bps"

    return selected


def render_home_cards() -> None:
    """
    Menampilkan 6 kotak informasi.
    """

    first_row = st.columns(3)
    second_row = st.columns(3)

    items = [
        ("bps", first_row[0]),
        ("dataset", first_row[1]),
        ("lstm", first_row[2]),
        ("evaluation", second_row[0]),
        ("prediction", second_row[1]),
        ("visualization", second_row[2]),
    ]

    for key, column in items:
        with column:
            render_home_topic_link(key)


def render_home_topic_link(key: str) -> None:
    """
    Membuat 1 card informasi yang bisa diklik.
    Tidak memakai bullet.
    Tidak memakai tombol Detail.
    """

    item = HOME_INFO_CONTENT[key]
    selected_key = get_selected_home_info()
    selected_class = " selected" if selected_key == key else ""

    st.markdown(
        f"""
        <a class="topic-card-link" href="?page=home&info={key}" target="_self">
            <div class="topic-card{selected_class}">
                <div class="topic-card-eyebrow">{item["label"]}</div>
                <div class="topic-card-title">{item["value"]}</div>
                <p class="topic-card-text">{item["title"]}</p>
            </div>
        </a>
        """,
        unsafe_allow_html=True,
    )


def render_selected_home_info() -> None:
    """
    Kotak penjelasan yang muncul di bawah 6 card.
    """

    selected_key = get_selected_home_info()
    selected_item = HOME_INFO_CONTENT[selected_key]

    detail_panel(
        title=selected_item["title"],
        text=selected_item["body"],
    )


def render_selected_extra_info() -> None:
    """
    Informasi tambahan untuk card tertentu.
    """

    selected_key = get_selected_home_info()

    if selected_key == "bps":
        render_bps_links()

    elif selected_key == "dataset":
        render_dataset_structure_detail()

    elif selected_key == "lstm":
        render_lstm_parameter_detail()


def render_bps_links() -> None:
    st.write("")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.link_button(
            "Website BPS Sulut",
            "https://sulut.bps.go.id/",
            use_container_width=True,
        )

    with col2:
        st.link_button(
            "Tabel Tenaga Kerja",
            "https://sulut.bps.go.id/id/statistics-table?subject=520",
            use_container_width=True,
        )

    with col3:
        st.link_button(
            "Publikasi BPS Sulut",
            "https://sulut.bps.go.id/id/publication",
            use_container_width=True,
        )


def render_dataset_structure_detail() -> None:
    with st.expander("Struktur Dataset"):
        st.markdown(
            """
            Dataset minimal harus memiliki kolom:

            ```text
            Tahun
            Total_Pengangguran
            ```

            Fitur pendukung yang dapat digunakan antara lain:

            ```text
            Jumlah_Penduduk
            TPAK
            PDRB
            Inflasi
            ```
            """
        )


def render_lstm_parameter_detail() -> None:
    with st.expander("Parameter Model LSTM"):
        st.markdown(
            """
            ```text
            Window Size              : 5
            Train Ratio              : 0.8
            LSTM Units               : 32
            Dropout Rate             : 0.2
            Epochs                   : 300
            Batch Size               : 4
            Validation Split         : 0.2
            Early Stopping Patience  : 30
            Correlation Threshold    : 0.3
            ```
            """
        )


# ============================================================
# LEGACY INFO PAGES
# ============================================================

def render_info_header(title: str, subtitle: str) -> None:
    page_header(
        title=title,
        subtitle=subtitle,
        label="Informasi",
    )

    if st.button("Kembali ke Beranda", use_container_width=False):
        go_to("home")


def render_info_bps_page() -> None:
    render_info_header(
        title="BPS Sulawesi Utara",
        subtitle="Sumber data statistik resmi untuk analisis pembangunan daerah.",
    )

    detail_panel(
        title=HOME_INFO_CONTENT["bps"]["title"],
        text=HOME_INFO_CONTENT["bps"]["body"],
    )

    render_bps_links()


def render_info_lstm_page() -> None:
    render_info_header(
        title="Model Long Short-Term Memory",
        subtitle="Model deret waktu untuk membaca pola historis data pengangguran.",
    )

    detail_panel(
        title=HOME_INFO_CONTENT["lstm"]["title"],
        text=HOME_INFO_CONTENT["lstm"]["body"],
    )

    render_lstm_parameter_detail()


def render_info_evaluation_page() -> None:
    render_info_header(
        title="Evaluasi Model",
        subtitle="MAE, RMSE, dan MAPE digunakan untuk membaca performa prediksi.",
    )

    detail_panel(
        title=HOME_INFO_CONTENT["evaluation"]["title"],
        text=HOME_INFO_CONTENT["evaluation"]["body"],
    )


def render_info_dataset_page() -> None:
    render_info_header(
        title="Dataset",
        subtitle="Data historis menjadi dasar utama proses training dan prediksi.",
    )

    detail_panel(
        title=HOME_INFO_CONTENT["dataset"]["title"],
        text=HOME_INFO_CONTENT["dataset"]["body"],
    )

    render_dataset_structure_detail()


def render_info_prediction_page() -> None:
    render_info_header(
        title="Prediksi",
        subtitle="Hasil prediksi disajikan untuk melihat estimasi jumlah pengangguran.",
    )

    detail_panel(
        title=HOME_INFO_CONTENT["prediction"]["title"],
        text=HOME_INFO_CONTENT["prediction"]["body"],
    )


def render_info_visualization_page() -> None:
    render_info_header(
        title="Visualisasi",
        subtitle="Grafik membantu membaca pola aktual dan hasil prediksi.",
    )

    detail_panel(
        title=HOME_INFO_CONTENT["visualization"]["title"],
        text=HOME_INFO_CONTENT["visualization"]["body"],
    )


# ============================================================
# ADMIN DASHBOARD
# ============================================================

def render_admin_home_page() -> None:
    hero(
        title="Prediksi Jumlah Pengangguran di Sulawesi Utara",
        subtitle=(
            "Halaman admin digunakan untuk mengelola dataset, melakukan validasi data, "
            "menentukan dataset aktif, menjalankan training model LSTM, melihat hasil evaluasi, "
            "serta mempublish dataset dan hasil prediksi agar dapat ditampilkan pada halaman user."
        ),
        label="Admin Page",
    )

    st.success(f"Login sebagai: {get_admin_display_name()}")

    render_step_indicator(
        [
            ("Kelola Dataset", "Upload dan aktifkan dataset."),
            ("Training Model", "Latih model LSTM."),
            ("Evaluasi", "Lihat MAE, RMSE, dan MAPE."),
            ("Publish", "Tampilkan hasil ke user."),
        ]
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        metric_tile("Dataset", "Kelola")
        if st.button("Buka Kelola Dataset", use_container_width=True, key="admin_open_dataset"):
            go_to("admin-dataset")

    with col2:
        metric_tile("Training", "Model LSTM")
        if st.button("Buka Training Model", use_container_width=True, key="admin_open_training"):
            go_to("admin-training")

    with col3:
        metric_tile("Hasil", "Prediksi")
        if st.button("Buka Hasil Prediksi", use_container_width=True, key="admin_open_results"):
            go_to("results")


# ============================================================
# LAZY PAGES
# ============================================================

def render_admin_login_page_lazy() -> None:
    from src.ui.admin_login import render_admin_login_page

    render_admin_login_page()


def render_admin_dataset_page_lazy() -> None:
    from src.ui.admin_dataset import render_admin_dataset_page

    render_admin_dataset_page()


def render_user_prediction_page_lazy() -> None:
    from src.ui.user_prediction import render_user_prediction_page

    render_user_prediction_page()


def render_admin_training_page_lazy() -> None:
    from src.ui.admin_training import render_admin_training_page

    render_admin_training_page()


# ============================================================
# SIDEBAR
# ============================================================

def sidebar_button(label: str, page: str, current_page: str, key: str) -> None:
    if current_page == page:
        nav_active(label)
        return

    if st.sidebar.button(label, use_container_width=True, key=key):
        go_to(page)


def render_sidebar() -> None:
    current_page = get_current_page()

    st.sidebar.markdown(
        f"""
        <div class="sidebar-title">{APP_SHORT_NAME}</div>
        <div class="sidebar-subtitle">
            BPS Sulawesi Utara • LSTM Forecasting
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.sidebar.divider()

    if is_admin_logged_in():
        sidebar_status(f"Login sebagai: {get_admin_display_name()}")

        nav_group("Admin")
        sidebar_button("Dashboard Admin", "admin-dashboard", current_page, "nav_admin_dashboard")
        sidebar_button("Kelola Dataset", "admin-dataset", current_page, "nav_admin_dataset")
        sidebar_button("Training Model", "admin-training", current_page, "nav_admin_training")

        nav_group("Publik")
        sidebar_button("Beranda", "home", current_page, "nav_home_admin")
        sidebar_button("Dataset", "dataset", current_page, "nav_dataset_admin")
        sidebar_button("Hasil Prediksi", "results", current_page, "nav_results_admin")
        sidebar_button("Prediksi User", "user-prediction", current_page, "nav_user_prediction_admin")

        st.sidebar.divider()

        if st.sidebar.button("Logout", use_container_width=True, key="nav_logout"):
            logout_admin_session()

            try:
                st.query_params.clear()
            except Exception:
                pass

            st.query_params["page"] = "home"
            st.rerun()

        return

    nav_group("Menu")
    sidebar_button("Beranda", "home", current_page, "nav_home")
    sidebar_button("Dataset", "dataset", current_page, "nav_dataset")
    sidebar_button("Hasil Prediksi", "results", current_page, "nav_results")
    sidebar_button("Prediksi User", "user-prediction", current_page, "nav_user_prediction")

    st.sidebar.divider()

    sidebar_button("Login Admin", "login", current_page, "nav_login")


# ============================================================
# ROUTING
# ============================================================

def require_login_or_redirect() -> bool:
    if is_admin_logged_in():
        return True

    go_to("login")
    return False


def render_selected_page() -> None:
    page = get_current_page()

    if page == "home":
        render_home_page()

    elif page == "dataset":
        render_user_dataset_page()

    elif page == "results":
        render_user_results_page()

    elif page == "user-prediction":
        render_user_prediction_page_lazy()

    elif page == "info-bps":
        render_info_bps_page()

    elif page == "info-lstm":
        render_info_lstm_page()

    elif page == "info-evaluation":
        render_info_evaluation_page()

    elif page == "info-dataset":
        render_info_dataset_page()

    elif page == "info-prediction":
        render_info_prediction_page()

    elif page == "info-visualization":
        render_info_visualization_page()

    elif page == "login":
        if is_admin_logged_in():
            go_to("admin-dashboard")
            return

        render_admin_login_page_lazy()

    elif page == "admin-dashboard":
        if not require_login_or_redirect():
            return

        render_admin_home_page()

    elif page == "admin-dataset":
        if not require_login_or_redirect():
            return

        render_admin_dataset_page_lazy()

    elif page == "admin-training":
        if not require_login_or_redirect():
            return

        render_admin_training_page_lazy()

    else:
        go_to("home")


def main() -> None:
    initialize_app()

    force_page = st.session_state.pop("force_page", None)

    if force_page:
        try:
            st.query_params.clear()
        except Exception:
            pass

        st.query_params["page"] = force_page
        st.rerun()

    render_sidebar()
    render_selected_page()
    render_footer()


if __name__ == "__main__":
    main()