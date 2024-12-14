from flask import Flask, render_template, request, redirect, url_for, session
from authlib.integrations.flask_client import OAuth
import pickle

# import numpy as np

# Initialize the Flask app
app = Flask(__name__)
app.secret_key = 'random_secret'

# Google OAuth configuration
oauth = OAuth(app)



google = oauth.register(
    name='google',

    client_id='700483157373-b2t0diu3ti8ob71q5rdq5o4krknapiid.apps.googleusercontent.com',
    client_secret='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',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    client_kwargs={
        'scope': 'openid email profile',
    },
)

# Load the saved model and scaler
with open('model.pkl', 'rb') as model_file:
    model = pickle.load(model_file)

with open('scaler.pkl', 'rb') as scaler_file:
    scaler = pickle.load(scaler_file)

@app.route('/')
def index():
    email = session.get('email', None)
    profile_image = session.get('profile_image', None)
    user = session.get('user_name')

    if email:
        return render_template('profile.html', user=user, profile_image=profile_image)
    else:

        return render_template('login.html')

@app.route('/login')
def login():
    google = oauth.create_client('google')
    redirect_url = url_for('authorize', _external=True)
    return google.authorize_redirect(redirect_url)

@app.route('/authorize')
def authorize():
    try:
        google = oauth.create_client('google')
        token = google.authorize_access_token()
        resp = google.get('userinfo')
        user_info = resp.json()

        if not user_info or 'email' not in user_info:
            return "Failed to fetch user info", 400

        session['email'] = user_info['email']
        session['profile_image'] = user_info.get('picture', None)
        session['user_name'] = user_info.get('name', None)

        return redirect('/')
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/logout')
def logout():
    for key in list(session.keys()):
        session.pop(key)
    return redirect('/')

@app.route('/diabetes')
def diabetes():
    if 'email' not in session:
        return redirect('/')
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    if 'email' not in session:
        return redirect('/')
    try:
        # Get data from form
        data = [
            float(request.form['Pregnancies']),
            float(request.form['Glucose']),
            float(request.form['BloodPressure']),
            float(request.form['SkinThickness']),
            float(request.form['Insulin']),
            float(request.form['BMI']),
            float(request.form['DiabetesPedigreeFunction']),
            float(request.form['Age'])
        ]

        # Standardize the input data
        data = scaler.transform([data])

        # Make prediction
        prediction = model.predict(data)

        # Return the result
        if prediction[0] == 1:
            result = "The model predicts that the patient has diabetes."
        else:
            result = "The model predicts that the patient does not have diabetes."
  
        return render_template('index.html', prediction=result)
    except Exception as e:
        return render_template('index.html', prediction=f"Error: {str(e)}")

if __name__ == '__main__':
    app.run(debug=True)
