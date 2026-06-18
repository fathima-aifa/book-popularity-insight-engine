# 📚 Book Popularity Insight Engine

## Project Overview

The **Book Popularity Insight Engine** is a Machine Learning and Generative AI-based web application that predicts the **popularity of books** using structured metadata and unstructured text descriptions.

The system uses a trained **XGBoost Regressor model** along with **TF-IDF text vectorization** to analyze book features such as genre, page count, publication year, and description. It then predicts a **popularity score** and categorizes books into different engagement levels.

In addition to prediction, the project integrates **Google Gemini (GenAI)** to generate intelligent recommendations for improving book reach, engagement, and marketing strategy.

---

##  Key Features

-  Predict book popularity using Machine Learning
-  Feature engineering with **TF-IDF text processing**
-  Multi-label genre encoding
-  AI-powered marketing and engagement suggestions (Gemini API)
-  Flask-based interactive web application
-  Model comparison (Linear Regression, Random Forest, XGBoost)

---

##  Project Structure

```text
book-popularity-insight-engine/
│
├── app/
│   ├── app.py
│   │   Main Flask backend that handles prediction and GenAI responses
│   ├── templates/
│   │   index.html → Frontend UI for user interaction
│   ├── static/
│   │   CSS and image assets for UI styling
│
├── models/
│   ├── xgboost_model.pkl → Final trained ML model
│   ├── tfidf_vectorizer.pkl → Text vectorizer for book descriptions
│   ├── feature_columns.pkl → Feature alignment for prediction
│
├── notebook/
│   ├── 01_eda.ipynb → Exploratory Data Analysis
│   ├── 02_preprocessing.ipynb → Data cleaning & feature engineering
│   ├── model_development.ipynb → Model training & evaluation
│
├── data_scrape.py → Script used for web scraping book dataset
├── .gitignore → Files excluded from Git tracking
├── README.md → Project documentation
