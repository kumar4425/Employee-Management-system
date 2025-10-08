from flask import Flask, render_template, request, redirect, url_for, flash
from db.operations import (
    init_db,
    get_all_employees,
    get_all_departments,
    add_employee,
    search_employees_by_name,
    update_employee,
    delete_employee,
    add_department,
    delete_department,
    get_employee_by_id
)

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'

init_db()

# ====== EMPLOYEE ROUTES ======
@app.route('/')
def index():
    search_query = request.args.get('search', '').strip()
    if search_query:
        employees = search_employees_by_name(search_query)
        flash(f"Found {len(employees)} employee(s) for '{search_query}'", "info")
    else:
        employees = get_all_employees()
    return render_template('index.html', employees=employees, search_query=search_query)

@app.route('/employee/add', methods=['GET', 'POST'])
def add_employee_route():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        dept_id = request.form.get('department_id')
        salary = request.form.get('salary', '0').strip()

        if not name or not email:
            flash("Name and email are required!", "error")
            return redirect(url_for('add_employee_route'))

        try:
            dept_id = int(dept_id) if dept_id else None
            salary = float(salary) if salary else 0.00
            add_employee(name, email, dept_id, salary)
            flash(f"✅ Employee '{name}' added successfully!", "success")
            return redirect(url_for('index'))
        except ValueError as e:
            flash(f"❌ {e}", "error")
            return redirect(url_for('add_employee_route'))

    departments = get_all_departments()
    return render_template('add_employee.html', departments=departments)

@app.route('/employee/edit/<int:emp_id>', methods=['GET', 'POST'])
def edit_employee(emp_id):
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        dept_id = request.form.get('department_id')
        salary = request.form.get('salary', '0').strip()

        if not name or not email:
            flash("Name and email are required!", "error")
            return redirect(url_for('edit_employee', emp_id=emp_id))

        try:
            dept_id = int(dept_id) if dept_id else None
            salary = float(salary) if salary else 0.00
            if update_employee(emp_id, name=name, email=email, dept_id=dept_id, salary=salary):
                flash("✅ Employee updated successfully!", "success")
            else:
                flash("❌ Employee not found.", "error")
            return redirect(url_for('index'))
        except ValueError as e:
            flash(f"❌ {e}", "error")
            return redirect(url_for('edit_employee', emp_id=emp_id))

    # GET: load current data
    employee = get_employee_by_id(emp_id)
    if not employee:
        flash("❌ Employee not found.", "error")
        return redirect(url_for('index'))
    
    departments = get_all_departments()
    return render_template('edit_employee.html', employee=employee, departments=departments)

@app.route('/employee/delete/<int:emp_id>')
def delete_employee_route(emp_id):
    if delete_employee(emp_id):
        flash("✅ Employee deleted successfully!", "success")
    else:
        flash("❌ Employee not found.", "error")
    return redirect(url_for('index'))

# ====== DEPARTMENT ROUTES ======
@app.route('/departments')
def department_list():
    departments = get_all_departments()
    return render_template('departments.html', departments=departments)

@app.route('/department/add', methods=['POST'])
def add_department_route():
    name = request.form.get('name', '').strip()
    if name:
        try:
            add_department(name)
            flash(f"✅ Department '{name}' added!", "success")
        except ValueError as e:
            flash(f"❌ {e}", "error")
    else:
        flash("❌ Department name cannot be empty.", "error")
    return redirect(url_for('department_list'))

@app.route('/department/delete/<int:dept_id>')
def delete_department_route(dept_id):
    try:
        if delete_department(dept_id):
            flash("✅ Department deleted successfully!", "success")
        else:
            flash("❌ Department not found.", "error")
    except ValueError as e:
        flash(f"❌ {e}", "error")
    return redirect(url_for('department_list'))

if __name__ == '__main__':
    app.run(debug=True)