import os
import joblib
import pandas as pd
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from google import genai
from nltk.stem import WordNetLemmatizer


lemmatizer = WordNetLemmatizer()

def lemmatize_text(text):
    tokens = text.lower().split()
    return [
        lemmatizer.lemmatize(word)
        for word in tokens
        if word.isalpha()
    ]




# Load secret environment variables (.env)
load_dotenv()

app = Flask(__name__)

# Initialize  Client securely
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Load your trained ML Artifacts safely

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(BASE_DIR, "models")

model = joblib.load(os.path.join(MODEL_DIR, "xgboost_model.pkl"))
tfidf = joblib.load(os.path.join(MODEL_DIR, "tfidf_vectorizer.pkl"))
expected_features = joblib.load(os.path.join(MODEL_DIR, "feature_columns.pkl"))

SELECTED_GENRES = [
    "fiction", "fantasy", "romance", "young adult", "historical fiction",
    "nonfiction", "mystery", "paranormal", "science fiction", "thriller", 
    "horror", "biography"
]

@app.route("/", methods=["GET"])
def index():
    # Renders the initial frontend screen
    return render_template("index.html")

@app.route("/predict", methods=["POST"])
def predict():
    try:
        # 1. Capture incoming JSON data package from Javascript front-end
        data = request.get_json()
        
        genres_input = data.get("genres", []) # List of strings chosen by the user
        page_count = float(data.get("page_count", 0))
        pub_year = float(data.get("pub_year", 2026))
        description = data.get("description", "")

        if page_count <= 0:
            return jsonify({
                "success": False,
                "error": "Page Count must be greater than zero."
                })
        if pub_year < 1500 or pub_year > 2100:
            return jsonify({
                "success": False,
                "error": "Publication Year must be between 1000 and 2100.."
                })

        if not description.strip():
            return jsonify({
                "success": False,
                "error": "Description cannot be empty."
                })

        if len(genres_input) == 0:
            return jsonify({
               "success": False,
               "error": "Please select at least one genre."
    })
        
        # 2. Build a single-row DataFrame matching training layout parameters
        input_df = pd.DataFrame([{
            'Page_Count': page_count,
            'Pub_Year': pub_year
        }])
        
        # 3. Handle Multi-Label Binarization manually for selected genre list inputs
        for g in SELECTED_GENRES:
            input_df[g] = 1 if g in [x.lower().strip() for x in genres_input] else 0
            
        # 4. Process unstructured text via your saved TF-IDF vectorizer
        tfidf_matrix = tfidf.transform([description])
        tfidf_df = pd.DataFrame(
            tfidf_matrix.toarray(), 
            columns=tfidf.get_feature_names_out(), 
            index=input_df.index
        )
        
        # Merge numerical data, structural genre columns, and text arrays together
        final_df = pd.concat([input_df, tfidf_df], axis=1)
        
        # Force column indexing arrays to match exact features expected by XGBoost
        final_df = final_df.reindex(columns=expected_features, fill_value=0)
        
        # 5. Execute ML Pipeline Prediction
        predicted_log_score = model.predict(final_df)[0]
        predicted_score = round(float(predicted_log_score), 2)
        
        # Classify the score into a readable success category
        if predicted_score > 4.5:
            category = "Bestseller Potential 🚀"
        elif predicted_score > 2.5:
            category = "Moderate Engagement 📈"
        else:
            category = "Niche / Low Reach 📉"

        # 6. Prompt Engineering Strategy Optimization Pipeline
        genai_prompt = f"""
        You are an experienced publishing consultant and book marketing strategist.
    
        Book Details:

        Genres:{', '.join(genres_input)}

        Page Count:{page_count}

        Publication Year:{pub_year}

        Predicted Popularity Score:{predicted_score}

        Prediction Category:{category}

        Book Description:{description}

        Provide:

        1. Why the predicted popularity may be at this level.
        2. Three reader engagement suggestions.
        3. Three marketing recommendations.
        4. Three reach improvement strategies.

        Keep the response practical, concise and specific to this book.
        """
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",  
            contents=f"""You are a professional publishing operations strategist.
                    {genai_prompt} """
                ) 
        strategies = response.text

        # 7. Return structural metrics as JSON back to the awaiting web interface
        return jsonify({
            "success": True,
            "score": predicted_score,
            "category": category,
            "strategies": strategies
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

if __name__ == "__main__":
    app.run(debug=True)