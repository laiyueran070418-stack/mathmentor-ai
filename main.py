import streamlit as st
from openai import OpenAI
import matplotlib.pyplot as plt
import numpy as np
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize Groq client (compatible with OpenAI SDK, free tier)
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    st.error("⚠️ GROQ_API_KEY not found. Please create a .env file with your Groq API key.")
    st.stop()

client = OpenAI(
    api_key=api_key,
    base_url="https://api.groq.com/openai/v1"
)

# Page config
st.set_page_config(
    page_title="MathMentor AI",
    page_icon="📐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title
st.title("📐 MathMentor AI")
st.subheader("Your AI-powered step-by-step math tutor with function visualization")

# Sidebar settings
with st.sidebar:
    st.header("⚙️ Settings")

    subject = st.selectbox(
        "Math Subject",
        ["Calculus", "Algebra", "Trigonometry", "General Math"]
    )

    mode = st.radio(
        "Tutor Mode",
        ["Full Step-by-Step Solution", "Hint Only (No Final Answer)"],
        help="Hint mode gives you guiding questions without revealing the answer."
    )

    show_plot = st.checkbox(
        "Auto-generate function graph",
        value=True,
        help="Automatically plot functions mentioned in the solution."
    )

    st.markdown("---")
    st.caption("🏆 Built for HackPSU Nittany AI Challenge")

# Input area
user_question = st.text_area(
    "📝 Enter your math problem:",
    height=120,
    placeholder="Example: Find the derivative of f(x) = x² + 4x - 2"
)

submit = st.button("✨ Get Solution", type="primary")

# System prompt builder
def build_system_prompt(subject, mode):
    base_rules = f"""
You are an expert math tutor specializing in {subject}.
Your goal is to help students learn, not just give answers.

Rules:
1. Use clear, step-by-step explanations. Do NOT skip steps.
2. Use LaTeX formatting for all math expressions:
   - Inline math: wrap with $...$
   - Display math: wrap with $$...$$
3. At the END of your response, extract the main function to plot.
   Format: [PLOT_FUNC: f(x) = x^2 + 3x]
   If there is no function to plot, write: [PLOT_FUNC: NONE]
4. Keep explanations concise but thorough.
5. Use simple English suitable for college students.
"""

    if "Hint" in mode:
        mode_rules = """
HINT MODE ACTIVE:
- Do NOT give the final answer or complete solution.
- Give guiding questions and hints about what approach to use.
- Point out which formulas or methods are relevant.
- Let the student work through the problem themselves.
- Do NOT reveal the final numerical or symbolic result.
"""
    else:
        mode_rules = """
FULL SOLUTION MODE:
- Show every step clearly.
- Explain WHY each step works, not just what to do.
- State the final answer clearly at the end.
"""

    return base_rules + mode_rules

# Function to safely evaluate math expressions for plotting
def safe_eval_function(expr, x_values):
    """Safely evaluate a math expression for plotting."""
    # Remove f(x) = prefix if present
    expr = expr.replace("f(x)", "").replace("=", "").strip()
    # Convert math notation ^ to Python exponent **
    expr = expr.replace("^", "**")

    # Allowed namespaces for safe eval
    allowed_names = {
        "np": np,
        "sin": np.sin,
        "cos": np.cos,
        "tan": np.tan,
        "exp": np.exp,
        "log": np.log,
        "sqrt": np.sqrt,
        "pi": np.pi,
        "e": np.e
    }

    return eval(expr, {"__builtins__": {}}, allowed_names)

# Main logic
if submit and user_question.strip():
    with st.spinner("🤔 Thinking through the problem..."):
        try:
            # Call Groq LLM
            response = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[
                    {"role": "system", "content": build_system_prompt(subject, mode)},
                    {"role": "user", "content": user_question}
                ],
                temperature=0.3
            )

            full_response = response.choices[0].message.content

            # Split response and plot function tag
            if "[PLOT_FUNC:" in full_response:
                parts = full_response.split("[PLOT_FUNC:")
                solution_text = parts[0].strip()
                plot_expr = parts[1].replace("]", "").strip()
            else:
                solution_text = full_response
                plot_expr = "NONE"

            # Show solution
            st.markdown("### ✅ Solution")

            if "Hint" in mode:
                st.info("💡 Hint Mode: This shows guiding steps only. Try solving it yourself!")

            st.markdown(solution_text)

            # Plot function if requested
            if show_plot and plot_expr.upper() != "NONE":
                st.markdown("### 📈 Function Visualization")
                try:
                    x = np.linspace(-10, 10, 500)
                    y = safe_eval_function(plot_expr, x)

                    fig, ax = plt.subplots(figsize=(8, 4))
                    ax.plot(x, y, color="#1f77b4", linewidth=2)
                    ax.grid(True, alpha=0.3)
                    ax.axhline(y=0, color="k", linestyle="-", alpha=0.3, linewidth=0.5)
                    ax.axvline(x=0, color="k", linestyle="-", alpha=0.3, linewidth=0.5)
                    ax.set_xlabel("x")
                    ax.set_ylabel("f(x)")
                    ax.set_title(f"Plot of {plot_expr}")
                    st.pyplot(fig)
                except Exception as plot_err:
                    st.warning(f"⚠️ Could not generate graph: {str(plot_err)}")
                    st.caption("The text solution above is still valid.")

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            st.warning("Please check your API key and try again.")

elif submit and not user_question.strip():
    st.warning("⚠️ Please enter a math problem first!")

# Footer
st.markdown("---")
st.caption("MathMentor AI · Nittany AI Challenge · HackPSU 2026")
