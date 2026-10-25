import streamlit as st
from openai import OpenAI
import matplotlib.pyplot as plt
import numpy as np
from dotenv import load_dotenv
import os
import re

# Load environment
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    st.error("⚠️ GROQ_API_KEY not found. Please check your .env file.")
    st.stop()

client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")

# Page config
st.set_page_config(page_title="MathMentor AI", page_icon="📐", layout="wide")

# Session state init
defaults = {
    'practice_mode': False,
    'current_problem_idx': 0,
    'practice_questions': [],
    'practice_done': False,
    'wrong_questions': [],
    'weak_topics': {},
    'discussion_posts': [{"author": "MathMentor Team", "text": "Welcome! Share your problem-solving tips here. 👋"}],
    'last_solution': "",
    'last_func': ""
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# Title
st.title("📐 MathMentor AI")
st.subheader("Your AI math tutor that guides, checks, and tracks your progress")

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    app_mode = st.radio("App Mode", [
        "Free Question Mode",
        "Knowledge Practice Mode",
        "My Mistake Notebook",
        "Community Discussion"
    ])

    subject = "Calculus"
    mode = "Full Solution"
    if app_mode == "Free Question Mode":
        subject = st.selectbox("Math Subject", ["Calculus", "Algebra", "Trigonometry"])
        mode = st.radio("Tutor Mode", ["Full Solution", "Hint Only"])

    show_plot = st.checkbox("Show interactive graph", value=True)

    # Progress dashboard
    st.markdown("---")
    st.markdown("### 📊 Your Progress")
    if st.session_state.wrong_questions:
        st.metric("Questions Practiced", len(st.session_state.wrong_questions))
        st.caption("Weakest topics:")
        for topic, count in sorted(st.session_state.weak_topics.items(), key=lambda x: -x[1])[:3]:
            st.progress(min(count/5, 1.0), text=f"{topic}: {count}")
    else:
        st.caption("No questions practiced yet.")

    st.markdown("---")
    st.caption("🏆 HackPSU Nittany AI Challenge")

# Prompt builder
def clean_latex(text):
    # Strip ALL LaTeX commands and messy formatting
    text = re.sub(r'\\[a-zA-Z]+', '', text)  # remove all \command
    text = text.replace('{', '(').replace('}', ')')  # convert braces
    text = text.replace('$$', '')  # remove all dollar signs
    text = text.replace('\\', '')  # remove leftover backslashes
    text = text.replace('[', '').replace(']', '')  # remove bracket wrappers
    text = text.replace('·', '').strip()  # remove weird bullets
    # Clean up extra spaces and empty lines
    text = re.sub(r' +', ' ', text)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    return text.strip()

def build_prompt(subject, mode):
    return f"""You are an expert math tutor for {subject}.
RULES - FOLLOW EXACTLY:
1. Break solution into clear numbered steps.
2. Write math in PLAIN TEXT with Unicode symbols:
   - Exponents: x^2, x^3
   - Fractions: a/b
   - Square root: sqrt(x)
   - Derivative: f'(x)
   - Integral: ∫ from a to b of f(x) dx
   - NO backslashes, NO LaTeX commands, NO $$
3. Put each formula on its own line.
4. After each step, write a plain English explanation.
5. End with "Common Mistakes:" section with 2-3 bullet points.
MODE: {mode}
- Hint Only: do NOT give final answer, only guiding questions.
- Full Solution: show all steps and final answer.
"""

# Safe eval
def safe_eval(expr, x_vals):
    expr = expr.replace("f(x)", "").replace("=", "").strip()
    expr = expr.replace("{", "").replace("}", "").replace("\\", "")
    expr = expr.replace("^", "**")
    expr = re.sub(r'(\d)([a-zA-Z])', r'\1*\2', expr)
    expr = " ".join(expr.split())
    allowed = {"np": np, "x": x_vals, "sin": np.sin, "cos": np.cos, "tan": np.tan,
               "exp": np.exp, "log": np.log, "sqrt": np.sqrt, "pi": np.pi, "e": np.e}
    return eval(expr, {"__builtins__": {}}, allowed)

# === FREE QUESTION MODE ===
if app_mode == "Free Question Mode":
    # Math symbol keyboard (Desmos-style)
    st.markdown("**Quick symbols:**")
    symbols_row1 = ["²", "³", "√", "π", "∂", "∫", "÷", "×", "−", "θ"]
    cols1 = st.columns(len(symbols_row1))
    for i, sym in enumerate(symbols_row1):
        if cols1[i].button(sym, key=f"sym1_{i}"):
            if 'user_input' not in st.session_state:
                st.session_state.user_input = ""
            st.session_state.user_input += sym

    symbols_row2 = ["sin", "cos", "tan", "log", "ln", "e", "∞", "≤", "≥", "≠"]
    cols2 = st.columns(len(symbols_row2))
    for i, sym in enumerate(symbols_row2):
        if cols2[i].button(sym, key=f"sym2_{i}"):
            if 'user_input' not in st.session_state:
                st.session_state.user_input = ""
            st.session_state.user_input += sym + "("

    user_q = st.text_area("📝 Enter your math problem:", height=100,
                          value=st.session_state.get('user_input', ''),
                          placeholder="Type or tap symbols above...")
    # Sync back
    st.session_state.user_input = user_q

    submit = st.button("✨ Get Solution", type="primary")

    if submit and user_q.strip():
        with st.spinner("🤔 Solving..."):
            try:
                resp = client.chat.completions.create(
                    model="openai/gpt-oss-20b",
                    messages=[
                        {"role": "system", "content": build_prompt(subject, mode)},
                        {"role": "user", "content": user_q}
                    ],
                    temperature=0.3
                )
                sol = clean_latex(resp.choices[0].message.content)
                st.session_state.last_solution = sol
                # Extract function for plotting - robust parsing
                if "f(x)" in user_q:
                    after = user_q.split("f(x)")[1]
                    if "=" in after:
                        func = after.split("=")[1].strip()
                        # Cut off at comma/period/text
                        func = re.split(r'[,.\n]', func)[0].strip()
                        # Convert unicode superscripts
                        func = func.replace("²", "^2").replace("³", "^3")
                        func = func.replace("×", "*")
                        st.session_state.last_func = func
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

    # Show solution if exists
    if st.session_state.last_solution:
        st.markdown("### ✅ Solution")
        st.markdown(st.session_state.last_solution)

        # Interactive plot - separate block, won't disappear on slider move
        if show_plot and st.session_state.last_func:
            st.markdown("---")
            st.markdown("### 📈 Interactive Graph")
            try:
                x = np.linspace(-10, 10, 500)
                y = safe_eval(st.session_state.last_func, x)

                tangent_x = st.slider("Drag to see tangent line:", -10.0, 10.0, 0.0, 0.1, key="tangent_slider")
                h = 0.001
                slope = (safe_eval(st.session_state.last_func, np.array([tangent_x+h]))[0] - safe_eval(st.session_state.last_func, np.array([tangent_x]))[0]) / h
                y_at_x = safe_eval(st.session_state.last_func, np.array([tangent_x]))[0]

                fig, ax = plt.subplots(figsize=(9, 5))
                ax.plot(x, y, color="#2563eb", linewidth=2.5, label="f(x)")
                tx = np.linspace(tangent_x-3, tangent_x+3, 100)
                ax.plot(tx, slope*(tx-tangent_x)+y_at_x, color="#dc2626", linewidth=2, linestyle="--", label=f"Tangent: slope={slope:.2f}")
                ax.scatter([tangent_x], [y_at_x], color="#dc2626", s=80, zorder=5)
                ax.grid(True, alpha=0.3, linestyle="--")
                ax.axhline(y=0, color="#666", linewidth=0.8)
                ax.axvline(x=0, color="#666", linewidth=0.8)
                ax.legend()
                st.pyplot(fig)
                st.info(f"📍 At x={tangent_x:.1f}: f(x)={y_at_x:.2f}, slope={slope:.2f}")
            except Exception as e:
                st.caption("ℹ️ Graph not available for this function.")

        # Answer checker
        st.markdown("---")
        st.markdown("### ✏️ Check Your Answer")
        user_ans = st.text_area("Your solution:", height=100, key="check_ans")
        check_btn = st.button("🔍 Check My Answer")

        if check_btn and user_ans.strip():
            with st.spinner("Comparing..."):
                try:
                    check_resp = client.chat.completions.create(
                        model="openai/gpt-oss-20b",
                        messages=[
                            {"role": "system", "content": "You are a math tutor. Grade the student's answer. Point out exactly where they went wrong, what concept they missed, and how to fix it. Be encouraging. DO NOT use LaTeX commands like \\frac, $$, or \\int. Write math in plain text: x^2, a/b, f'(x), and write integrals in plain words."},
                            {"role": "user", "content": f"Problem: {user_q}\nCorrect solution: {st.session_state.last_solution}\nStudent answer: {user_ans}"}
                        ],
                        temperature=0.3
                    )
                    fb = clean_latex(check_resp.choices[0].message.content)
                    st.markdown("### 📊 Feedback:")
                    st.markdown(fb)
                    st.session_state.wrong_questions.append({
                        "question": user_q, "answer": user_ans, "feedback": fb, "topic": subject
                    })
                    st.session_state.weak_topics[subject] = st.session_state.weak_topics.get(subject, 0) + 1
                    st.success("✅ Saved to your Mistake Notebook!")
                except Exception as e:
                    st.warning("Could not check answer right now.")

# === PRACTICE MODE ===
elif app_mode == "Knowledge Practice Mode":
    st.markdown("### 🎯 Knowledge Practice Mode")
    topic = st.selectbox("Choose topic:", [
        "Power Rule Derivatives",
        "Chain Rule",
        "Product Rule",
        "Trigonometric Derivatives",
        "Algebra Factoring",
        "Linear Equations",
        "Quadratic Formula",
        "Custom..."
    ])
    if topic == "Custom...":
        topic = st.text_input("Enter your own topic:", placeholder="e.g. Implicit Differentiation")

    if not st.session_state.practice_questions:
        start = st.button("🚀 Start Practice Set", type="primary")
        if start:
            with st.spinner("Generating problems..."):
                gen = client.chat.completions.create(
                    model="openai/gpt-oss-20b",
                    messages=[
                        {"role": "system", "content": f"Generate exactly 3 {topic} problems. Easy, medium, hard. Format: 'Problem 1: ...', 'Problem 2: ...', 'Problem 3: ...'."},
                        {"role": "user", "content": f"Create 3 {topic} problems."}
                    ],
                    temperature=0.7
                )
                qs = [q.strip() for q in gen.choices[0].message.content.split("Problem") if q.strip()][:3]
                st.session_state.practice_questions = qs
                st.session_state.current_problem_idx = 0
                st.rerun()

    if st.session_state.practice_questions and not st.session_state.practice_done:
        idx = st.session_state.current_problem_idx
        st.markdown(f"### Problem {idx+1}/3")
        st.markdown(st.session_state.practice_questions[idx])
        ans = st.text_area("Your answer:", height=120, key=f"ans_{idx}")
        submit_ans = st.button("Submit Answer", type="primary")

        if submit_ans and ans.strip():
            with st.spinner("Grading..."):
                grade = client.chat.completions.create(
                    model="openai/gpt-oss-20b",
                    messages=[
                        {"role": "system", "content": "Grade the student's answer. Give correct solution, point out mistakes, be encouraging. DO NOT use LaTeX commands like \\frac, $$, or \\int. Write math in plain text: x^2, a/b, f'(x), and write integrals in plain words."},
                        {"role": "user", "content": f"Problem: {st.session_state.practice_questions[idx]}\nStudent answer: {ans}"}
                    ],
                    temperature=0.3
                )
                fb = clean_latex(grade.choices[0].message.content)
                st.markdown("### 📝 Feedback:")
                st.markdown(fb)
                st.session_state.wrong_questions.append({
                    "question": st.session_state.practice_questions[idx], "answer": ans, "feedback": fb, "topic": topic
                })
                st.session_state.weak_topics[topic] = st.session_state.weak_topics.get(topic, 0) + 1

                if idx < 2:
                    next_b = st.button("Next Problem →")
                    if next_b:
                        st.session_state.current_problem_idx += 1
                        st.rerun()
                else:
                    finish = st.button("Finish Set")
                    if finish:
                        st.session_state.practice_done = True
                        st.rerun()

    if st.session_state.practice_done:
        st.success("🎉 Practice Set Complete!")
        st.info("Check your Mistake Notebook to review what you missed.")
        restart = st.button("🔄 New Practice Set")
        if restart:
            st.session_state.practice_questions = []
            st.session_state.current_problem_idx = 0
            st.session_state.practice_done = False
            st.rerun()

# === MISTAKE NOTEBOOK ===
elif app_mode == "My Mistake Notebook":
    st.markdown("### 📕 Your Mistake Notebook")
    if not st.session_state.wrong_questions:
        st.info("No mistakes yet! Practice problems to build your notebook.")
    else:
        st.warning(f"⚠️ {len(st.session_state.wrong_questions)} questions to review.")
        for i, q in enumerate(st.session_state.wrong_questions):
            with st.expander(f"Q{i+1}: {q['question'][:50]}..."):
                st.markdown(f"**Problem:** {q['question']}")
                st.markdown(f"**Your answer:** {q['answer']}")
                st.markdown(f"**Feedback:** {q['feedback']}")

# === COMMUNITY DISCUSSION ===
elif app_mode == "Community Discussion":
    st.markdown("### 💬 Community Discussion")
    st.caption("Share tips, notes, and problem-solving tricks.")
    new_post = st.text_area("Share a tip:", height=80, key="new_post")
    post_btn = st.button("📢 Post", type="primary")
    if post_btn and new_post.strip():
        st.session_state.discussion_posts.append({"author": "You", "text": new_post.strip()})
        st.rerun()
    st.markdown("---")
    for post in reversed(st.session_state.discussion_posts):
        st.markdown(f"**{post['author']}**")
        st.markdown(post['text'])
        st.markdown("---")

st.markdown("---")
st.caption("MathMentor AI · Nittany AI Challenge · HackPSU 2026")
