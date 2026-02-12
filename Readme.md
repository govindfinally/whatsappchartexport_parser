🟢 WhatsApp Chat Export Parser & Analyzer

A web-based app that parses and visualizes WhatsApp chat exports using Streamlit.
Upload your exported .txt chat file, and instantly see detailed stats, message patterns, and interactive visualizations.

🔗 Live Demo:[ https://govindfinally-whatsappchartexport-parser-app-hrccpc.streamlit.app/](https://govindfinally-whatsappchartexport-parser-app-hrccpc.streamlit.app/)

🚀 Features

📂 Upload your WhatsApp chat export (.txt) file (without media)

🔍 Automatic parsing of messages (date, time, sender, and text)

📊 Stats on total messages, words, media, and links shared

👥 Top contributors and user-wise activity

⏰ Message frequency by date, month, weekday, and hour

🔤 Word and emoji usage analysis

🎨 Clean Streamlit UI for smooth interaction

🧰 Getting Started
1️⃣ Prerequisites

Python 3.x

Required libraries (listed in requirements.txt):
streamlit, pandas, matplotlib, seaborn, emoji, etc.

2️⃣ Local Setup
# Clone the repository
git clone https://github.com/<your-username>/whatsapp-chat-parser.git
cd whatsapp-chat-parser

# Install dependencies
pip install -r requirements.txt

# Run the Streamlit app
streamlit run app.py


Then open your browser at:
👉 http://localhost:8501/

📂 File Structure
📁 whatsapp-chat-parser/
├── app.py                # Main Streamlit script
├── preprocessor.py       # Functions to parse raw chat text into structured DataFrame
├── helper.py             # Utility functions for metrics, analysis, and plots
├── requirements.txt      # Python dependencies
└── README.md             # Project documentation

🧮 How It Works

Export your WhatsApp chat from your phone (without media).

On Android: Menu → More → Export Chat → Without Media

On iPhone: Swipe left on chat → More → Export Chat → Without Media

Upload the exported .txt file to the app.

The backend parses timestamps, user names, and messages.

Data is stored in a structured DataFrame for analysis.

Charts and statistics are generated dynamically — all within the browser.

📊 Example Insights

Total messages and words sent

Active hours and weekdays

Message timeline (by month or user)

Most active users

Wordcloud and emoji usage

Link and media sharing count

🛠️ Future Enhancements

🧠 Sentiment analysis of messages

🌍 Multilingual chat parsing (Hindi, Bengali, etc.)

📅 Predictive analytics for future activity trends

⬇️ Export processed data to CSV or Excel

📈 Add Plotly charts for more interactivity

⚠️ Limitations

Parsing accuracy depends on WhatsApp’s export format (locale/date format variations).

Some system messages (“User added”, “Group icon changed”) may be ignored.

Very large chats may take extra time to process.

📜 License
MIT License  
Copyright (c) 2025 Govind Mohanty

📬 Contact

For feedback, issues, or collaboration:
Govind Mohanty
🌐 Live App: [https://govindfinally-whatsappchartexport-parser-app-hrccpc.streamlit.app/](https://govindfinally-whatsappchartexport-parser-app-hrccpc.streamlit.app/)

📧 Email: (govindmohanty4@gmail.com)

