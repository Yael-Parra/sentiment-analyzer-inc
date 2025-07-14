<p align="center">
  <img src="img/logo.png" alt="YouTube Comments Sentiment and Toxicity Analyzer Logo" width="200"/>
</p>

<h1 align="center">YouTube Comments Sentiment and Toxicity Analyzer</h1>

<p align="center">
  Emotional Intelligence for Creators • Dockerized & Azure Deployed • FastAPI + React + Supabase
</p>

---

## 🧭 Table of Contents

- [📌 Project Overview](#-project-overview)
- [🎯 Target Audience](#-target-audience)
- [⚙️ Features & Limitations](#️-features--limitations)
- [🚀 Future Improvements](#-future-improvements)
- [🛠️ Tools & Technologies](#-tools--technologies)
- [🧪 Model Architecture](#-model-architecture)
- [📁 Project Structure](#-project-structure)
- [✍ Deployment Instructions](#-deployment-instructions)
- [👩‍💻 Contributors](#-contributors)

---

## 📌 Project Overview

<p align="justify">
  
**YouTube Comments Sentiment Analyzer** is a full-stack application that allows creators to **analyze the emotional sentiment and 12 types of toxicities** on their YouTube videos.  
Whether you're a seasoned content creator or an aspiring YouTuber, this tool provides a **dashboard-friendly interface** to help you interpret your audience's emotional response and adjust your content strategy accordingly.
</p>

The platform supports:
- Automatic fetching and processing of YouTube video comments
- Sentiment scoring using **pre-trained VADER models** and custom-trained models with **spaCy**
- Fully dockerized backend/frontend stack, **deployed via Azure**

---

## 🎯 Target Audience

- **YouTubers** seeking feedback at scale
- **Content creators** who want to adapt based on emotional trends
- **Marketers or analysts** working with YouTube channel data

> ❗ Note: The tool only supports **video comments** — Shorts, Live chat, or Community posts are not yet supported.

---

## ⚙️ Features & Limitations

### ✅ Features

- Fetch YouTube comments with ease
- Analyze sentiment (positive / neutral / negative)
- Access emotion trends in an intuitive UI
- Fully dockerized and Azure-compatible

### ⚠️ Limitations

- Only supports comments from **videos**, not **Shorts** or **Livestreams**
- Results are based on available public comments
- Sentiment detection may not fully capture sarcasm, slang, or complex irony

---

## 🚀 Future Improvements

- Expand dataset to **retrain models** with better generalization
- Improve **dashboard UX** and visual customization
- Add **multi-language support**
- Integrate **YouTube Shorts & Live Chat analysis** (in progress...)

---

## 🛠️ Tools & Technologies

### ⚙️ Backend

![FastAPI](https://img.shields.io/badge/-FastAPI-009688?logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/-Python-3776AB?logo=python&logoColor=white)
![Dill](https://img.shields.io/badge/-Dill-6E4C1E)
![TQDM](https://img.shields.io/badge/-TQDM-92C63D)
![spaCy](https://img.shields.io/badge/-spaCy-09A3D5)

### 🧠 Sentiment Modeling

![VADER](https://img.shields.io/badge/-VADER-6A1B9A)
![spaCy](https://img.shields.io/badge/-spaCy-09A3D5)

- Pre-trained models (VADER) for general sentiment polarity
- Custom-trained classifier using **spaCy**, **Dill**, and **TQDM**

### 🌐 Frontend

![React](https://img.shields.io/badge/-React-61DAFB?logo=react&logoColor=black)
![TailwindCSS](https://img.shields.io/badge/-TailwindCSS-06B6D4?logo=tailwindcss&logoColor=white)
![Vite](https://img.shields.io/badge/-Vite-646CFF?logo=vite&logoColor=white)

### 🧱 Database & Infra

![Supabase](https://img.shields.io/badge/-Supabase-3ECF8E?logo=supabase&logoColor=white)
![Docker](https://img.shields.io/badge/-Docker-2496ED?logo=docker&logoColor=white)
![Azure](https://img.shields.io/badge/-Azure-0078D4?logo=microsoftazure&logoColor=white)

---

## 🧪 Model Architecture

- **Data Ingestion**: YouTube API
- **Sentiment Processing**:  
  - Rule-based with **VADER**  
  - Supervised learning with **spaCy** + manual annotation
- **Storage**: Supabase
- **Frontend UI**: React + Tailwind + Chart libraries
- **Containerization**: Docker (multi-service with docker-compose)
- **Deployment**: Hosted on Azure via container services

---

## 📁 Project Structure


---

## ✍ Deployment Instructions

1. Run it in your PC with a virtual environment:
  1. Clone the repository
     ```
     git clone https://github.com/your-repo/youtube-sentiment-analyzer.git
     cd youtube-sentiment-analyzer
      ```
  2. Set up your .env file based on .env.example
  3. You need to have java installed in your PC and ...   
  4. To run in the terminal:
       You need to open 2 terminal windows.
         - In the first terminal, go to the root of the project and run:
         ```
         uvicorn server.main:app --reload
         ```
         - In the second terminal go to client then run:
         ```
         cd client
         npm run dev
         ```

2. Run it with Docker:
  1. Build and run the application
  ```
  docker-compose up --build
  ```
3. Try it in our website:
  1. Visit:
     ```
     www.
     ```

---
## 👩‍💻 Contributors
We are a diverse team passionate about emotional analytics, content strategy, and real-time data apps.
Feel free to explore, fork, or connect with us for ideas, feedback, or collaborations.


| Name | GitHub | LinkedIn |
|------|--------|----------|
| **Pepe Ruiz** | [![GitHub](https://img.shields.io/badge/GitHub-c4302b?logo=github&logoColor=white)](https://github.com/peperuizdev) | [![LinkedIn](https://img.shields.io/badge/LinkedIn-0A66C2?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/peperuiznieto/) |
| **Nhoeli Salazar** | [![GitHub](https://img.shields.io/badge/GitHub-c4302b?logo=github&logoColor=white)](https://github.com/Nho89) | [![LinkedIn](https://img.shields.io/badge/LinkedIn-0A66C2?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/nhoeli-salazar/) |
| **Andreina Suescum** | [![GitHub](https://img.shields.io/badge/GitHub-c4302b?logo=github&logoColor=white)](https://github.com/mariasuescum) | [![LinkedIn](https://img.shields.io/badge/LinkedIn-0A66C2?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/andreina-suescum/) |
| **Yael Parra** | [![GitHub](https://img.shields.io/badge/GitHub-c4302b?logo=github&logoColor=white)](https://github.com/Yael-Parra) | [![LinkedIn](https://img.shields.io/badge/LinkedIn-0A66C2?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/yael-parra/) |
| **Maryna Nalyvaiko** | [![GitHub](https://img.shields.io/badge/GitHub-c4302b?logo=github&logoColor=white)](https://github.com/MarynaDRST) | [![LinkedIn](https://img.shields.io/badge/LinkedIn-0A66C2?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/maryna-nalyvaiko-69745a236/) |


