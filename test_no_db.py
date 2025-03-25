from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/api/test', methods=['POST'])
def test_api():
    """测试API，不依赖数据库"""
    data = request.get_json()
    return jsonify({
        'status': 'success',
        'message': '测试成功',
        'data': data
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True) 