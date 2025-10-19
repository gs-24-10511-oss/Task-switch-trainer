import random
import time
import pandas as pd
import streamlit as st

# =============== 기본 설정 ===============
st.set_page_config(page_title="과제 전환 훈련", page_icon="🧩", layout="centered")

ARABIC_POOL = list(range(1, 31))
KOREAN_NUMS = [
    "하나","둘","셋","넷","다섯","여섯","일곱","여덟","아홉","열",
    "열하나","열둘","열셋","열넷","열다섯","열여섯","열일곱","열여덟","열아홉","스물",
    "스물하나","스물둘","스물셋","스물넷","스물다섯","스물여섯","스물일곱","스물여덟","스물아홉","서른"
]
KIDX = {v: i for i, v in enumerate(KOREAN_NUMS)}

# =============== 유틸 함수 ===============
def gen_problem():
    """아라비아 3개 또는 한글 3개로 한 문제 생성"""
    is_arabic = random.choice([True, False])
    if is_arabic:
        nums = random.sample(ARABIC_POOL, 3)
        random.shuffle(nums)
        options = [str(n) for n in nums]
        correct = str(max(nums))  # 아라비아 → 가장 큰 수
        qtype = "아라비아"
        rule = "가장 큰 숫자"
    else:
        nums = random.sample(KOREAN_NUMS, 3)
        random.shuffle(nums)
        options = nums[:]
        correct = min(nums, key=lambda x: KIDX[x])  # 한글 → 가장 작은 수
        qtype = "한글"
        rule = "가장 작은 숫자"
    return options, correct, qtype, rule

def new_quiz(total_q, time_limit):
    st.session_state.total = int(total_q)
    st.session_state.tlimit = int(time_limit)
    st.session_state.idx = 0
    st.session_state.score = 0
    st.session_state.history = []
    st.session_state.start_time = time.time()
    st.session_state.q = gen_problem()

def submit_answer(choice_text=None, force_timeout=False):
    """답안 제출 처리 (버튼 클릭 시 호출)"""
    if "q" not in st.session_state or st.session_state.q is None:
        return
    options, correct, qtype, rule = st.session_state.q
    elapsed = time.time() - st.session_state.start_time

    # 시간초과 판단: 제한 초과면 무조건 시간초과
    is_timeout = force_timeout or (elapsed > st.session_state.tlimit)
    if is_timeout:
        result = "시간초과"
        selected = "미응답" if choice_text is None else choice_text
        add_score = 0
    else:
        selected = choice_text
        if selected == correct:
            result = "정답"
            add_score = 1
        else:
            result = "오답"
            add_score = 0

    st.session_state.score += add_score
    st.session_state.history.append({
        "문항": st.session_state.idx + 1,
        "문제유형": qtype,
        "규칙": rule,
        "보기": " / ".join(options),
        "선택": selected,
        "정답": correct,
        "경과시간(s)": round(elapsed, 2),
        "결과": result
    })

    # 다음 문제로 이동 or 종료
    st.session_state.idx += 1
    if st.session_state.idx < st.session_state.total:
        st.session_state.q = gen_problem()
        st.session_state.start_time = time.time()
    else:
        st.session_state.q = None  # 종료

# =============== 사이드바: 설정/학생정보 ===============
with st.sidebar:
    st.header("설정")
    student_name = st.text_input("이름", "")
    class_name = st.text_input("반(선택)", "")
    student_id = st.text_input("번호(선택)", "")
    total_q = st.number_input("문항 수", min_value=5, max_value=50, value=15, step=1)
    time_limit = st.number_input("문제당 제한(초)", min_value=3, max_value=20, value=5, step=1)
    seed_val = st.text_input("랜덤 시드(선택, 동일문제 재현용)", "")

    if st.button("새 게임 시작"):
        if seed_val.strip():
            try:
                random.seed(seed_val.strip())
            except Exception:
                pass
        new_quiz(total_q, time_limit)

# =============== 본문 UI ===============
st.title("🧩 과제 전환 훈련")
st.caption("아라비아 숫자만 제시되면 가장 큰 수, 한글 숫자만 제시되면 가장 작은 수를 선택하세요.")

# 초기 상태 보정
if "total" not in st.session_state:
    new_quiz(total_q, time_limit)

# 진행 화면
if st.session_state.q is not None:
    options, correct, qtype, rule = st.session_state.q
    remain = max(0, st.session_state.tlimit - (time.time() - st.session_state.start_time))

    top = st.container()
    with top:
        col1, col2, col3 = st.columns([1,1,1])
        with col1:
            st.markdown(f"**진행:** {st.session_state.idx + 1} / {st.session_state.total}")
        with col2:
            st.markdown(f"**규칙:** {rule}")
        with col3:
            st.markdown(f"**남은 시간:** {remain:0.1f}초")

        st.progress(min(1.0, (st.session_state.idx) / st.session_state.total))

        st.markdown("---")
        st.markdown(f"### {' / '.join(options)}")

        cols = st.columns(3)
        for i, opt in enumerate(options):
            if cols[i].button(opt, use_container_width=True):
                submit_answer(choice_text=opt)

        # 시간만 초과했을 때, 사용자가 눌러서 넘어갈 수 있도록 '시간초과(패스)' 버튼 제공
        st.markdown("")
        if st.button("⏰ 시간초과(패스)"):
            submit_answer(choice_text=None, force_timeout=True)

else:
    # 종료 화면
    st.success(f"완료! 정답 {st.session_state.score}/{st.session_state.total} "
               f"({st.session_state.score/st.session_state.total*100:.1f}%)")

    df = pd.DataFrame(st.session_state.history)
    # 학생 정보 메타 부가
    if "이름" not in df.columns:
        df.insert(0, "이름", student_name if student_name else "미기입")
    else:
        df["이름"] = student_name if student_name else "미기입"
    if "반" not in df.columns:
        df.insert(1, "반", class_name if class_name else "미기입")
    else:
        df["반"] = class_name if class_name else "미기입"
    if "번호" not in df.columns:
        df.insert(2, "번호", student_id if student_id else "미기입")
    else:
        df["번호"] = student_id if student_id else "미기입"

    st.subheader("결과 테이블")
    st.dataframe(df, use_container_width=True)

    # CSV 다운로드
    csv_bytes = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="📥 결과 CSV 다운로드",
        data=csv_bytes,
        file_name=f"과제전환훈련_결과_{student_name or '미기입'}.csv",
        mime="text/csv"
    )

    # 다시 시작
    st.markdown("---")
    if st.button("다시 시작"):
        new_quiz(st.session_state.total, st.session_state.tlimit)
