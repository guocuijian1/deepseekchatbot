# User Guide for the Project

## Overview
This project is a chatbot application that integrates with a vector database and uses language models to process and respond to user queries. It includes the following components:
- **Backend Services**: Python-based services for vector database management and chatbot logic.
- **Frontend**: A web-based user interface for interacting with the chatbot.
- **Data Management**: Handles embedding and querying of data from Excel files and markdown documents.

---

## Prerequisites
1. **Python**: Ensure Python 3.8+ is installed.
2. **Node.js**: Required for frontend development (if applicable).
3. **Dependencies**: Install required Python packages using `pip install -r requirements.txt`.
4. **Environment Variables**:
    - `OPENAI_API_KEY`: API key for OpenAI integration.

---

## Project Structure
- `octane_service.py`: Handles vector database operations and Excel data embedding.
- `chat_service.py`: Manages chatbot logic and user interaction.
- `templates/index.html`: Frontend HTML template for the chatbot UI.
- `static/`: Contains CSS and JavaScript files for the frontend.

---

## Setup Instructions

### Backend
1. Clone the repository:
   ```bash
   git clone git@github.com:guocuijian1/deepseekchatbot.git
2. Enter project folder:   
   cd deepseekchatbot
3. Install dependencies:
   pip install -r requirements.txt
4. Run web server:
   flask run
5. Access the chatbot UI:
   Open a web browser and navigate to `http://localhost:5000`
   