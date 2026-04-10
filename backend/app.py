from flask import Flask, request, jsonify
from services.employee_data import search_employees, validate_employee

app = Flask(__name__)

@app.route("/api/employees/search")
def search():
    name = request.args.get("name", "")
    try:
        result = search_employees(name)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/employees/validate", methods=["POST"])
def validate():
    data = request.json
    emp_id = data.get("employee_id")
    emp_name = data.get("employee_name")
    if validate_employee(emp_id, emp_name):
        return jsonify({"valid": True})
    return jsonify({"valid": False}), 400

if __name__ == "__main__":
    app.run(debug=True)
