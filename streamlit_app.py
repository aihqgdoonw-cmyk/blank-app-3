import random
import time

import streamlit as st

st.set_page_config(
    page_title="받아올림·받아내림 블록 학습 앱",
    page_icon="🧩",
    layout="wide",
)

BLOCK_STYLES = {
    "hundreds": {"label": "100 블록", "emoji": "🟦", "color": "#4f46e5"},
    "tens": {"label": "10 블록", "emoji": "🟩", "color": "#16a34a"},
    "ones": {"label": "1 블록", "emoji": "🟨", "color": "#f59e0b"},
}

BADGE_RULES = [
    ("첫 번째 도전", lambda s: s.total_correct >= 1),
    ("연속 3회 정답", lambda s: s.streak >= 3),
    ("블록 교환왕", lambda s: s.exchange_count >= 5),
    ("레벨 업", lambda s: s.level >= 2),
    ("원리 탐구자", lambda s: s.total_correct >= 10),
]


def init_session_state():
    defaults = {
        "xp": 0,
        "streak": 0,
        "total_correct": 0,
        "exchange_count": 0,
        "badges": [],
        "problem": None,
        "workspace": {"hundreds": 0, "tens": 0, "ones": 0},
        "initial_workspace": {"hundreds": 0, "tens": 0, "ones": 0},
        "feedback": "",
        "explanation": "",
        "problem_solved": False,
        "new_badge": "",
        "last_mode": "혼합",
        "last_difficulty": "중간",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def blocks_from_number(value):
    return {
        "hundreds": value // 100,
        "tens": (value % 100) // 10,
        "ones": value % 10,
    }


def combine_blocks(*block_sets):
    combined = {"hundreds": 0, "tens": 0, "ones": 0}
    for block in block_sets:
        for place in combined:
            combined[place] += block.get(place, 0)
    return combined


def total_value(blocks):
    return blocks["hundreds"] * 100 + blocks["tens"] * 10 + blocks["ones"]


def make_problem(problem_mode, difficulty):
    ranges = {
        "쉬움": (10, 49),
        "중간": (20, 79),
        "어려움": (30, 99),
    }
    low, high = ranges[difficulty]
    mode = problem_mode
    if problem_mode == "혼합":
        mode = random.choice(["받아올림", "받아내림"])

    if mode == "받아올림":
        while True:
            a = random.randint(low, high)
            b = random.randint(low, high)
            if (a % 10 + b % 10) >= 10:
                return {"type": "addition", "a": a, "b": b, "text": f"{a} + {b}"}
    if mode == "받아내림":
        while True:
            a = random.randint(low + 10, high + 20)
            b = random.randint(low, min(a - 1, high))
            if a % 10 < b % 10:
                return {"type": "subtraction", "a": a, "b": b, "text": f"{a} - {b}"}


def generate_problem(problem_mode, difficulty):
    problem = make_problem(problem_mode, difficulty)
    st.session_state.problem = problem
    if problem["type"] == "addition":
        st.session_state.workspace = combine_blocks(
            blocks_from_number(problem["a"]), blocks_from_number(problem["b"])
        )
    else:
        st.session_state.workspace = blocks_from_number(problem["a"])
    st.session_state.initial_workspace = st.session_state.workspace.copy()
    st.session_state.problem_solved = False
    st.session_state.feedback = ""
    st.session_state.explanation = ""
    st.session_state.last_mode = problem_mode
    st.session_state.last_difficulty = difficulty


def set_feedback(success, message):
    st.session_state.feedback = message
    if success:
        st.session_state.problem_solved = True


def update_stats(correct):
    if correct:
        bonus = min(st.session_state.streak, 3) * 5
        gained = 20 + bonus
        st.session_state.xp += gained
        st.session_state.total_correct += 1
        st.session_state.streak += 1
        st.session_state.feedback = f"✅ 정답이에요! 경험치 {gained}점을 얻었어요."
    else:
        st.session_state.streak = 0
        st.session_state.feedback = "❌ 아직 정답이 아니에요. 블록 교환을 다시 확인해 보세요."
    update_badges()


def update_badges():
    class State:
        pass

    state = State()
    state.total_correct = st.session_state.total_correct
    state.streak = st.session_state.streak
    state.exchange_count = st.session_state.exchange_count
    state.level = st.session_state.xp // 100 + 1
    for name, rule in BADGE_RULES:
        if rule(state) and name not in st.session_state.badges:
            st.session_state.badges.append(name)
            st.session_state.new_badge = name


def make_explanation():
    problem = st.session_state.problem
    if problem["type"] == "addition":
        return (
            "일의 자리 블록을 모두 모았더니 10개가 되었어요. "
            "그래서 10개의 1블록을 1개의 10블록으로 바꾸는 것이 받아올림이에요. "
            "이제 열 자리 블록과 함께 더하면 전체 숫자가 정확하게 계산됩니다."
        )
    return (
        "일의 자리에서 필요한 블록이 부족했어요. "
        "그래서 10블록 하나를 10개의 1블록으로 바꿔서 빼는 것이 받아내림이에요. "
        "이 과정을 통해 남은 블록이 정확한 차가 됩니다."
    )


def animate_exchange(message):
    placeholder = st.empty()
    for dot in range(4):
        placeholder.markdown(f"**{message}{'.' * dot}**")
        time.sleep(0.12)
    placeholder.empty()


def exchange_blocks(from_place, to_place, remove_amount, add_amount):
    if st.session_state.workspace[from_place] >= remove_amount:
        st.session_state.workspace[from_place] -= remove_amount
        st.session_state.workspace[to_place] += add_amount
        st.session_state.exchange_count += 1
        animate_exchange(f"{BLOCK_STYLES[from_place]['label']}를 교환 중")


def change_block(place, delta):
    new_value = st.session_state.workspace[place] + delta
    st.session_state.workspace[place] = max(new_value, 0)


def reset_workspace():
    st.session_state.workspace = st.session_state.initial_workspace.copy()
    st.session_state.feedback = ""
    st.session_state.explanation = ""
    st.session_state.problem_solved = False


def render_block_card(name, count):
    style = BLOCK_STYLES[name]
    icons = style["emoji"] * min(count, 10)
    extra = f" <strong>x{count}</strong>" if count > 10 else ""
    return f"""
    <div style="border: 2px solid {style['color']}; border-radius: 18px; padding: 14px; margin-bottom: 10px; background: #ffffff;">
      <div style="font-size: 18px; font-weight: 700; color: {style['color']};">{style['label']}</div>
      <div style="font-size: 28px; margin: 10px 0;">{icons}{extra}</div>
      <div style="color: #444;">개수: <strong>{count}</strong></div>
    </div>
    """


def render_app():
    st.markdown(
        """
        <style>
        .stButton>button { width: 100%; min-height: 3rem; font-size: 1rem; }
        .block-card { background: #f8fafc; border-radius: 18px; padding: 16px; }
        .highlight-box { background: #ecfdf5; border-left: 5px solid #22c55e; border-radius: 12px; padding: 16px; margin-bottom: 16px; }
        .hint-box { background: #eff6ff; border-left: 5px solid #3b82f6; border-radius: 12px; padding: 16px; margin-bottom: 16px; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("🎈 받아올림·받아내림 블록 학습 앱")
    st.markdown(
        "아래 블록을 직접 교환하면서 10개가 모이면 한 자리 위로 올라가고, 1 열에서 10개의 1로 바뀌는 원리를 배워요."
    )

    sidebar = st.sidebar
    sidebar.header("학습 설정")
    mode = sidebar.selectbox(
        "문제 유형",
        ["받아올림", "받아내림", "혼합"],
        index=["받아올림", "받아내림", "혼합"].index(st.session_state.last_mode),
        key="mode_select",
    )
    difficulty = sidebar.selectbox(
        "난이도",
        ["쉬움", "중간", "어려움"],
        index=["쉬움", "중간", "어려움"].index(st.session_state.last_difficulty),
        key="difficulty_select",
    )
    if sidebar.button("새 문제 만들기", key="generate_problem"):
        generate_problem(mode, difficulty)

    sidebar.markdown("---")
    sidebar.subheader("게임 요소")
    sidebar.metric("경험치", st.session_state.xp)
    sidebar.metric("레벨", st.session_state.xp // 100 + 1)
    sidebar.metric("연속 정답", st.session_state.streak)
    sidebar.markdown("### 배지")
    if st.session_state.badges:
        for badge in st.session_state.badges:
            sidebar.markdown(f"- 🏅 {badge}")
    else:
        sidebar.markdown("- 아직 배지가 없어요. 도전해 보세요!")
    if st.session_state.new_badge:
        sidebar.success(f"새로운 배지 획득! {st.session_state.new_badge}")
        st.session_state.new_badge = ""

    st.markdown("---")

    problem = st.session_state.problem
    if problem is None:
        generate_problem(mode, difficulty)
        problem = st.session_state.problem

    a_blocks = blocks_from_number(problem["a"])
    b_blocks = blocks_from_number(problem["b"])

    # ============ 문제 (전체 너비) ============
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 18px; padding: 24px; color: white; text-align: center; margin-bottom: 20px;">
        <div style="font-size: 28px; font-weight: 700; margin-bottom: 10px;">문제</div>
        <div style="font-size: 48px; font-weight: 900; margin-bottom: 15px; letter-spacing: 2px;">{problem['text']}</div>
        <div style="font-size: 16px; opacity: 0.95;">
    """, unsafe_allow_html=True)
    
    if problem["type"] == "addition":
        st.markdown("두 수의 블록을 합친 뒤, 일의 자리가 10개가 되면 교환하세요!", unsafe_allow_html=True)
    else:
        st.markdown("큰 수에서 작은 수를 빼되, 부족하면 교환소를 사용하세요!", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

    # 준비된 블록 정보
    with st.expander("📖 준비된 블록 확인", expanded=True):
        prep_cols = st.columns(2)
        with prep_cols[0]:
            st.markdown(f"**첫 번째 수: {problem['a']}**")
            st.markdown(f"- 10블록: {a_blocks['tens']}개")
            st.markdown(f"- 1블록: {a_blocks['ones']}개")
        with prep_cols[1]:
            st.markdown(f"**두 번째 수: {problem['b']}**")
            st.markdown(f"- 10블록: {b_blocks['tens']}개")
            st.markdown(f"- 1블록: {b_blocks['ones']}개")

    st.markdown("---")

    # ============ 블록 상태 | 교환소 (나란히) ============
    work_col, exchange_col = st.columns([1, 1.2])

    with work_col:
        st.subheader("📦 현재 블록")
        st.markdown(render_block_card("hundreds", st.session_state.workspace["hundreds"]), unsafe_allow_html=True)
        st.markdown(render_block_card("tens", st.session_state.workspace["tens"]), unsafe_allow_html=True)
        st.markdown(render_block_card("ones", st.session_state.workspace["ones"]), unsafe_allow_html=True)
        st.markdown(f"""
        <div style="background: #fef3c7; border-radius: 12px; padding: 14px; text-align: center; margin-top: 10px;">
            <div style="font-size: 14px; color: #92400e;">현재 합계</div>
            <div style="font-size: 36px; font-weight: 900; color: #f59e0b;">{total_value(st.session_state.workspace)}</div>
        </div>
        """, unsafe_allow_html=True)

    with exchange_col:
        st.subheader("🔄 블록 교환소")
        st.markdown("""
        <div style="background: #dcfce7; border: 2px solid #22c55e; border-radius: 12px; padding: 16px;">
            <div style="font-size: 14px; font-weight: 700; color: #166534; margin-bottom: 12px;">교환 버튼을 눌러보세요!</div>
        </div>
        """, unsafe_allow_html=True)

        # 1블록 ↔ 10블록 교환
        ex_row1 = st.columns(2)
        with ex_row1[0]:
            if st.button("🟨 10개 → 🟩\n1블록 10개 to 10블록", key="exchange_ones_to_tens", use_container_width=True):
                exchange_blocks("ones", "tens", 10, 1)
        with ex_row1[1]:
            if st.button("🟩 1개 → 🟨 x10\n10블록 to 1블록 10개", key="exchange_tens_to_ones", use_container_width=True):
                exchange_blocks("tens", "ones", 1, 10)

        # 10블록 ↔ 100블록 교환
        ex_row2 = st.columns(2)
        with ex_row2[0]:
            if st.button("🟩 10개 → 🟦\n10블록 10개 to 100블록", key="exchange_tens_to_hundreds", use_container_width=True):
                exchange_blocks("tens", "hundreds", 10, 1)
        with ex_row2[1]:
            if st.button("🟦 1개 → 🟩 x10\n100블록 to 10블록 10개", key="exchange_hundreds_to_tens", use_container_width=True):
                exchange_blocks("hundreds", "tens", 1, 10)

    st.markdown("---")

    # ============ 직접 조작 & 정답 확인 ============
    action_col1, action_col2, action_col3 = st.columns([1, 1, 1])

    with action_col1:
        st.subheader("직접 조작")
        if problem["type"] == "addition":
            ctrl_cols = st.columns(2)
            if ctrl_cols[0].button("+1 블록", key="add_one", use_container_width=True):
                change_block("ones", 1)
            if ctrl_cols[1].button("-1 블록", key="remove_one", use_container_width=True):
                change_block("ones", -1)
        else:
            ctrl_cols = st.columns(3)
            if ctrl_cols[0].button("-1블록", key="sub_one", use_container_width=True):
                change_block("ones", -1)
            if ctrl_cols[1].button("-10블록", key="sub_ten", use_container_width=True):
                change_block("tens", -1)
            if ctrl_cols[2].button("-100블록", key="sub_hundred", use_container_width=True):
                change_block("hundreds", -1)

    with action_col2:
        st.subheader("작업 관리")
        if st.button("🔄 초기화", key="reset_workspace", use_container_width=True):
            reset_workspace()
        st.markdown("")  # 공간 조정

    with action_col3:
        st.subheader("정답 확인")
        check_button = st.button("✅ 정답 확인!", key="check_answer", use_container_width=True)
        if check_button:
            evaluate_answer()

    st.markdown("---")

    # ============ 피드백 ============
    if st.session_state.feedback:
        if st.session_state.problem_solved:
            st.success(f"**{st.session_state.feedback}**")
            st.info(make_explanation())
        else:
            st.warning(f"**{st.session_state.feedback}**")


def evaluate_answer():
    problem = st.session_state.problem
    current = total_value(st.session_state.workspace)
    if problem["type"] == "addition":
        correct = current == problem["a"] + problem["b"]
    else:
        correct = current == problem["a"] - problem["b"]
    if correct and not st.session_state.problem_solved:
        update_stats(True)
        st.session_state.explanation = make_explanation()
    else:
        update_stats(False)


def main():
    init_session_state()
    render_app()


if __name__ == "__main__":
    main()
