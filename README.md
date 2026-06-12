# AI Study Buddy

A complete, feature-rich, interactive learning dashboard built with **Streamlit** and powered by the **Google Gemini 1.5 Flash API**. AI Study Buddy helps students understand complex academic concepts, summarize lecture slide/PDF notes, generate interactive practice quizzes, practice with dynamic flashcards, and chat with a specialized AI tutor.

---

##  Features

# 1.  Main Dashboard :
   - Track academic analytics: study streak, active learning time, total AI sessions, and average quiz scores.
   - Interactive bar chart showing study activity patterns.
   - Personalized learning recommendations based on recently studied topics.

2. # Concept Explainer :
   - User inputs any query or concept (e.g. *Photosynthesis*, *QuickSort*).
   - Generates simple explanations (with real-world analogies), deep technical details, key takeaways, and interview prep questions.
   - Saves queries to study history.
   - Single-click downloads to plain text (`.txt`) or formatted PDF (`.pdf`).

3. # Notes Summarizer :
   - Supports pasting long notes or uploading a PDF chapter directly.
   - Outputs a concise executive summary, key vocabulary concepts, exam-focus points, and a checkable revision list.
   - Exports the summary sheet.

4. # Interactive Quiz Generator :
   - Instantly generates 10 MCQs based on a topic and chosen difficulty (Beginner, Intermediate, Advanced).
   - Interactive grading interface: submit your answers, see correct/incorrect feedback (green/red), review correct answers, and read thorough rationale explanations.
   - Automatically saves score progress to the analytics dashboard.

5. # Flashcard Generator :
   - Generates a customized deck of study flashcards.
   - Features a styled CSS card panel showing the concept (Front) with a "Flip Card" trigger to reveal the answer/definition (Back).
   - Horizontal pagination buttons to cycle through the deck.

6. # Study Assistant Chat :
   - Multi-turn conversation assistant to answer follow-up queries.
   - Save or clear chat conversations.

---

##  Project Structure

```
AI_Study_Buddy/
│
├── app.py                     # Main dashboard page and entry point
├── requirements.txt           # Project package dependencies
├── .env                       # Environment variables config
├── README.md                  # Project documentation
│
├── pages/                     # Streamlit multi-page module
│   ├── explain.py             # Concept Explainer page
│   ├── summarize.py           # Notes Summarizer page
│   ├── quiz.py                # Interactive MCQ Quizzes page
│   ├── flashcards.py          # Study Flashcard deck page
│   └── chat.py                # Tutor Chat page
│
├── utils/                     # Utility layer
│   ├── database.py            # SQLite helper for history, streaks, and learning duration
│   ├── gemini_helper.py       # Gemini 1.5 Flash client configurations & prompt templates
│   ├── pdf_reader.py          # PDF text extraction (via pypdf)
│   ├── ui_helper.py           # Common CSS, sidebar, and time-tracking routines
│   └── export_helper.py       # Export formatting routines (TXT & ReportLab PDF)
│
└── database/
    └── study_history.db       # Created automatically on startup
```

---

##  Setup Instructions

### 1. Prerequisites
Ensure you have **Python 3.9** or higher installed.

### 2. Clone/Copy Project and Navigate
Make sure all files are in a dedicated directory:
```bash
cd AI_Study_Buddy
```

### 3. Install Dependencies
It is highly recommended to use a virtual environment:
```bash
# Create virtual environment
python -m venv venv

# Activate on Windows (cmd/powershell):
.\venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### 4. Configure Gemini API Key
Create a `.env` file at the root level and add your Gemini API Key:
```env
GEMINI_API_KEY=your_google_gemini_api_key_here
```
> **Note**: You can also enter or override your Gemini API key in the sidebar text input field when running the application.

### 5. Launch the Application
Run the Streamlit server from your terminal:
```bash
streamlit run app.py
```
This command will launch the development server and print the local URL (usually `http://localhost:8501`) in the shell. Open it in a web browser.
