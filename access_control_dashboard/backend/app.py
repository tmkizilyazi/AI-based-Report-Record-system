from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
from database import (
    analyze_access_logs,
    get_door_statistics,
    get_user_statistics,
    get_hourly_statistics,
    get_access_logs,
    get_database_schema,
    test_db_connection,
    chat_with_database,
    execute_generated_sql
)
from config import API_HOST, API_PORT, DEBUG, ALLOWED_ORIGINS

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": ALLOWED_ORIGINS}})

@app.route('/')
def home():
    return "MCP Erişim Kontrol Paneli API"

@app.route('/api/chat', methods=['GET', 'POST'])
def chat():
    try:
        if request.method == 'POST':
            data = request.json
            if not data or 'message' not in data:
                return jsonify({'error': 'Mesaj parametresi gerekli'}), 400
            
            message = data['message']
        else:  # GET metodu
            message = request.args.get('message', '')
            if not message:
                return jsonify({'error': 'Mesaj parametresi gerekli'}), 400
        
        response = chat_with_database(message)
        return jsonify({'response': response})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/access-logs', methods=['GET'])
def access_logs():
    """Erişim kayıtlarını getirir"""
    try:
        logs = get_access_logs()
        return jsonify(logs)
    except Exception as e:
        print(f"Access logs hatası: {str(e)}")
        return jsonify([]), 200

@app.route('/api/door-statistics', methods=['GET'])
def door_statistics():
    """Kapı istatistiklerini getirir"""
    try:
        stats = get_door_statistics()
        return jsonify(stats)
    except Exception as e:
        print(f"Door statistics hatası: {str(e)}")
        return jsonify([]), 200

@app.route('/api/user-statistics', methods=['GET'])
def user_statistics():
    """Kullanıcı istatistiklerini getirir"""
    try:
        stats = get_user_statistics()
        return jsonify(stats)
    except Exception as e:
        print(f"User statistics hatası: {str(e)}")
        return jsonify([]), 200

@app.route('/api/hourly-statistics', methods=['GET'])
def hourly_statistics():
    """Saatlik istatistikleri getirir"""
    try:
        stats = get_hourly_statistics()
        return jsonify(stats)
    except Exception as e:
        print(f"Hourly statistics hatası: {str(e)}")
        return jsonify([]), 200

@app.route('/api/schema', methods=['GET'])
def get_schema():
    """Veritabanı şemasını getirir"""
    try:
        schema = get_database_schema()
        return jsonify(schema)
    except Exception as e:
        print(f"Schema hatası: {str(e)}")
        return jsonify({'tables': {}, 'relationships': []}), 200

@app.route('/api/test-connection', methods=['GET'])
def test_connection():
    """Veritabanı bağlantısını test eder"""
    try:
        result = test_db_connection()
        return jsonify({'message': result})
    except Exception as e:
        print(f"Test connection hatası: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/execute-sql', methods=['POST'])
def execute_sql():
    try:
        data = request.json
        if not data or 'question' not in data:
            return jsonify({'error': 'Soru parametresi gerekli'}), 400
        
        question = data['question']
        result = execute_generated_sql(question)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host=API_HOST, port=API_PORT, debug=DEBUG) 