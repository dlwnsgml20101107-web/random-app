
import streamlit as st

# ----------------------------------
# 1. 프로그램 기본 설정
# ----------------------------------

st.set_page_config(
    page_title="저항 색상 띠 계산기",
    page_icon="🔌",
    layout="centered"
)

st.title("🔌 저항 색상 띠 계산기")
st.write("저항의 색상 띠를 선택하면 저항값을 자동으로 계산합니다.")

# ----------------------------------
# 2. 색상별 데이터 저장
# ----------------------------------

color_data = {
    "검정색": {"digit": 0, "multiplier": 1, "hex": "#202020"},
    "갈색": {"digit": 1, "multiplier": 10, "hex": "#8B4513"},
    "빨간색": {"digit": 2, "multiplier": 100, "hex": "#E53935"},
    "주황색": {"digit": 3, "multiplier": 1000, "hex": "#EF6C00"},
    "노란색": {"digit": 4, "multiplier": 10000, "hex": "#FDD835"},
    "초록색": {"digit": 5, "multiplier": 100000, "hex": "#388E3C"},
    "파란색": {"digit": 6, "multiplier": 1000000, "hex": "#1976D2"},
    "보라색": {"digit": 7, "multiplier": 10000000, "hex": "#7B1FA2"},
    "회색": {"digit": 8, "multiplier": 100000000, "hex": "#9E9E9E"},
    "흰색": {"digit": 9, "multiplier": 1000000000, "hex": "#FFFFFF"},
    "금색": {"multiplier": 0.1, "hex": "#D4AF37"},
    "은색": {"multiplier": 0.01, "hex": "#C0C0C0"}
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

# ----------------------------------
# 3. 저항값 표시 함수
# ----------------------------------

def format_resistance(value):

    if value >= 1000000:
        return f"{value / 1000000:g} MΩ"

    elif value >= 1000:
        return f"{value / 1000:g} kΩ"

    else:
        return f"{value:g} Ω"


# ----------------------------------
# 4. 저항 색상 띠 개수 선택
# ----------------------------------

st.subheader("① 저항 종류 선택")

band_count = st.radio(
    "색상 띠 개수",
    [4, 5, 6],
    horizontal=True
)

st.caption(
    "4색 띠: 숫자 2개 + 배율 + 허용 오차\n\n"
    "5색 띠: 숫자 3개 + 배율 + 허용 오차\n\n"
    "6색 띠: 숫자 3개 + 배율 + 허용 오차 + 온도 계수"
)



# ----------------------------------
# 5. 가로형 화면 구성 및 색상 안내
# ----------------------------------

left_col, right_col = st.columns([1.4, 1])

with left_col:

    st.subheader("② 색상 띠 입력")

    digit_count = 2 if band_count == 4 else 3

    digit_colors = list(color_data.keys())[:10]
    multiplier_colors = list(color_data.keys())
    tolerance_colors = list(tolerance_data.keys())
    temperature_colors = list(temperature_data.keys())

    band_names = (
        ["첫 번째 숫자", "두 번째 숫자"]
        if band_count == 4
        else ["첫 번째 숫자", "두 번째 숫자", "세 번째 숫자"]
    )

    band_names += ["배율", "허용 오차"]

    if band_count == 6:
        band_names += ["온도 계수"]

    default_colors = {
        4: ["갈색", "검정색", "빨간색", "금색"],
        5: ["갈색", "검정색", "검정색", "빨간색", "갈색"],
        6: ["갈색", "검정색", "검정색", "빨간색", "갈색", "갈색"]
    }

    selected_colors = []

    # 색상 띠 선택 영역을 가로로 배치
    columns = st.columns(band_count)

    for i in range(band_count):

        with columns[i]:

            if i < digit_count:
                options = digit_colors
            elif i == digit_count:
                options = multiplier_colors
            elif i == digit_count + 1:
                options = tolerance_colors
            else:
                options = temperature_colors

            st.caption(f"{i + 1}번째 띠")

            selected = st.selectbox(
                band_names[i],
                options,
                index=options.index(default_colors[band_count][i]),
                key=f"band_{band_count}_{i}"
            )

            selected_colors.append(selected)

            hex_color = color_data[selected]["hex"]

            st.markdown(
                f"""
                <div style="
                    height: 35px;
                    background-color: {hex_color};
                    border: 1px solid #888;
                    border-radius: 5px;
                    margin-top: 5px;
                "></div>
                """,
                unsafe_allow_html=True
            )

with right_col:

    st.subheader("📊 계산에 사용되는 정보")

    # 색상 띠의 역할
    if band_count == 4:
        role_text = "숫자 2개 + 배율 + 허용 오차"
    elif band_count == 5:
        role_text = "숫자 3개 + 배율 + 허용 오차"
    else:
        role_text = "숫자 3개 + 배율 + 허용 오차 + 온도 계수"

    st.info(role_text)

    st.markdown("**색상별 숫자 및 배율**")

    # 숫자 색상 표
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
        height=250
    )

    st.markdown("**허용 오차 및 온도 계수**")

    tolerance_rows = []

    for color, value in tolerance_data.items():
        tolerance_rows.append({
            "색상": color,
            "허용 오차": f"±{value}%"
        })

    st.dataframe(
        tolerance_rows,
        hide_index=True,
        use_container_width=True,
        height=180
    )

# ----------------------------------
# 6. 색상 띠 위치별 역할 안내
# ----------------------------------

st.divider()

st.subheader("📖 색상 띠 위치별 의미")

if band_count == 4:

    role_columns = st.columns(4)

    roles = [
        ("1번째 띠", "첫 번째 숫자"),
        ("2번째 띠", "두 번째 숫자"),
        ("3번째 띠", "배율"),
        ("4번째 띠", "허용 오차")
    ]

elif band_count == 5:

    role_columns = st.columns(5)

    roles = [
        ("1번째 띠", "첫 번째 숫자"),
        ("2번째 띠", "두 번째 숫자"),
        ("3번째 띠", "세 번째 숫자"),
        ("4번째 띠", "배율"),
        ("5번째 띠", "허용 오차")
    ]

else:

    role_columns = st.columns(6)

    roles = [
        ("1번째 띠", "첫 번째 숫자"),
        ("2번째 띠", "두 번째 숫자"),
        ("3번째 띠", "세 번째 숫자"),
        ("4번째 띠", "배율"),
        ("5번째 띠", "허용 오차"),
        ("6번째 띠", "온도 계수")
    ]

for col, (title, description) in zip(role_columns, roles):

    with col:

        with st.container(border=True):
            st.caption(title)
            st.markdown(f"**{description}**")
