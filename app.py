mport streamlit as st

# ==========================================
# 1. 기본 설정
# ==========================================

st.set_page_config(
    page_title="저항 색상 띠 계산기",
    page_icon="🔌",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 화면 디자인
st.markdown("""
<style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0.5rem;
        padding-left: 2rem;
        padding-right: 2rem;
        max-width: 100%;
    }

    h1 {
        padding-bottom: 0.2rem;
    }

    [data-testid="stMetricValue"] {
        font-size: 1.8rem;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)


# ==========================================
# 2. 색상 데이터
# ==========================================

color_data = {
    "검정색": {
        "digit": 0,
        "multiplier": 1,
        "hex": "#202020"
    },
    "갈색": {
        "digit": 1,
        "multiplier": 10,
        "hex": "#8B4513"
    },
    "빨간색": {
        "digit": 2,
        "multiplier": 100,
        "hex": "#E53935"
    },
    "주황색": {
        "digit": 3,
        "multiplier": 1000,
        "hex": "#EF6C00"
    },
    "노란색": {
        "digit": 4,
        "multiplier": 10000,
        "hex": "#FDD835"
    },
    "초록색": {
        "digit": 5,
        "multiplier": 100000,
        "hex": "#388E3C"
    },
    "파란색": {
        "digit": 6,
        "multiplier": 1000000,
        "hex": "#1976D2"
    },
    "보라색": {
        "digit": 7,
        "multiplier": 10000000,
        "hex": "#7B1FA2"
    },
    "회색": {
        "digit": 8,
        "multiplier": 100000000,
        "hex": "#9E9E9E"
    },
    "흰색": {
        "digit": 9,
        "multiplier": 1000000000,
        "hex": "#FFFFFF"
    },
    "금색": {
        "multiplier": 0.1,
        "hex": "#D4AF37"
    },
    "은색": {
        "multiplier": 0.01,
        "hex": "#C0C0C0"
    }
}


# 허용 오차 (%)
tolerance_data = {
    "갈색": 1,
    "빨간색": 2,
    "초록색": 0.5,
    "파란색": 0.25,
    "보라색": 0.1,
    "회색": 0.05,
    "금색": 5,
    "은색": 10,
    "없음": 20
}


# 온도 계수 (ppm/℃)
temperature_data = {
    "검정색": 250,
    "갈색": 100,
    "빨간색": 50,
    "주황색": 15,
    "노란색": 25,
    "초록색": 20,
    "파란색": 10,
    "보라색": 5,
    "회색": 1
}


# ==========================================
# 3. 저항값 표시 함수
# ==========================================

def format_resistance(value):

    if value >= 1_000_000:
        return f"{value / 1_000_000:g} MΩ"

    elif value >= 1_000:
        return f"{value / 1_000:g} kΩ"

    else:
        return f"{value:g} Ω"


# ==========================================
# 4. 제목
# ==========================================

st.title("🔌 저항 색상 띠 계산기")

st.caption(
    "Resistor Color Code Calculator | "
    "색상 띠를 선택하여 저항값과 허용 오차를 계산합니다."
)

st.divider()


# ==========================================
# 5. 화면 분할
# ==========================================

input_col, result_col, guide_col = st.columns(
    [1.15, 1.05, 1.2],
    gap="large"
)


# ==========================================
# 6. 왼쪽 : 색상 띠 입력
# ==========================================

with input_col:

    st.subheader("① 색상 띠 입력")

    band_count = st.radio(
        "저항 종류",
        [4, 5, 6],
        horizontal=True,
        format_func=lambda x: f"{x}색 띠"
    )

    # 숫자 띠 개수
    digit_count = 2 if band_count == 4 else 3

    # 각 띠의 역할
    if band_count == 4:

        band_names = [
            "첫 번째 숫자",
            "두 번째 숫자",
            "배율",
            "허용 오차"
        ]

    elif band_count == 5:

        band_names = [
            "첫 번째 숫자",
            "두 번째 숫자",
            "세 번째 숫자",
            "배율",
            "허용 오차"
        ]

    else:

        band_names = [
            "첫 번째 숫자",
            "두 번째 숫자",
            "세 번째 숫자",
            "배율",
            "허용 오차",
            "온도 계수"
        ]

    # 기본 선택 색상
    default_colors = {
        4: [
            "갈색",
            "검정색",
            "빨간색",
            "금색"
        ],
        5: [
            "갈색",
            "검정색",
            "검정색",
            "빨간색",
            "갈색"
        ],
        6: [
            "갈색",
            "검정색",
            "검정색",
            "빨간색",
            "갈색",
            "갈색"
        ]
    }

    selected_colors = []

    # 색상 선택
    for i in range(band_count):

        if i < digit_count:

            options = [
                color for color, info in color_data.items()
                if "digit" in info
            ]

        elif i == digit_count:

            options = list(color_data.keys())

        elif i == digit_count + 1:

            options = list(tolerance_data.keys())

        else:

            options = list(temperature_data.keys())

        selected = st.selectbox(
            f"{i + 1}번째 띠 · {band_names[i]}",
            options,
            index=options.index(default_colors[band_count][i]),
            key=f"band_{band_count}_{i}"
        )

        selected_colors.append(selected)

    # 선택된 색상 시각화
    st.markdown("**선택한 저항 색상**")

    color_columns = st.columns(band_count)

    for i, col in enumerate(color_columns):

        with col:

            color = selected_colors[i]

            if color == "없음":
                hex_color = "#FFFFFF"
            else:
                hex_color = color_data[color]["hex"]

            st.markdown(
                f"""
                <div style="
                    height:55px;
                    background-color:{hex_color};
                    border:1px solid #888;
                    border-radius:7px;
                    margin-bottom:5px;
                "></div>

                <p style="
                    text-align:center;
                    font-size:12px;
                    margin-top:0px;
                ">
                    {i + 1}번째
                </p>
                """,
                unsafe_allow_html=True
            )


# ==========================================
# 7. 저항값 계산
# ==========================================

# 숫자 띠 결합
digits = ""

for i in range(digit_count):

    digits += str(
        color_data[selected_colors[i]]["digit"]
    )

significant_value = int(digits)


# 배율 계산
multiplier_color = selected_colors[digit_count]

multiplier = color_data[
    multiplier_color
]["multiplier"]


# 최종 저항값
resistance = significant_value * multiplier


# 허용 오차 계산
tolerance_color = selected_colors[digit_count + 1]

tolerance = tolerance_data[tolerance_color]


# 최소 및 최대 저항값
minimum = resistance * (1 - tolerance / 100)

maximum = resistance * (1 + tolerance / 100)


# ==========================================
# 8. 가운데 : 계산 결과
# ==========================================

with result_col:

    st.subheader("② 계산 결과")

    with st.container(border=True):

        st.caption("최종 저항값")

        st.markdown(
            f"""
            <h1 style="
                color:#16A36A;
                font-size:38px;
                margin-top:5px;
            ">
                {format_resistance(resistance)}
            </h1>
            """,
            unsafe_allow_html=True
        )

        st.write(
            f"허용 오차: **±{tolerance}%**"
        )

        st.divider()

        st.caption("저항값 범위")

        range_col1, range_col2 = st.columns(2)

        with range_col1:

            st.metric(
                "최솟값",
                format_resistance(minimum)
            )

        with range_col2:

            st.metric(
                "최댓값",
                format_resistance(maximum)
            )

        # 6색 띠일 경우 온도 계수
        if band_count == 6:

            temperature_color = selected_colors[5]

            coefficient = temperature_data[
                temperature_color
            ]

            st.divider()

            st.write(
                f"온도 계수: **{coefficient} ppm/℃**"
            )

    st.markdown("**③ 계산 과정**")

    with st.container(border=True):

        st.write(
            f"숫자 띠: **{digits}**"
        )

        st.write(
            f"배율: **×{multiplier:g}**"
        )

        st.latex(
            f"{significant_value} \\times {multiplier:g}"
            f" = {resistance:g}\\ \\Omega"
        )

        st.write(
            f"허용 오차: **±{tolerance}%**"
        )

        if tolerance_color == "없음":

            st.caption(
                "허용 오차 색상 띠가 없는 경우 "
                "±20%를 적용합니다."
            )


# ==========================================
# 9. 오른쪽 : 색상 코드 안내
# ==========================================

with guide_col:

    st.subheader("④ 색상 코드 안내")

    st.caption(
        "색상별 숫자와 배율을 확인할 수 있습니다."
    )

    # 숫자 및 배율 표
    digit_rows = []

    for color, info in color_data.items():

        if "digit" in info:

            digit_rows.append({
                "색상": color,
                "숫자": info["digit"],
                "배율": f"×{info['multiplier']:g}"
            })

    st.dataframe(
        digit_rows,
        hide_index=True,
        use_container_width=True,
        height=300
    )

    # 허용 오차 표
    st.markdown("**허용 오차**")

    tolerance_rows = [
        {
            "색상": color,
            "허용 오차": f"±{value}%"
        }
        for color, value in tolerance_data.items()
    ]

    st.dataframe(
        tolerance_rows,
        hide_index=True,
        use_container_width=True,
        height=190
    )

    # 6색 띠일 때 온도 계수 표
    if band_count == 6:

        st.markdown("**온도 계수**")

        temperature_rows = [
            {
                "색상": color,
                "계수": f"{value} ppm/℃"
            }
            for color, value in temperature_data.items()
        ]

        st.dataframe(
            temperature_rows,
            hide_index=True,
            use_container_width=True,
            height=150
        )
