# MathMentor AI 📐

An AI-powered math tutor that generates step-by-step solutions and automatic function visualizations. Built for HackPSU Nittany AI Challenge.

## ✨ Features

- **Step-by-step solutions** — Clear, detailed explanations for algebra, calculus, and trigonometry problems
- **Hint Mode** — Toggle between full solutions and guiding hints only (no answer reveal)
- **Automatic function plotting** — Instantly visualizes functions with Matplotlib
- **Beautiful LaTeX rendering** — Clean math formulas displayed natively
- **Subject selection** — Switch between Calculus, Algebra, Trigonometry, and General Math

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- OpenAI API key ([get one here](https://platform.openai.com/api-keys))

### Installation

1. Clone this repository:
```bash
git clone <your-repo-url>
cd mathmentor-ai
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file:
```bash
cp .env.example .env
```

4. Add your OpenAI API key to `.env`:
```
OPENAI_API_KEY=sk-your-key-here
```

5. Run the app:
```bash
streamlit run main.py
```

The app will open in your browser at `http://localhost:8501`.

## 🛠️ Tech Stack

- **Frontend**: Streamlit
- **AI**: OpenAI GPT-4o Mini
- **Visualization**: Matplotlib
- **Language**: Python

## 🎯 Why MathMentor AI?

Generic chatbots like ChatGPT are powerful but unfocused for math learning. They:
- Skip steps or give answers too quickly
- Don't visualize functions automatically
- Have messy interfaces filled with unrelated content

MathMentor AI is a **dedicated math learning tool** that:
- Enforces step-by-step teaching logic
- Integrates text solutions + function graphs in one place
- Includes a Hint Mode to prevent students from just copying answers
- Removes all distractions, focusing solely on math learning

## 📈 Future Improvements

- Upload handwritten problems via OCR
- Save problem history and personalized error tracking
- Export solutions as PDF
- Support for multi-variable calculus and linear algebra
- Collaborative study mode

## 🏆 HackPSU

Built for the **Nittany AI Challenge** track at HackPSU Fall 2026.
