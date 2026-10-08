from flask import Flask, render_template, request, jsonify
import database

app = Flask(__name__)
database.init_db()

def evaluate_rules(data):
    amount = data['amount']
    frequency = data['frequency']
    country = data['country'].strip().casefold()
    login_country = data['login_country'].strip().casefold()
    account_age = data['account_age']
    reasons = []

    if frequency > 5:
        reasons.append('More than 5 transactions in 1 minute')
    if country != login_country:
        reasons.append('Login country differs from transaction country')
    if amount > 50000:
        reasons.append('Transaction amount exceeds ₹50,000 threshold')
    if account_age < 7 and amount > 20000:
        reasons.append('High amount transaction on an account younger than 7 days')

    fraud_rules = {'More than 5 transactions in 1 minute',
                   'High amount transaction on an account younger than 7 days'}
    if any(reason in fraud_rules for reason in reasons):
        return 'Fraud', '; '.join(reasons)
    if reasons:
        return 'Suspicious', '; '.join(reasons)
    return 'Safe', 'Transaction passed all configured rule checks'

def validate_payload(payload):
    if not isinstance(payload, dict):
        raise ValueError('JSON request body is required.')
    try:
        clean = {
            'amount': float(payload.get('amount')),
            'frequency': int(payload.get('frequency')),
            'country': str(payload.get('country', '')).strip(),
            'login_country': str(payload.get('login_country', '')).strip(),
            'tx_time': str(payload.get('tx_time', '')).strip(),
            'account_age': int(payload.get('account_age')),
        }
    except (TypeError, ValueError):
        raise ValueError('Amount, frequency and account age must be valid numbers.')
    if clean['amount'] < 0 or clean['frequency'] < 0 or clean['account_age'] < 0:
        raise ValueError('Amount, frequency and account age cannot be negative.')
    if not clean['country'] or not clean['login_country'] or not clean['tx_time']:
        raise ValueError('Country, login country and transaction time are required.')
    return clean

@app.get('/')
def home():
    return render_template('index.html')

@app.post('/api/check-transaction')
def check_transaction():
    try:
        data = validate_payload(request.get_json(silent=True))
    except ValueError as error:
        return jsonify({'status': 'error', 'message': str(error)}), 400
    risk_level, reason = evaluate_rules(data)
    tx_id = database.save_transaction(data, risk_level, reason)
    return jsonify({'status': 'success', 'tx_id': tx_id, 'risk_level': risk_level, 'reason': reason})

@app.get('/api/dashboard')
def dashboard():
    return jsonify(database.get_dashboard_stats())

@app.get('/api/history')
def history():
    return jsonify(database.get_all_transactions())

@app.get('/api/analytics')
def analytics():
    return jsonify(database.get_analytics_data())

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
