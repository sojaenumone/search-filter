import streamlit as st
import time # 응답 시뮬레이션을 위한 지연 시간

def main():
    st.set_page_config(layout="wide") # 페이지 전체 너비 사용

    st.title("시험지 자료 탐색 및 AI 질의")

    # ------------------ 필터 영역 ------------------
    st.subheader("탐색 필터 설정")

    # 필터 값을 저장할 세션 스테이트 초기화 (Streamlit 앱이 재실행되어도 값 유지)
    # 각 필터의 기본값을 설정합니다.
    if 'year_filter_val' not in st.session_state:
        st.session_state.year_filter_val = "2024"
    if 'school_level_filter_val' not in st.session_state:
        st.session_state.school_level_filter_val = "중등"
    if 'grade_filter_val' not in st.session_state:
        st.session_state.grade_filter_val = "1학년"
    if 'subject_filter_val' not in st.session_state:
        st.session_state.subject_filter_val = "수학"
    if 'domain_filter_val' not in st.session_state:
        st.session_state.domain_filter_val = "영역(단원)"
    if 'question_type_filter_val' not in st.session_state:
        st.session_state.question_type_filter_val = "문항 유형"
    if 'difficulty_filter_val' not in st.session_state:
        st.session_state.difficulty_filter_val = "미지정"
    if 'last_query_sent' not in st.session_state: # 마지막으로 AI에 전달된 쿼리를 저장하여 중복 호출 방지
        st.session_state.last_query_sent = ""

    # 필터 드롭다운 위젯 생성 및 세션 스테이트와 연결
    # Streamlit의 columns는 float 비율을 사용하여 좀 더 유연하게 너비를 조절할 수 있습니다.
    cols_filter = st.columns([1, 1, 1, 1, 1, 1, 1])

    with cols_filter[0]:
        st.session_state.year_filter_val = st.selectbox("년도", ["2024", "2023", "2022"], key="year_filter", index=0)
    with cols_filter[1]:
        st.session_state.school_level_filter_val = st.selectbox("학교급", ["중등", "고등"], key="school_level_filter", index=0)
    with cols_filter[2]:
        st.session_state.grade_filter_val = st.selectbox("학년", ["1학년", "2학년", "3학년"], key="grade_filter", index=0)
    with cols_filter[3]:
        st.session_state.subject_filter_val = st.selectbox("과목", ["수학", "국어", "영어", "과학"], key="subject_filter", index=0)
    with cols_filter[4]:
        # 과목에 따른 세부 과목/단원 옵션 변경
        domain_options_map = {
            "수학": ["영역(단원)", "수와 연산", "문자와 식", "함수", "기하", "확률과 통계"],
            "국어": ["영역(단원)", "문학", "비문학", "화법과 작문", "문법"],
            "영어": ["영역(단원)", "문법", "독해", "듣기", "회화"],
            "과학": ["영역(단원)", "물리", "화학", "생명과학", "지구과학"]
        }
        current_domain_options = domain_options_map.get(st.session_state.subject_filter_val, ["영역(단원)"])
        # 현재 선택된 domain_filter_val이 새로운 옵션에 없으면 기본값으로 리셋
        if st.session_state.domain_filter_val not in current_domain_options:
            st.session_state.domain_filter_val = current_domain_options[0]
        
        st.session_state.domain_filter_val = st.selectbox("영역(단원)", current_domain_options, key="domain_filter", index=current_domain_options.index(st.session_state.domain_filter_val) if st.session_state.domain_filter_val in current_domain_options else 0)

    # 문항 유형 및 난이도 필터
    with cols_filter[5]:
        st.session_state.question_type_filter_val = st.selectbox("문항 유형", ["문항 유형", "객관식", "주관식"], key="question_type_filter", index=0)
    with cols_filter[6]:
        st.session_state.difficulty_filter_val = st.selectbox("난이도", ["미지정", "하", "중", "상"], key="difficulty_filter", index=0)

    # 여기에 '검색' 버튼은 두지 않습니다. 텍스트 검색창으로 질의를 통합합니다.
    st.markdown("---")

    # ------------------ AI 질의 검색창 영역 ------------------
    st.subheader("AI에게 질문하세요")

    # 검색창 입력값. on_change를 사용하지 않고, 텍스트가 변경될 때마다 바로 트리거되도록 합니다.
    # 사용자가 Enter를 누르거나, 포커스를 잃을 때마다 콜백이 호출되도록 하려면 on_change를 쓸 수 있지만,
    # 여기서는 검색창 자체의 값이 변경되면 바로 처리하도록 합니다.
    search_query = st.text_input(
        "궁금한 내용을 입력하세요", # 사용자에게 보여지는 라벨
        placeholder="선택된 필터를 기반으로 궁금한 점을 질문해보세요 (예: 수와 연산에 대해 설명해줘)",
        key="gemini_search_input",
        label_visibility="collapsed" # 상단의 라벨을 숨김
    )

    # Gemini 스타일의 추가 버튼들 (이 버튼들을 누르면 특정 액션이 트리거되도록 할 수 있음)
    col_gem_add, col_gem_deep, col_gem_canvas, col_gem_mic = st.columns([0.5, 1.5, 1.5, 0.5])
    with col_gem_add:
        st.button("➕", key="add_btn") # 파일 첨부 등
    with col_gem_deep:
        st.button("🔎 Deep Research", key="deep_research_btn") # 심층 검색 기능
    with col_gem_canvas:
        st.button("📝 Canvas", key="canvas_btn") # 스케치 등 기능
    with col_gem_mic:
        st.button("🎤", key="mic_btn") # 음성 입력

    # ------------------ AI 응답 영역 ------------------
    st.markdown("---")
    st.subheader("AI 응답")

    # 검색창에 입력된 내용이 있고, 마지막으로 보낸 쿼리와 다를 때만 AI 응답 로직 실행
    if search_query and search_query != st.session_state.last_query_sent:
        # 필터 값 가져오기
        selected_year = st.session_state.year_filter_val
        selected_school_level = st.session_state.school_level_filter_val
        selected_grade = st.session_state.grade_filter_val
        selected_subject = st.session_state.subject_filter_val
        selected_domain = st.session_state.domain_filter_val
        selected_question_type = st.session_state.question_type_filter_val
        selected_difficulty = st.session_state.difficulty_filter_val

        # 최종 프롬프트 구성 (필터와 검색창 내용을 결합)
        full_prompt_parts = []
        if selected_year != "2024": # 기본값인 "2024"가 아니면 포함
            full_prompt_parts.append(f"{selected_year}년도")
        if selected_school_level != "중등": # 기본값인 "중등"이 아니면 포함
            full_prompt_parts.append(f"{selected_school_level}")
        if selected_grade != "1학년": # 기본값인 "1학년"이 아니면 포함
            full_prompt_parts.append(f"{selected_grade}")

        # 과목은 항상 포함 (기본값이 있더라도)
        full_prompt_parts.append(f"{selected_subject} 과목")

        if selected_domain and selected_domain != "영역(단원)": # 기본값이 아니면 포함
            full_prompt_parts.append(f"{selected_domain} 단원")
        if selected_question_type and selected_question_type != "문항 유형": # 기본값이 아니면 포함
            full_prompt_parts.append(f"{selected_question_type} 유형으로")
        if selected_difficulty and selected_difficulty != "미지정": # 기본값이 아니면 포함
            full_prompt_parts.append(f"난이도 '{selected_difficulty}'인")

        context_string = " ".join(full_prompt_parts)
        if context_string:
            final_ai_prompt = f"'{context_string}' 조건에서 '{search_query}'에 대해 설명해줘."
        else:
            final_ai_prompt = f"'{search_query}'에 대해 설명해줘."


        st.write("---")
        st.info("AI 모델에게 질문을 보내는 중...")
        st.write(f"**AI에 전달되는 프롬프트:** {final_ai_prompt}") # AI에 전달되는 최종 프롬프트 표시

        # --- 실제 AI 모델 API 호출 (여기에 구현) ---
        # 예시:
        # from openai import OpenAI
        # client = OpenAI(api_key="YOUR_OPENAI_API_KEY")
        # response = client.chat.completions.create(
        #     model="gpt-3.5-turbo", # 또는 "gemini-pro" 등
        #     messages=[{"role": "user", "content": final_ai_prompt}]
        # )
        # ai_response_text = response.choices[0].message.content
        # ---------------------------------------------

        # 시뮬레이션된 AI 응답
        with st.spinner('AI가 답변을 생성하는 중...'):
            time.sleep(2) # AI 응답 대기 시간 시뮬레이션

            # 필터와 검색 쿼리를 모두 고려한 시뮬레이션 답변
            if selected_school_level == "중등" and selected_grade == "1학년" and selected_subject == "수학":
                if "수와 연산" in selected_domain and "수와연산" in search_query:
                    ai_response_text = """
                    **[중등 1학년 수학 - 수와 연산] 에 대한 상세 설명:**

                    선택하신 조건(중등 1학년 수학, 수와 연산 단원)에 따라 '수와 연산'의 핵심 개념과 예시를 설명해 드리겠습니다. 이 단원은 정수와 유리수의 개념을 확장하고, 이들 수의 사칙연산을 능숙하게 다루는 것을 목표로 합니다.

                    **1. 정수:**
                    * **양의 정수:** 자연수 (1, 2, 3, ...)
                    * **음의 정수:** 양의 정수에 음의 부호를 붙인 수 (-1, -2, -3, ...)
                    * **0:** 양의 정수도 음의 정수도 아닌 수

                    **2. 유리수:**
                    * $\frac{b}{a}$ (단, $a, b$는 정수이고 $a \neq 0$) 꼴로 나타낼 수 있는 수.
                    * 정수, 유한소수, 순환소수가 모두 유리수에 포함됩니다.

                    **3. 수직선:**
                    * 수를 시각적으로 나타내는 선으로, 원점을 기준으로 양수는 오른쪽, 음수는 왼쪽에 위치합니다.

                    **4. 절댓값:**
                    * 수직선에서 원점으로부터 어떤 수까지의 거리입니다. 항상 0 또는 양수이며, 기호 $|a|$로 나타냅니다.
                        * 예: $|-5|=5$, $|3|=3$

                    **5. 정수와 유리수의 사칙연산:**
                    * **덧셈:** 같은 부호는 절댓값의 합에 공통 부호, 다른 부호는 절댓값의 차에 절댓값이 큰 수의 부호를 붙입니다.
                    * **뺄셈:** 빼는 수의 부호를 바꾸어 덧셈으로 계산합니다. (예: $3 - (-2) = 3 + 2 = 5$)
                    * **곱셈:** 부호 규칙(같은 부호는 양수, 다른 부호는 음수)을 따릅니다.
                    * **나눗셈:** 나누는 수의 역수를 곱합니다.
                    * **혼합 계산:** 괄호 → 거듭제곱 → 곱셈/나눗셈 → 덧셈/뺄셈 순서로 계산합니다.

                    **예시 문제:** $(-5) + 3 \times (4 - 6) \div 2$
                    1.  괄호 안: $4 - 6 = -2$
                    2.  곱셈: $3 \times (-2) = -6$
                    3.  나눗셈: $(-6) \div 2 = -3$
                    4.  덧셈: $(-5) + (-3) = -8$
                    """
                elif "함수" in selected_domain and "함수" in search_query:
                    ai_response_text = """
                    **[중등 1학년 수학 - 함수] 에 대한 상세 설명:**

                    선택하신 조건(중등 1학년 수학, 함수 단원)에 따라 '함수'의 기본 개념을 설명해 드리겠습니다. 중학교 1학년에서는 주로 '정비례'와 '반비례' 관계를 통해 함수의 개념을 익히게 됩니다.

                    **1. 함수의 개념:**
                    * 두 변수 $x$와 $y$ 사이에서 $x$의 값이 하나 정해지면, 그에 따라 $y$의 값이 **오직 하나로 결정되는 관계**를 함수라고 합니다. ($y$는 $x$의 함수라고 하며, $y=f(x)$로 나타냅니다.)

                    **2. 정비례:**
                    * $y = ax$ (단, $a \neq 0$)의 형태로 나타나는 관계입니다.
                    * $x$ 값이 2배, 3배, ...가 되면 $y$ 값도 2배, 3배, ...가 됩니다.
                    * 원점을 지나는 직선 그래프를 갖습니다.

                    **3. 반비례:**
                    * $y = \frac{a}{x}$ (단, $a \neq 0, x \neq 0$)의 형태로 나타나는 관계입니다.
                    * $x$ 값이 2배, 3배, ...가 되면 $y$ 값은 $\frac{1}{2}$배, $\frac{1}{3}$배, ...가 됩니다.
                    * 원점에 대해 대칭인 한 쌍의 곡선 그래프를 갖습니다.

                    **예시:**
                    * **정비례:** 한 개에 500원 하는 사과 $x$개의 가격 $y$원 ($y = 500x$)
                    * **반비례:** 넓이가 24인 직사각형의 가로 길이 $x$와 세로 길이 $y$ ($y = \frac{24}{x}$)
                    """
                else:
                    ai_response_text = f"""
                    **[선택된 필터 조건: {selected_year}년도 {selected_school_level} {selected_grade} {selected_subject} 과목, 영역: {selected_domain}, 문항 유형: {selected_question_type}, 난이도: {selected_difficulty}]**

                    **질문:** '{search_query}'에 대한 답변입니다.

                    현재 시뮬레이션된 답변은 '중등 1학년 수학 - 수와 연산' 또는 '함수' 관련 질문에만 특화되어 있습니다. 다른 질문이나 필터 조합에 대한 상세한 응답은 실제 AI 모델을 연동해야 합니다.
                    """
            else:
                 ai_response_text = f"""
                **[선택된 필터 조건: {selected_year}년도 {selected_school_level} {selected_grade} {selected_subject} 과목, 영역: {selected_domain}, 문항 유형: {selected_question_type}, 난이도: {selected_difficulty}]**

                **질문:** '{search_query}'에 대한 답변입니다.

                현재 시뮬레이션된 답변은 '중등 1학년 수학' 필터에만 맞춰져 있습니다. 다른 필터 조합이나 질문에 대한 자세한 응답은 실제 AI 모델을 연동해야 합니다.
                """

        st.success("AI 답변 완료!")
        st.markdown(ai_response_text) # 마크다운 형식으로 표시

        # 마지막으로 AI에 보낸 쿼리 저장
        st.session_state.last_query_sent = search_query
    else:
        st.info("상단의 필터를 설정하고 아래 검색창에 궁금한 점을 입력해주세요. 입력 즉시 AI가 답변합니다.")

if __name__ == "__main__":
    main()