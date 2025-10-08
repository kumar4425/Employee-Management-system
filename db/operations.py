import psycopg2
from .config import DB_CONFIG
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_connection():
    """Create a new database connection."""
    return psycopg2.connect(**DB_CONFIG)

# ====== Initialize Database Schema ======
def init_db():
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS departments (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(100) UNIQUE NOT NULL
                    );
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS employees (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        email VARCHAR(100) UNIQUE NOT NULL,
                        department_id INTEGER REFERENCES departments(id) ON DELETE SET NULL,
                        salary DECIMAL(10, 2) DEFAULT 0.00
                    );
                """)
                conn.commit()
        logger.info("✅ Database schema initialized.")
    except Exception as e:
        logger.error("❌ Failed to initialize DB: %s", e)
        raise

# ====== Department Operations ======
def add_department(name):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO departments (name) VALUES (%s);", (name,))
                conn.commit()
        logger.info("✅ Department added: %s", name)
    except psycopg2.IntegrityError:
        raise ValueError("Department name must be unique!")
    except Exception as e:
        logger.error("❌ Error adding department: %s", e)
        raise

def get_all_departments():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name FROM departments ORDER BY name;")
            return cur.fetchall()

def delete_department(dept_id):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM employees WHERE department_id = %s LIMIT 1;", (dept_id,))
                if cur.fetchone():
                    raise ValueError("Cannot delete: department has employees. Reassign them first.")
                cur.execute("DELETE FROM departments WHERE id = %s;", (dept_id,))
                deleted = cur.rowcount > 0
                if deleted:
                    conn.commit()
                return deleted
    except Exception as e:
        logger.error("❌ Failed to delete department: %s", e)
        raise

# ====== Employee Operations ======
def add_employee(name, email, dept_id, salary=0.00):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO employees (name, email, department_id, salary) VALUES (%s, %s, %s, %s);",
                    (name, email, dept_id, salary)
                )
                conn.commit()
        logger.info("✅ Employee added: %s", name)
    except psycopg2.IntegrityError as e:
        msg = str(e).lower()
        if "unique constraint" in msg or "duplicate key" in msg:
            raise ValueError("Email already exists!")
        elif "foreign key" in msg:
            raise ValueError("Invalid department ID!")
        else:
            raise
    except Exception as e:
        logger.error("❌ Error adding employee: %s", e)
        raise

def get_all_employees():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT e.id, e.name, e.email, d.name AS department, e.salary
                FROM employees e
                LEFT JOIN departments d ON e.department_id = d.id
                ORDER BY e.id;
            """)
            return cur.fetchall()

def search_employees_by_name(name_part):
    """Search employees by partial name match (case-insensitive)."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT e.id, e.name, e.email, d.name AS department, e.salary
                FROM employees e
                LEFT JOIN departments d ON e.department_id = d.id
                WHERE e.name ILIKE %s
                ORDER BY e.id;
            """, (f"%{name_part}%",))
            return cur.fetchall()

def update_employee(emp_id, name=None, email=None, dept_id=None, salary=None):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                fields = []
                values = []
                if name is not None:
                    fields.append("name = %s")
                    values.append(name)
                if email is not None:
                    fields.append("email = %s")
                    values.append(email)
                if dept_id is not None:
                    fields.append("department_id = %s")
                    values.append(dept_id)
                if salary is not None:
                    fields.append("salary = %s")
                    values.append(salary)
                if not fields:
                    return True  # Nothing to update
                query = f"UPDATE employees SET {', '.join(fields)} WHERE id = %s;"
                values.append(emp_id)
                cur.execute(query, values)
                updated = cur.rowcount > 0
                if updated:
                    conn.commit()
                return updated
    except psycopg2.IntegrityError as e:
        msg = str(e).lower()
        if "unique constraint" in msg or "duplicate key" in msg:
            raise ValueError("Email already exists!")
        elif "foreign key" in msg:
            raise ValueError("Invalid department ID!")
        else:
            raise
    except Exception as e:
        logger.error("❌ Failed to update employee: %s", e)
        raise

def delete_employee(emp_id):
    """Delete an employee by ID."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM employees WHERE id = %s;", (emp_id,))
                deleted = cur.rowcount > 0
                if deleted:
                    conn.commit()
                return deleted
    except Exception as e:
        logger.error("❌ Failed to delete employee: %s", e)
        raise

def get_employee_by_id(emp_id):
    """Get a single employee by ID."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT e.id, e.name, e.email, e.department_id, e.salary
                FROM employees e
                WHERE e.id = %s;
            """, (emp_id,))
            return cur.fetchone()