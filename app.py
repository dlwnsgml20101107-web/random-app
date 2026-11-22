mport streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, NullFormatter

# ------------------------------------------------------------
# 1. 화면 설정 및 디자인
# ------------------------------------------------------------

st.set_page_config(
    page_title="RC Filter Analyzer",
    page_icon="🔌",
    layout="wide"
)

st.markdown("""
<style>
.block-container {
    max-width: 1200px;
    padding-top: 1.5rem;
    padding-bottom: 2rem;
    padding-left: 3rem;
    padding-right: 3rem;
}
h1 {
    font-size: 1.65rem !important;
    font-weight: 700 !important;
    margin-bottom: 0.3rem !important;
}
h2 { font-size: 1.25rem !important; font-weight: 650 !important; }
h3 { font-size: 1.05rem !important; }
p, label, .stMarkdown { font-size: 0.88rem; }
.stCaption { font-size: 0.75rem; }
[data-testid="stMetric"] {
    background-color: rgba(128, 128, 128, 0.07);
    padding: 12px 15px;
    border-radius: 10px;
    border: 1px solid rgba(128, 128, 128, 0.15);
}
[data-testid="stMetricLabel"] { font-size: 0.78rem !important; }
[data-testid="stMetricValue"] {
    font-size: 1.35rem !important;
    font-weight: 650;
}
.stNumberInput, .stSelectbox { margin-bottom: 0.35rem; }
.stButton button, .stDownloadButton button {
    border-radius: 8px;
    font-size: 0.85rem;
}
hr { margin-top: 1rem; margin-bottom: 1rem; }
[data-testid="stSidebar"] { min-width: 270px; }
</style>
""", unsafe_allow_html=True)


# ------------------------------------------------------------
# 2. 회로 계산 함수
# ------------------------------------------------------------

def cutoff_frequency(resistance_ohm, capacitance_f):
    """1차 RC 회로의 차단 주파수를 계산한다."""
    if resistance_ohm <= 0 or capacitance_f <= 0:
        raise ValueError("저항과 커패시터 값은 0보다 커야 합니다.")
    return 1.0 / (2.0 * np.pi * resistance_ohm * capacitance_f)


def calculate_response(
    filter_type,
    frequencies_hz,
    resistance_ohm=None,
    capacitance_f=None,
    bandpass_components=None
):
    """
    전압 이득(선형), 이득(dB), 위상차(도)를 계산한다.

    대역통과 모델:
    1차 고역통과 RC -> 이상적인 버퍼 -> 1차 저역통과 RC
    두 단계 사이의 부하 효과는 버퍼가 차단한다고 가정한다.
    """
    frequencies = np.asarray(frequencies_hz, dtype=float)

    if np.any(frequencies <= 0):
        raise ValueError("주파수는 0보다 커야 합니다.")

    if filter_type in ("저역통과", "고역통과"):
        if resistance_ohm is None or capacitance_f is None:
            raise ValueError("저항과 커패시터 값이 필요합니다.")
        if resistance_ohm <= 0 or capacitance_f <= 0:
            raise ValueError("저항과 커패시터 값은 0보다 커야 합니다.")

        x = 2.0 * np.pi * frequencies * resistance_ohm * capacitance_f

        if filter_type == "저역통과":
            gain = 1.0 / np.sqrt(1.0 + x**2)
            phase_deg = -np.degrees(np.arctan(x))
        else:
            gain = x / np.sqrt(1.0 + x**2)
            phase_deg = np.degrees(np.arctan2(1.0, x))

    elif filter_type == "대역통과":
        if bandpass_components is None:
            raise ValueError("대역통과 필터의 두 단계 부품값이 필요합니다.")

        r_hp, c_hp, r_lp, c_lp = bandpass_components
        if min(r_hp, c_hp, r_lp, c_lp) <= 0:
            raise ValueError("모든 저항과 커패시터 값은 0보다 커야 합니다.")

        x_hp = 2.0 * np.pi * frequencies * r_hp * c_hp
        x_lp = 2.0 * np.pi * frequencies * r_lp * c_lp

        hp_gain = x_hp / np.sqrt(1.0 + x_hp**2)
        lp_gain = 1.0 / np.sqrt(1.0 + x_lp**2)

        # 버퍼로 분리된 두 단계 전달함수의 곱
        gain = hp_gain * lp_gain
        phase_deg = np.degrees(
            np.arctan2(1.0, x_hp) - np.arctan(x_lp)
        )
    else:
        raise ValueError("지원하지 않는 필터입니다.")

    gain_db = 20.0 * np.log10(np.maximum(gain, 1e-15))
    return gain, gain_db, phase_deg


# ------------------------------------------------------------
# 3. 리스트와 반복문을 이용한 출력 전압 계산
# ------------------------------------------------------------

def calculate_output_voltages(input_voltage, gains):
    output_voltage_list = []

    for i in range(len(gains)):
        output_voltage = input_voltage * float(gains[i])
        output_voltage_list.append(output_voltage)

    return output_voltage_list


# ------------------------------------------------------------
# 4. 자동 검증 함수
# ------------------------------------------------------------

def run_self_tests():
    r = 1000.0
    c = 1e-6
    fc = cutoff_frequency(r, c)

    lp_gain, _, lp_phase = calculate_response(
        "저역통과", [fc], r, c
    )
    hp_gain, _, hp_phase = calculate_response(
        "고역통과", [fc], r, c
    )

    expected_gain = 1.0 / np.sqrt(2.0)
    assert abs(float(lp_gain[0]) - expected_gain) < 1e-10
    assert abs(float(hp_gain[0]) - expected_gain) < 1e-10
    assert abs(float(lp_phase[0]) + 45.0) < 1e-8
    assert abs(float(hp_phase[0]) - 45.0) < 1e-8

    # 대역통과 전달함수의 독립적인 기준값 검증
    # fL=1/(2πR_hpC_hp), fH=1/(2πR_lpC_lp)
    # 두 차단 주파수의 기하평균에서 계산값을 직접 확인한다.
    r_hp, c_hp = 1000.0, 1e-6
    r_lp, c_lp = 1000.0, 10e-9
    f_low = cutoff_frequency(r_hp, c_hp)
    f_high = cutoff_frequency(r_lp, c_lp)
    f_test = np.sqrt(f_low * f_high)

    bp_gain, bp_db, bp_phase = calculate_response(
        "대역통과",
        [f_test],
        bandpass_components=(r_hp, c_hp, r_lp, c_lp)
    )

    x_hp = 2.0 * np.pi * f_test * r_hp * c_hp
    x_lp = 2.0 * np.pi * f_test * r_lp * c_lp
    expected_bp_gain = (
        x_hp / np.sqrt(1.0 + x_hp**2)
    ) * (
        1.0 / np.sqrt(1.0 + x_lp**2)
    )
    expected_bp_phase = np.degrees(
        np.arctan2(1.0, x_hp) - np.arctan(x_lp)
    )

    assert abs(float(bp_gain[0]) - expected_bp_gain) < 1e-10
    assert abs(float(bp_db[0]) - 20.0 * np.log10(expected_bp_gain)) < 1e-9
    assert abs(float(bp_phase[0]) - expected_bp_phase) < 1e-8

    # 출력 전압 리스트 계산 검증
    outputs = calculate_output_voltages(5.0, [1.0, 0.5, 0.25])
    assert np.allclose(outputs, [5.0, 2.5, 1.25])

    # 대역통과 주파수 순서 검증
    assert f_low < f_high

    return True


# ------------------------------------------------------------
# 5. 메인 화면
# ------------------------------------------------------------

st.title("🔌 전자 필터 설계 및 주파수 응답 분석기")
st.caption("RC Filter Design & Frequency Response Analyzer")
st.write(
    "저항과 커패시터 값을 입력하면 RC 필터의 차단 주파수, "
    "출력 전압, 전압 이득 및 위상 변화를 분석합니다."
)
st.divider()


# ------------------------------------------------------------
# 6. 프로그램 목적 및 작동 원리 설명
# ------------------------------------------------------------

with st.expander("📖 프로그램의 목적과 작동 원리 알아보기", expanded=False):
    st.markdown("""
### ① 프로그램의 목적

이 프로그램은 저항(R)과 커패시터(C)로 구성된 RC 필터의
전기적 특성을 분석하고 설계하는 것을 목적으로 합니다.

사용자가 부품값을 입력하면 차단 주파수를 계산하고,
주파수 변화에 따라 출력 전압과 전압 이득, 위상차가
어떻게 달라지는지 그래프와 표로 확인할 수 있습니다.

### ② RC 필터의 작동 원리

RC 필터는 저항과 커패시터를 이용하여 입력 신호의 주파수에 따라
출력 신호의 크기를 조절하는 회로입니다.

- **저역통과 필터:** 낮은 주파수는 잘 통과시키고 높은 주파수는 약하게 만듭니다.
- **고역통과 필터:** 높은 주파수는 잘 통과시키고 낮은 주파수는 약하게 만듭니다.
- **대역통과 필터:** 특정 주파수 범위의 신호를 상대적으로 잘 통과시키고,
  그보다 낮거나 높은 주파수의 신호는 약하게 만듭니다.

### ③ 차단 주파수의 계산 원리

\\[
f_c = \\frac{1}{2\\pi RC}
\\]

차단 주파수에서 1차 RC 필터의 전압 이득은 약 0.707이며,
이는 입력 전압의 약 70.7%에 해당합니다.

### ④ 대역통과 필터의 회로 구조

이 프로그램의 대역통과 필터는 다음 구조를 가정합니다.

**입력 → 1차 고역통과 RC → 이상적인 버퍼 → 1차 저역통과 RC → 출력**

두 단계 사이에 버퍼가 있어 서로 부하를 주지 않는다고 가정합니다.
따라서 전체 전달함수는 두 단계 전달함수의 곱으로 계산합니다.

여기서 하한·상한 주파수는 각각 고역통과 단계와 저역통과 단계의
개별 RC 차단 주파수입니다. 전체 대역통과 응답의 최대 이득을 기준으로
한 -3 dB 경계와는 일반적으로 정확히 같지 않습니다.

### ⑤ 프로그램의 분석 과정

1. 필터 종류와 회로 부품값 또는 차단 주파수를 설정합니다.
2. 각 단계의 차단 주파수를 계산합니다.
3. 주파수별 전압 이득과 위상차를 계산합니다.
4. 전압 이득에 입력 전압을 곱해 출력 전압을 구합니다.
5. 결과를 그래프와 표로 표시하고 CSV로 저장합니다.
""")


# ------------------------------------------------------------
# 7. 용어 설명
# ------------------------------------------------------------

if "show_explanation" not in st.session_state:
    st.session_state.show_explanation = False

if st.button("📘 전자 필터 용어 설명 보기 / 닫기"):
    st.session_state.show_explanation = not st.session_state.show_explanation

if st.session_state.show_explanation:
    with st.container(border=True):
        st.subheader("프로그램에 사용되는 기본 용어")
        st.markdown("""
**저항(R)**  
전류의 흐름을 제한하는 전자 부품입니다. 단위는 옴(Ω)입니다.

**커패시터(C)**  
전기 에너지를 전기장 형태로 저장하고 방출하는 부품입니다. 단위는 패럿(F)입니다.

**주파수(Hz)**  
전기 신호가 1초 동안 반복되는 횟수입니다.

**전자 필터**  
특정 주파수의 신호는 통과시키고 다른 주파수의 신호는 약하게 만드는 회로입니다.

**저역통과 필터**  
낮은 주파수는 잘 통과시키고 높은 주파수는 약하게 만듭니다.

**고역통과 필터**  
높은 주파수는 잘 통과시키고 낮은 주파수는 약하게 만듭니다.

**대역통과 필터**  
특정 범위의 주파수는 통과시키고 그 범위보다 낮거나 높은 주파수는 약하게 만듭니다.

**차단 주파수**  
1차 RC 단계에서 출력 전압이 해당 단계의 통과 대역 기준 약 70.7%가 되는 주파수입니다.

**전압 이득**  
출력 전압을 입력 전압으로 나눈 값입니다.

**위상차**  
입력 신호와 출력 신호의 위상 차이를 각도로 나타낸 값입니다.

**차단 주파수 공식**  
\\[
f_c = \\frac{1}{2\\pi RC}
\\]
""")


# ------------------------------------------------------------
# 8. 사용자 입력
# ------------------------------------------------------------

st.sidebar.header("⚙️ 회로 및 분석 조건")

filter_type = st.sidebar.selectbox(
    "필터 종류",
    ["저역통과", "고역통과", "대역통과"]
)

input_voltage = st.sidebar.number_input(
    "입력 전압 크기 (V)",
    min_value=0.001,
    max_value=100000.0,
    value=5.0,
    step=1.0
)

bandpass_components = None
f_low = None
f_high = None

if filter_type in ("저역통과", "고역통과"):
    resistance_kohm = st.sidebar.number_input(
        "저항값 R (kΩ)",
        min_value=0.001,
        max_value=10000.0,
        value=1.0,
        step=1.0
    )
    capacitance_uf = st.sidebar.number_input(
        "커패시터값 C (μF)",
        min_value=0.001,
        max_value=100000.0,
        value=1.0,
        step=1.0
    )
    r_ohm = resistance_kohm * 1000.0
    c_f = capacitance_uf * 1e-6
    fc = cutoff_frequency(r_ohm, c_f)

else:
    st.sidebar.markdown("**대역통과 필터 설정**")
    design_mode = st.sidebar.radio(
        "설정 방법",
        ["저항·커패시터 값 입력", "하한·상한 차단 주파수 입력"]
    )

    if design_mode == "저항·커패시터 값 입력":
        st.sidebar.caption("고역통과 단계")
        r_hp_kohm = st.sidebar.number_input(
            "고역통과 저항 R₁ (kΩ)",
            min_value=0.001, max_value=10000.0,
            value=1.0, step=1.0
        )
        c_hp_uf = st.sidebar.number_input(
            "고역통과 커패시터 C₁ (μF)",
            min_value=0.000001, max_value=100000.0,
            value=1.0, format="%.6f"
        )

        st.sidebar.caption("저역통과 단계")
        r_lp_kohm = st.sidebar.number_input(
            "저역통과 저항 R₂ (kΩ)",
            min_value=0.001, max_value=10000.0,
            value=1.0, step=1.0
        )
        c_lp_uf = st.sidebar.number_input(
            "저역통과 커패시터 C₂ (μF)",
            min_value=0.000001, max_value=100000.0,
            value=0.01, format="%.6f"
        )

        r_hp, c_hp = r_hp_kohm * 1000.0, c_hp_uf * 1e-6
        r_lp, c_lp = r_lp_kohm * 1000.0, c_lp_uf * 1e-6
        f_low = cutoff_frequency(r_hp, c_hp)
        f_high = cutoff_frequency(r_lp, c_lp)

    else:
        st.sidebar.caption("원하는 통과 대역 경계 설정")
        f_low = st.sidebar.number_input(
            "하한 차단 주파수 (Hz)",
            min_value=0.001, max_value=1e12,
            value=100.0, step=10.0
        )
        f_high = st.sidebar.number_input(
            "상한 차단 주파수 (Hz)",
            min_value=0.002, max_value=1e12,
            value=10000.0, step=100.0
        )
        common_r_kohm = st.sidebar.number_input(
            "두 단계에 사용할 저항값 (kΩ)",
            min_value=0.001, max_value=10000.0,
            value=1.0, step=1.0
        )
        common_r = common_r_kohm * 1000.0

        if f_high > f_low:
            c_hp = 1.0 / (2.0 * np.pi * common_r * f_low)
            c_lp = 1.0 / (2.0 * np.pi * common_r * f_high)
            r_hp = r_lp = common_r
            st.sidebar.caption(
                f"계산된 C₁ = {c_hp * 1e6:.6g} μF / "
                f"C₂ = {c_lp * 1e6:.6g} μF"
            )
        else:
            c_hp = c_lp = 1e-6
            r_hp = r_lp = common_r

    bandpass_components = (r_hp, c_hp, r_lp, c_lp)
    fc = None

st.sidebar.divider()
st.sidebar.subheader("주파수 분석")

start_frequency = st.sidebar.number_input(
    "분석 시작 주파수 (Hz)",
    min_value=0.001, max_value=1e9,
    value=10.0, step=1.0
)
end_frequency = st.sidebar.number_input(
    "분석 종료 주파수 (Hz)",
    min_value=0.002, max_value=1e12,
    value=100000.0, step=1.0
)
number_of_points = st.sidebar.slider(
    "그래프 계산 지점 수",
    min_value=50, max_value=1000,
    value=300, step=50
)
test_frequency = st.sidebar.number_input(
    "별도로 확인할 주파수 (Hz)",
    min_value=0.001, max_value=1e12,
    value=1000.0, step=1.0
)


# ------------------------------------------------------------
# 9. 계산 및 입력값 검증
# ------------------------------------------------------------

if end_frequency <= start_frequency:
    st.error("종료 주파수는 시작 주파수보다 커야 합니다.")
    st.stop()

if filter_type == "대역통과" and f_high <= f_low:
    st.error("상한 차단 주파수는 하한 차단 주파수보다 커야 합니다.")
    st.stop()

if filter_type == "대역통과":
    if f_high <= f_low:
        st.stop()
    frequencies = np.logspace(
        np.log10(start_frequency),
        np.log10(end_frequency),
        number_of_points
    )
    gain, gain_db, phase_deg = calculate_response(
        "대역통과",
        frequencies,
        bandpass_components=bandpass_components
    )
    point_gain, point_gain_db, point_phase = calculate_response(
        "대역통과",
        [test_frequency],
        bandpass_components=bandpass_components
    )
else:
    frequencies = np.logspace(
        np.log10(start_frequency),
        np.log10(end_frequency),
        number_of_points
    )
    gain, gain_db, phase_deg = calculate_response(
        filter_type, frequencies, r_ohm, c_f
    )
    point_gain, point_gain_db, point_phase = calculate_response(
        filter_type, [test_frequency], r_ohm, c_f
    )


# ------------------------------------------------------------
# 10. 리스트와 반복문을 이용한 데이터 처리
# ------------------------------------------------------------

frequency_list = frequencies.tolist()
gain_list = gain.tolist()
gain_db_list = gain_db.tolist()
phase_list = phase_deg.tolist()

output_voltage_list = calculate_output_voltages(
    input_voltage, gain_list
)


# ------------------------------------------------------------
# 11. 계산 결과
# ------------------------------------------------------------

st.subheader("📊 분석 결과")

if filter_type == "대역통과":
    col1, col2, col3 = st.columns(3)
    col1.metric("하한 차단 주파수", f"{f_low:,.2f} Hz")
    col2.metric("상한 차단 주파수", f"{f_high:,.2f} Hz")
    col3.metric("통과 대역 폭", f"{f_high - f_low:,.2f} Hz")
    st.caption(
        "위 두 경계는 각각 고역통과 단계와 저역통과 단계의 개별 차단 주파수입니다."
    )
    st.caption(
        f"고역통과 단계: R₁ = {r_hp:,.2f} Ω, C₁ = {c_hp:.8g} F  |  "
        f"저역통과 단계: R₂ = {r_lp:,.2f} Ω, C₂ = {c_lp:.8g} F"
    )
else:
    col1, col2, col3 = st.columns(3)
    col1.metric("차단 주파수", f"{fc:,.2f} Hz")
    col2.metric("전압 이득", f"{float(point_gain[0]):.4f} 배")
    col3.metric("위상차", f"{float(point_phase[0]):.2f}°")
    st.caption(
        f"저항 = {r_ohm:,.2f} Ω  |  "
        f"커패시터 = {c_f:.8g} F"
    )

output_voltage = input_voltage * float(point_gain[0])
st.metric(
    f"{test_frequency:,.2f} Hz에서의 출력 전압",
    f"{output_voltage:.4f} V"
)
st.caption(f"입력 전압 = {input_voltage:g} V")
st.divider()


# ------------------------------------------------------------
# 12. 주파수 응답 그래프
# ------------------------------------------------------------

st.subheader("📈 주파수 응답 분석")
graph_col1, graph_col2 = st.columns(2)

with graph_col1:
    st.markdown("**① 주파수에 따른 전압 이득**")
    fig1, ax1 = plt.subplots(figsize=(5.2, 2.7), dpi=100)
    ax1.semilogx(
        frequency_list, gain_db_list,
        linewidth=1.8, label="Gain"
    )
    ax1.xaxis.set_major_formatter(
        FuncFormatter(lambda value, position: f"{value:,.0f}")
    )
    ax1.xaxis.set_minor_formatter(NullFormatter())

    if filter_type == "대역통과":
        ax1.axvline(
            f_low, linestyle="--", linewidth=1,
            label="Lower stage cutoff"
        )
        ax1.axvline(
            f_high, linestyle="--", linewidth=1,
            label="Upper stage cutoff"
        )
        left = max(start_frequency, f_low)
        right = min(end_frequency, f_high)
        if right > left:
            ax1.axvspan(left, right, alpha=0.12, label="Nominal passband")
    else:
        ax1.axvline(fc, linestyle="--", linewidth=1, label="Cutoff")
        ax1.axhline(-3.0103, linestyle=":", linewidth=1, label="-3.01 dB")

    ax1.set_xlabel("Frequency (Hz)", fontsize=8)
    ax1.set_ylabel("Gain (dB)", fontsize=8)
    ax1.set_title(f"{filter_type} filter", fontsize=10)
    ax1.tick_params(labelsize=7)
    ax1.grid(True, which="both", alpha=0.25)
    ax1.legend(fontsize=7, loc="best")
    fig1.tight_layout()
    st.pyplot(fig1, use_container_width=True)
    plt.close(fig1)

with graph_col2:
    st.markdown("**② 주파수에 따른 위상 변화**")
    fig2, ax2 = plt.subplots(figsize=(5.2, 2.7), dpi=100)
    ax2.semilogx(
        frequency_list, phase_list,
        linewidth=1.8, label="Phase"
    )
    ax2.xaxis.set_major_formatter(
        FuncFormatter(lambda value, position: f"{value:,.0f}")
    )
    ax2.xaxis.set_minor_formatter(NullFormatter())

    if filter_type == "대역통과":
        ax2.axvline(f_low, linestyle="--", linewidth=1, label="Lower cutoff")
        ax2.axvline(f_high, linestyle="--", linewidth=1, label="Upper cutoff")
        left = max(start_frequency, f_low)
        right = min(end_frequency, f_high)
        if right > left:
            ax2.axvspan(left, right, alpha=0.12, label="Nominal passband")
    else:
        ax2.axvline(fc, linestyle="--", linewidth=1, label="Cutoff")

    ax2.set_xlabel("Frequency (Hz)", fontsize=8)
    ax2.set_ylabel("Phase (degrees)", fontsize=8)
    ax2.set_title(f"{filter_type} filter", fontsize=10)
    ax2.tick_params(labelsize=7)
    ax2.grid(True, which="both", alpha=0.25)
    ax2.legend(fontsize=7, loc="best")
    fig2.tight_layout()
    st.pyplot(fig2, use_container_width=True)
    plt.close(fig2)

st.divider()


# ------------------------------------------------------------
# 13. 계산 데이터 및 CSV 다운로드
# ------------------------------------------------------------

st.subheader("📋 계산 데이터")
result_df = pd.DataFrame({
    "주파수(Hz)": frequency_list,
    "전압 이득(배)": gain_list,
    "전압 이득(dB)": gain_db_list,
    "위상차(도)": phase_list,
    "출력 전압(V)": output_voltage_list
})
st.dataframe(
    result_df,
    use_container_width=True,
    hide_index=True,
    height=250
)

csv_data = result_df.to_csv(index=False).encode("utf-8-sig")
st.download_button(
    "📥 분석 결과 CSV 다운로드",
    data=csv_data,
    file_name="rc_filter_analysis.csv",
    mime="text/csv"
)


# ------------------------------------------------------------
# 14. 설계 역산 기능
# ------------------------------------------------------------

st.divider()
st.subheader("④ 설계 역산 기능")

if filter_type == "대역통과":
    st.write("원하는 하한·상한 차단 주파수에 맞는 커패시터 값을 계산합니다.")
    target_low = st.number_input(
        "목표 하한 차단 주파수 (Hz)",
        min_value=0.001, max_value=1e12,
        value=float(f_low), step=10.0
    )
    target_high = st.number_input(
        "목표 상한 차단 주파수 (Hz)",
        min_value=0.002, max_value=1e12,
        value=float(f_high), step=100.0
    )
    if target_high <= target_low:
        st.error("상한 차단 주파수는 하한 차단 주파수보다 커야 합니다.")
    else:
        required_c_hp = 1.0 / (2.0 * np.pi * r_hp * target_low)
        required_c_lp = 1.0 / (2.0 * np.pi * r_lp * target_high)
        st.success(
            f"고역통과 단계 C₁ = {required_c_hp * 1e6:.6g} μF\n\n"
            f"저역통과 단계 C₂ = {required_c_lp * 1e6:.6g} μF"
        )
else:
    st.write("원하는 차단 주파수에 맞는 저항값을 계산합니다.")
    target_fc = st.number_input(
        "목표 차단 주파수 (Hz)",
        min_value=0.001, max_value=1e9,
        value=1000.0, step=1.0
    )
    required_r = 1.0 / (2.0 * np.pi * target_fc * c_f)
    st.success(
        f"현재 커패시터값 {capacitance_uf:g} μF를 유지한다면 "
        f"필요한 저항은 {required_r:,.2f} Ω "
        f"({required_r / 1000:.4f} kΩ) 입니다."
    )


# ------------------------------------------------------------
# 15. 자동 검증
# ------------------------------------------------------------

st.divider()
with st.expander("🔍 계산 공식 자동 검증 결과 보기"):
    try:
        run_self_tests()
        st.success(
            "검증 통과! 저역통과·고역통과·대역통과 필터의 "
            "전압 이득, 위상차 및 출력 전압 계산이 기준값과 일치합니다."
        )
    except (AssertionError, ValueError) as error:
        st.error(f"검증 실패: {error}")


# ------------------------------------------------------------
# 16. 하단 안내
# ------------------------------------------------------------

st.divider()
st.caption(
    "교육용 시뮬레이터입니다. 실제 회로 제작 전에는 "
    "부품의 허용오차와 정격을 확인해야 합니다."
)
