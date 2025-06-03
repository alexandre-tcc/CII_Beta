from flask import Flask, render_template, request, redirect
import base64

#bundle import
from CII import gpt
from CII import graph
from CII import da
from CII import fmp
from CII import CII

app = Flask(__name__)

# Load your logo image as base64
with open("static/logo.png", "rb") as img_file:
    encoded_image = base64.b64encode(img_file.read()).decode()

@app.route('/')
def home_redirect():
    return redirect('/sign-in')

@app.route('/sign-in', methods=['GET', 'POST'])
def sign_in():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # For now, accept any credentials
        return redirect('/home')
    return render_template('login.html', encoded_image=encoded_image, username='', password='', login_failed=False)

@app.route('/403')
def forbidden():
    return render_template('403.html', encoded_image=encoded_image)

@app.route('/home')
def home_page():
    return render_template('home.html', encoded_image=encoded_image)


@app.route('/CII')
def cii_page():
    return render_template('cii.html', encoded_image=encoded_image)

@app.route('/impact_analysis')
def impact_analysis():
    return render_template('impact_analysis/impact_analysis.html', encoded_image=encoded_image)

@app.route('/impact_analysis/ticker', methods=['GET', 'POST'])
def ticker_input():
    if request.method == 'POST':
        ticker = request.form.get('ticker')
        if CII.ticker_test(ticker):
            return redirect(f"/Dashboard?ticker={ticker}")
        else:
            return render_template('ticker.html', error="Can't run analysis on this ticker.")
    return render_template('ticker.html', encoded_image=encoded_image)

@app.route('/impact_analysis/manual')
def impact_analysis_manual():
    return render_template('impact_analysis/manual.html', encoded_image=encoded_image)

if __name__ == '__main__':
    app.run(debug=True)