
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
# 5. 색상 띠 입력
# ----------------------------------

st.subheader("② 색상 띠 입력")

digit_count = 2 if band_count == 4 else 3

digit_colors = list(color_data.keys())[:10]

multiplier_colors = list(color_data.keys())

tolerance_colors = list(tolerance_data.keys())

temperature_colors = list(temperature_data.keys())

selected_colors = []

# 색상 띠의 역할 설정
band_names = (
    ["첫 번째 숫자", "두 번째 숫자"]
    if band_count == 4
    else ["첫 번째 숫자", "두 번째 숫자", "세 번째 숫자"]
)

band_names += ["배율", "허용 오차"]

if band_count == 6:
    band_names += ["온도 계수"]

# 기본 색상 설정
default_colors = {
    4: ["갈색", "검정색", "빨간색", "금색"],
    5: ["갈색", "검정색", "검정색", "빨간색", "갈색"],
    6: ["갈색", "검정색", "검정색", "빨간색", "갈색", "갈색"]
}

columns = st.columns(band_count)

for i in range(band_count):

    with columns[i]:

        st.write(f"**{i + 1}번째 띠**")

        # 위치에 따라 선택 가능한 색상 제한
        if i < digit_count:
            options = digit_colors

        elif i == digit_count:
            options = multiplier_colors

        elif i == digit_count + 1:
            options = tolerance_colors

        else:
            options = temperature_colors

        default_color = default_colors[band_count][i]

        selected = st.selectbox(
            band_names[i],
            options,
            index=options.index(default_color),
            key=f"band_{band_count}_{i}"
        )

        selected_colors.append(selected)

        # 선택된 색상을 화면에 표시
        hex_color = color_data[selected]["hex"]

        st.markdown(
            f"""
            <div style="
                height: 45px;
                background-color: {hex_color};
                border: 1px solid #888;
                border-radius: 5px;
                margin-top: 5px;
            "></div>
            """,
            unsafe_allow_html=True
        )

# ----------------------------------
# 6. 저항값 계산
# ----------------------------------

st.divider()
st.subheader("③ 계산 결과")

# 앞쪽 색상 띠의 숫자를 하나의 정수로 결합
digits = ""

for i in range(digit_count):
    digits += str(color_data[selected_colors[i]]["digit"])

significant_value = int(digits)

# 배율 계산
multiplier = color_data[selected_colors[digit_count]]["multiplier"]

# 최종 저항값
resistance = significant_value * multiplier

# 허용 오차 계산
tolerance_color = selected_colors[digit_count + 1]

tolerance = tolerance_data[tolerance_color]

# 허용 오차 범위
minimum = resistance * (1 - tolerance / 100)
maximum = resistance * (1 + tolerance / 100)

# ----------------------------------
# 7. 결과 출력
# ----------------------------------

st.success("저항값 계산 완료!")

st.metric(
    label="계산된 저항값",
    value=format_resistance(resistance)
)

st.write(f"**허용 오차:** ±{tolerance}%")

st.write(
    f"**최소 저항값:** {format_resistance(minimum)}"
)

st.write(
    f"**최대 저항값:** {format_resistance(maximum)}"
)

# 6색 띠일 경우 온도 계수 표시
if band_count == 6:

    temperature_color = selected_colors[5]

    temperature_coefficient = temperature_data[temperature_color]

    st.write(
        f"**온도 계수:** {temperature_coefficient} ppm/℃"
    )

# ----------------------------------
# 8. 계산 과정 출력
# ----------------------------------

st.divider()
st.subheader("④ 계산 과정")

st.write("**1. 숫자 띠 해석**")

for i in range(digit_count):

    color = selected_colors[i]

    number = color_data[color]["digit"]

    st.write(
        f"{i + 1}번째 띠 ({color}) → {number}"
    )

st.write("**2. 배율 해석**")

st.write(
    f"{selected_colors[digit_count]} → ×{multiplier:g}"
)

st.write("**3. 저항값 계산**")

st.latex(
    f"{significant_value} \\times {multiplier:g}"
    f" = {resistance:g}\\ \\Omega"
)

st.write("**4. 허용 오차 해석**")

st.write(
    f"{tolerance_color} → ±{tolerance}%"
)

st.info(
    f"최종 결과: {format_resistance(resistance)} "
    f"±{tolerance}%"
)

# ----------------------------------
# 9. 색상별 참고 정보
# ----------------------------------

with st.expander("색상 띠별 의미 알아보기"):

    st.write("**숫자 및 배율**")

    for color, info in color_data.items():

        st.write(
            f"- {color}: 숫자 {info['digit'] if 'digit' in info else '-'}, "
            f"배율 ×{info['multiplier']:g}"
        )

    st.write("**허용 오차**")

    for color, value in tolerance_data.items():

        st.write(f"- {color}: ±{value}%")

    st.write("**온도 계수**")

    for color, value in temperature_data.items():

        st.write(f"- {color}: {value} ppm/℃")
