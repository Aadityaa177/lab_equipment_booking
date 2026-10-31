
from datetime import date
from functools import wraps

from flask import (
    Flask, render_template, request, jsonify,
    redirect, url_for, flash
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user, logout_user,
    login_required, current_user
)
from sqlalchemy import text, bindparam
from werkzeug.security import check_password_hash, generate_password_hash

from config import Config


app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'home'

DAYS = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']


# --------------------------------------------------
# USER AUTHENTICATION
# --------------------------------------------------

class User(UserMixin):
    def __init__(self, row):
        self.id = row['user_id']
        self.college_id = row['college_id']
        self.full_name = row['full_name']
        self.role = row['role']


@login_manager.user_loader
def load_user(user_id):
    row = db.session.execute(
        text("""
            SELECT user_id, college_id, full_name, role
            FROM users
            WHERE user_id = :id
        """),
        {'id': user_id}
    ).mappings().first()

    return User(row) if row else None


def roles(*allowed):
    def decorator(fn):
        @wraps(fn)
        @login_required
        def wrapper(*args, **kwargs):
            if current_user.role not in allowed:
                return jsonify(error='Forbidden for this role'), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator


@app.get('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('login.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    college_id = request.form.get('college_id', '').strip()
    password = request.form.get('password', '')

    row = db.session.execute(
        text('SELECT * FROM users WHERE college_id = :id'),
        {'id': college_id}
    ).mappings().first()

    if not row or not check_password_hash(row['password_hash'], password):
        flash('Invalid college ID or password.')
        return redirect(url_for('home'))

    login_user(User(row))
    return redirect(url_for('dashboard'))


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.get('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'ADMIN':
        return redirect(url_for('admin_users'))
    if current_user.role == 'STAFF':
        return redirect(url_for('staff_dashboard'))
    if current_user.role == 'INCHARGE':
        return redirect(url_for('incharge_dashboard'))
    return redirect(url_for('timetable'))


# --------------------------------------------------
# REGISTRATION AND ADMIN USER MANAGEMENT
# --------------------------------------------------

ROLE_DOMAINS = {
    'STUDENT': 'vitstudent.ac.in',
    'FACULTY': 'vitfaculty.ac.in',
    'STAFF': 'vitstaff.ac.in',
    'INCHARGE': 'vitstaff.ac.in',
}


def valid_institutional_email(email, role):
    email = email.strip().lower()

    if email.count('@') != 1 or role not in ROLE_DOMAINS:
        return False

    local_part, domain = email.rsplit('@', 1)

    return (
        bool(local_part)
        and len(email) <= 254
        and domain == ROLE_DOMAINS[role]
    )


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        college_id = request.form.get('college_id', '').strip()
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not college_id or not full_name or not email or not password:
            flash('Please complete all fields.')
            return render_template('register.html')

        if len(college_id) > 50 or len(full_name) > 100:
            flash('College ID or name is too long.')
            return render_template('register.html')

        if not valid_institutional_email(email, 'STUDENT'):
            flash('Use your VIT student email ending in @vitstudent.ac.in.')
            return render_template('register.html')

        if len(password) < 8:
            flash('Password must contain at least 8 characters.')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match.')
            return render_template('register.html')

        existing = db.session.execute(
            text("""
                SELECT user_id
                FROM users
                WHERE college_id = :college_id OR email = :email
            """),
            {'college_id': college_id, 'email': email}
        ).first()

        if existing:
            flash('That college ID or email is already registered.')
            return render_template('register.html')

        try:
            user_result = db.session.execute(
                text("""
                    INSERT INTO users
                        (college_id, full_name, email, password_hash, role)
                    VALUES
                        (:college_id, :full_name, :email, :password_hash, 'STUDENT')
                """),
                {
                    'college_id': college_id,
                    'full_name': full_name,
                    'email': email,
                    'password_hash': generate_password_hash(password)
                }
            )
            db.session.execute(
                text("INSERT INTO students (user_id) VALUES (:uid)"),
                {'uid': user_result.lastrowid}
            )
            db.session.commit()
            flash('Registration successful. You can now log in.')
            return redirect(url_for('home'))

        except Exception:
            db.session.rollback()
            app.logger.exception('Student registration failed')
            flash('Registration could not be completed. Please try again.')
            return render_template('register.html')

    return render_template('register.html')


@app.get('/admin/users')
@roles('ADMIN')
def admin_users():
    # Admin sees separate role-specific tables. The users table remains the
    # central source for authentication and common identity fields.
    students = db.session.execute(text("""
        SELECT u.user_id, u.college_id, u.full_name, u.email,
               s.programme, s.year_of_study, s.section
        FROM students s JOIN users u ON u.user_id = s.user_id
        WHERE u.role = 'STUDENT'
        ORDER BY u.full_name
    """)).mappings().all()

    faculty = db.session.execute(text("""
        SELECT u.user_id, u.college_id, u.full_name, u.email,
               f.department, f.designation
        FROM faculty f JOIN users u ON u.user_id = f.user_id
        WHERE u.role = 'FACULTY'
        ORDER BY u.full_name
    """)).mappings().all()

    staff = db.session.execute(text("""
        SELECT u.user_id, u.college_id, u.full_name, u.email,
               s.department, s.designation
        FROM staff s JOIN users u ON u.user_id = s.user_id
        WHERE u.role = 'STAFF'
        ORDER BY u.full_name
    """)).mappings().all()

    lab_incharges = db.session.execute(text("""
        SELECT u.user_id, u.college_id, u.full_name, u.email,
               li.department, li.designation
        FROM lab_incharges li JOIN users u ON u.user_id = li.user_id
        WHERE u.role = 'INCHARGE'
        ORDER BY u.full_name
    """)).mappings().all()

    return render_template(
        'admin_users.html', students=students, faculty=faculty,
        staff=staff, lab_incharges=lab_incharges
    )


@app.post('/admin/users/create')
@roles('ADMIN')
def admin_create_user():
    college_id = request.form.get('college_id', '').strip()
    full_name = request.form.get('full_name', '').strip()
    email = request.form.get('email', '').strip().lower()
    role = request.form.get('role', '').strip().upper()
    password = request.form.get('password', '')
    department = request.form.get('department', '').strip() or None
    designation = request.form.get('designation', '').strip() or None
    programme = request.form.get('programme', '').strip() or None
    year_raw = request.form.get('year_of_study', '').strip()
    section = request.form.get('section', '').strip() or None

    if role not in ('FACULTY', 'STAFF', 'INCHARGE'):
        flash('Choose a valid privileged account role.')
        return redirect(url_for('admin_users'))
    if not college_id or not full_name or not email or not password:
        flash('Complete all required account fields.')
        return redirect(url_for('admin_users'))
    if len(college_id) > 50 or len(full_name) > 100 or len(password) < 8:
        flash('Check the ID, name and password length (minimum 8 characters).')
        return redirect(url_for('admin_users'))
    if not valid_institutional_email(email, role):
        flash('Email domain does not match the selected role.')
        return redirect(url_for('admin_users'))
    if not department or not designation:
        flash('Enter department and designation for this role.')
        return redirect(url_for('admin_users'))

    existing = db.session.execute(
        text("SELECT user_id FROM users WHERE college_id = :college_id OR email = :email"),
        {'college_id': college_id, 'email': email}
    ).first()
    if existing:
        flash('That college ID or email is already registered.')
        return redirect(url_for('admin_users'))

    try:
        user_result = db.session.execute(
            text("""
                INSERT INTO users (college_id, full_name, email, password_hash, role)
                VALUES (:college_id, :full_name, :email, :password_hash, :role)
            """),
            {
                'college_id': college_id, 'full_name': full_name, 'email': email,
                'password_hash': generate_password_hash(password), 'role': role
            }
        )
        uid = user_result.lastrowid
        profile_table = {'FACULTY': 'faculty', 'STAFF': 'staff',
                         'INCHARGE': 'lab_incharges'}[role]
        db.session.execute(
            text(f"INSERT INTO {profile_table} (user_id, department, designation) "
                 "VALUES (:uid, :department, :designation)"),
            {'uid': uid, 'department': department, 'designation': designation}
        )
        db.session.commit()
        flash(f'{role.title()} account created successfully.')
    except Exception:
        db.session.rollback()
        app.logger.exception('Admin account creation failed')
        flash('Account could not be created. Check the server log.')

    return redirect(url_for('admin_users'))


@app.post('/admin/users/<int:user_id>/profile')
@roles('ADMIN')
def admin_update_profile(user_id):
    role_row = db.session.execute(
        text("SELECT role FROM users WHERE user_id = :uid"),
        {'uid': user_id}
    ).first()
    if not role_row:
        flash('Account not found.')
        return redirect(url_for('admin_users'))

    role = role_row[0]
    try:
        if role == 'STUDENT':
            year_raw = request.form.get('year_of_study', '').strip()
            year = int(year_raw) if year_raw else None
            if year is not None and not 1 <= year <= 8:
                raise ValueError('Year of study must be between 1 and 8.')
            db.session.execute(
                text("""UPDATE students
                        SET programme = :programme, year_of_study = :year, section = :section
                        WHERE user_id = :uid"""),
                {'programme': request.form.get('programme', '').strip() or None,
                 'year': year, 'section': request.form.get('section', '').strip() or None,
                 'uid': user_id}
            )
        elif role in ('FACULTY', 'STAFF', 'INCHARGE'):
            table = {'FACULTY': 'faculty', 'STAFF': 'staff',
                     'INCHARGE': 'lab_incharges'}[role]
            db.session.execute(
                text(f"UPDATE {table} SET department = :department, designation = :designation "
                     "WHERE user_id = :uid"),
                {'department': request.form.get('department', '').strip() or None,
                 'designation': request.form.get('designation', '').strip() or None,
                 'uid': user_id}
            )
        else:
            flash('This role does not have an editable profile here.')
            return redirect(url_for('admin_users'))
        db.session.commit()
        flash('Profile details saved.')
    except (ValueError, TypeError) as error:
        db.session.rollback()
        flash(str(error))
    except Exception:
        db.session.rollback()
        app.logger.exception('Profile update failed')
        flash('Could not save profile details.')

    return redirect(url_for('admin_users'))


# --------------------------------------------------
# TIMETABLE AND BOOKING PAGES
# --------------------------------------------------

@app.get('/timetable')
@roles('STUDENT', 'FACULTY')
def timetable():
    rows = db.session.execute(
        text("""
            SELECT slot_id, day_of_week, slot_code,
                   start_time, end_time, display_label
            FROM timetable_slots
            WHERE day_of_week IN ('MON', 'TUE', 'WED', 'THU', 'FRI')
        """)
    ).mappings().all()

    slots_by_code = {row['slot_code']: row for row in rows}

    return render_template(
        'timetable.html',
        slots_by_code=slots_by_code
    )


@app.get('/booking')
@roles('STUDENT', 'FACULTY')
def booking():
    return render_template('booking.html')


@app.get('/my-bookings')
@roles('STUDENT', 'FACULTY')
def my_bookings():
    rows = db.session.execute(
        text("""
            SELECT
                b.booking_id,
                b.booking_date,
                b.purpose,
                b.status,
                b.created_at,
                GROUP_CONCAT(
                    DISTINCT CONCAT(c.computer_code, ' (', l.lab_name, ')')
                    ORDER BY c.computer_code SEPARATOR ', '
                ) AS computers,
                GROUP_CONCAT(
                    DISTINCT ts.slot_code
                    ORDER BY ts.start_time SEPARATOR ', '
                ) AS periods
            FROM bookings b
            JOIN booking_items bi ON bi.booking_id = b.booking_id
            JOIN computers c ON c.computer_id = bi.computer_id
            JOIN labs l ON l.lab_id = c.lab_id
            JOIN timetable_slots ts ON ts.slot_id = bi.slot_id
            WHERE b.user_id = :uid
            GROUP BY
                b.booking_id, b.booking_date, b.purpose,
                b.status, b.created_at
            ORDER BY b.created_at DESC, b.booking_id DESC
        """),
        {'uid': current_user.id}
    ).mappings().all()

    return render_template('my_bookings.html', bookings=rows)


# --------------------------------------------------
# STAFF DASHBOARD
# --------------------------------------------------

@app.get('/staff')
@roles('STAFF')
def staff_dashboard():
    computers = db.session.execute(
        text("""
            SELECT c.computer_id, c.computer_code, c.health_status,
                   c.health_updated_at, l.lab_name, l.floor_number
            FROM computers c
            JOIN labs l ON l.lab_id = c.lab_id
            ORDER BY l.lab_name, c.computer_code
        """)
    ).mappings().all()

    return render_template(
        'staff_dashboard.html',
        computers=computers
    )


# --------------------------------------------------
# LAB IN-CHARGE DASHBOARD
# --------------------------------------------------

@app.get('/incharge')
@roles('INCHARGE')
def incharge_dashboard():
    labs = db.session.execute(
        text("""
            SELECT lab_id, lab_name, floor_number
            FROM labs
            WHERE incharge_user_id = :uid
            ORDER BY lab_name
        """),
        {'uid': current_user.id}
    ).mappings().all()

    computers = db.session.execute(
        text("""
            SELECT c.computer_id, c.computer_code, c.health_status,
                   c.health_updated_at, l.lab_name, l.floor_number
            FROM computers c
            JOIN labs l ON l.lab_id = c.lab_id
            WHERE l.incharge_user_id = :uid
            ORDER BY l.lab_name, c.computer_code
        """),
        {'uid': current_user.id}
    ).mappings().all()

    return render_template(
        'incharge_dashboard.html',
        labs=labs,
        computers=computers
    )


# Add a computer to a lab assigned to the logged-in in-charge.
@app.post('/incharge/computers/add')
@roles('INCHARGE')
def add_computer():
    computer_code = request.form.get('computer_code', '').strip().upper()
    lab_id = request.form.get('lab_id', '').strip()
    health_status = request.form.get('health_status', 'HEALTHY').upper()

    if not computer_code or len(computer_code) > 50:
        flash('Enter a valid computer code.')
        return redirect(url_for('incharge_dashboard'))

    if not lab_id.isdigit():
        flash('Select a valid lab.')
        return redirect(url_for('incharge_dashboard'))

    if health_status not in ('HEALTHY', 'UNHEALTHY'):
        flash('Invalid health status.')
        return redirect(url_for('incharge_dashboard'))

    assigned_lab = db.session.execute(
        text("""
            SELECT lab_id
            FROM labs
            WHERE lab_id = :lab_id AND incharge_user_id = :uid
        """),
        {'lab_id': int(lab_id), 'uid': current_user.id}
    ).first()

    if not assigned_lab:
        flash('You can only add computers to your assigned labs.')
        return redirect(url_for('incharge_dashboard'))

    existing = db.session.execute(
        text("""
            SELECT computer_id
            FROM computers
            WHERE computer_code = :code
        """),
        {'code': computer_code}
    ).first()

    if existing:
        flash('That computer code already exists.')
        return redirect(url_for('incharge_dashboard'))

    try:
        db.session.execute(
            text("""
                INSERT INTO computers
                    (computer_code, lab_id, health_status,
                     health_updated_by, health_updated_at)
                VALUES
                    (:code, :lab_id, :status, :uid, CURRENT_TIMESTAMP)
            """),
            {
                'code': computer_code,
                'lab_id': int(lab_id),
                'status': health_status,
                'uid': current_user.id
            }
        )
        db.session.commit()
        flash(f'Computer {computer_code} added successfully.')

    except Exception:
        db.session.rollback()
        app.logger.exception('Adding computer failed')
        flash('Could not add the computer. Check the code and try again.')

    return redirect(url_for('incharge_dashboard'))


# Update health only for computers in the in-charge's assigned labs.
@app.post('/incharge/computer/<int:computer_id>/health')
@roles('INCHARGE')
def update_computer_health(computer_id):
    status = request.form.get('health_status', '').upper()
    description = request.form.get('description', '').strip()[:2000]
    if not description:
        description = 'Computer marked unhealthy by lab in-charge.'

    if status not in ('HEALTHY', 'UNHEALTHY'):
        flash('Invalid computer health status.')
        return redirect(url_for('incharge_dashboard'))

    try:
        row = db.session.execute(
            text("""
                SELECT c.computer_id, c.health_status
                FROM computers c
                JOIN labs l ON l.lab_id = c.lab_id
                WHERE c.computer_id = :cid AND l.incharge_user_id = :uid
                FOR UPDATE
            """),
            {'cid': computer_id, 'uid': current_user.id}
        ).first()
        if not row:
            db.session.rollback()
            flash('Computer not found in your assigned labs.')
            return redirect(url_for('incharge_dashboard'))

        db.session.execute(
            text("""
                UPDATE computers
                SET health_status = :status,
                    health_updated_by = :uid,
                    health_updated_at = CURRENT_TIMESTAMP
                WHERE computer_id = :cid
            """),
            {'status': status, 'uid': current_user.id, 'cid': computer_id}
        )

        active = db.session.execute(
            text("""
                SELECT maintenance_id
                FROM maintenance
                WHERE computer_id = :cid AND status IN ('OPEN', 'IN_PROGRESS')
                ORDER BY reported_at DESC
                LIMIT 1
                FOR UPDATE
            """),
            {'cid': computer_id}
        ).first()

        if status == 'UNHEALTHY':
            if active:
                db.session.execute(
                    text("""
                        UPDATE maintenance
                        SET reported_by = COALESCE(reported_by, :uid),
                            description = :description
                        WHERE maintenance_id = :mid
                    """),
                    {'uid': current_user.id, 'description': description,
                     'mid': active[0]}
                )
            else:
                db.session.execute(
                    text("""
                        INSERT INTO maintenance
                            (computer_id, reported_by, description, status, reported_at, resolved_at)
                        VALUES (:cid, :uid, :description, 'OPEN', CURRENT_TIMESTAMP, NULL)
                    """),
                    {'cid': computer_id, 'uid': current_user.id,
                     'description': description}
                )
            flash('Computer marked unhealthy; maintenance record opened.')
        else:
            if active:
                db.session.execute(
                    text("""
                        UPDATE maintenance
                        SET status = 'RESOLVED', resolved_at = CURRENT_TIMESTAMP
                        WHERE maintenance_id = :mid
                    """),
                    {'mid': active[0]}
                )
                flash('Computer marked healthy; maintenance record resolved.')
            else:
                flash('Computer marked healthy. No open maintenance record needed.')

        db.session.commit()
    except Exception:
        db.session.rollback()
        app.logger.exception('Computer health / maintenance update failed')
        flash('Could not update computer health or maintenance record.')

    return redirect(url_for('incharge_dashboard'))


@app.get('/incharge/maintenance')
@roles('INCHARGE')
def incharge_maintenance():
    rows = db.session.execute(
        text("""
            SELECT m.maintenance_id, m.computer_id, c.computer_code,
                   l.lab_name, m.reported_by, reporter.full_name AS reported_by_name,
                   m.description, m.status, m.reported_at, m.resolved_at
            FROM maintenance m
            JOIN computers c ON c.computer_id = m.computer_id
            JOIN labs l ON l.lab_id = c.lab_id
            LEFT JOIN users reporter ON reporter.user_id = m.reported_by
            WHERE l.incharge_user_id = :uid
            ORDER BY
                CASE m.status WHEN 'OPEN' THEN 1 WHEN 'IN_PROGRESS' THEN 2 ELSE 3 END,
                m.reported_at DESC
        """),
        {'uid': current_user.id}
    ).mappings().all()
    return render_template('maintenance.html', maintenance_rows=rows)


@app.post('/incharge/maintenance/<int:maintenance_id>/status')
@roles('INCHARGE')
def update_maintenance_status(maintenance_id):
    status = request.form.get('status', '').upper()
    if status not in ('OPEN', 'IN_PROGRESS'):
        flash('Choose OPEN or IN_PROGRESS here. Mark the computer HEALTHY to resolve a repair.')
        return redirect(url_for('incharge_maintenance'))

    result = db.session.execute(
        text("""
            UPDATE maintenance m
            JOIN computers c ON c.computer_id = m.computer_id
            JOIN labs l ON l.lab_id = c.lab_id
            SET m.status = :status,
                m.resolved_at = NULL
            WHERE m.maintenance_id = :mid
              AND l.incharge_user_id = :uid
              AND m.status IN ('OPEN', 'IN_PROGRESS')
        """),
        {'status': status, 'mid': maintenance_id, 'uid': current_user.id}
    )
    db.session.commit()
    flash('Maintenance status updated.' if result.rowcount else
          'Open maintenance record not found in your assigned labs.')
    return redirect(url_for('incharge_maintenance'))


# --------------------------------------------------
# API ROUTES
# --------------------------------------------------

@app.get('/api/me')
@login_required
def me():
    return jsonify(
        college_id=current_user.college_id,
        full_name=current_user.full_name,
        role=current_user.role
    )


@app.get('/api/slots')
@login_required
def slots():
    rows = db.session.execute(
        text("""
            SELECT slot_id, day_of_week, slot_code,
                   TIME_FORMAT(start_time, '%H:%i') AS start_time,
                   TIME_FORMAT(end_time, '%H:%i') AS end_time
            FROM timetable_slots
            WHERE slot_code LIKE 'L%'
            ORDER BY start_time, slot_code
        """)
    ).mappings().all()

    return jsonify(slots=[dict(row) for row in rows])


@app.get('/api/timetable-slots')
@roles('STUDENT', 'FACULTY')
def api_timetable_slots():
    rows = db.session.execute(
        text("""
            SELECT slot_id, day_of_week, slot_code, display_label
            FROM timetable_slots
            WHERE day_of_week IN ('MON', 'TUE', 'WED', 'THU', 'FRI')
            ORDER BY FIELD(day_of_week, 'MON', 'TUE', 'WED', 'THU', 'FRI'),
                     start_time
        """)
    ).mappings().all()

    return jsonify(slots=[dict(row) for row in rows])


def selected_slots(raw, date_value):
    if (
        not isinstance(raw, list)
        or not 1 <= len(raw) <= 6
        or any(type(value) != int or value <= 0 for value in raw)
        or len(set(raw)) != len(raw)
    ):
        raise ValueError('Select 1–6 distinct timetable periods.')

    rows = db.session.execute(
        text("""
            SELECT slot_id, day_of_week, start_time, end_time
            FROM timetable_slots
            WHERE slot_id IN :ids
        """).bindparams(bindparam('ids', expanding=True)),
        {'ids': raw}
    ).mappings().all()

    if len(rows) != len(raw):
        raise ValueError('Unknown timetable period.')

    expected_day = DAYS[date_value.weekday()]

    if any(row['day_of_week'] != expected_day for row in rows):
        raise ValueError('Date does not match the timetable day.')

    ordered = db.session.execute(
        text("""
            SELECT slot_id
            FROM timetable_slots
            WHERE day_of_week = :day AND slot_code LIKE 'L%'
            ORDER BY start_time
        """),
        {'day': expected_day}
    ).scalars().all()

    positions = sorted(ordered.index(row['slot_id']) for row in rows)

    if positions != list(range(positions[0], positions[0] + len(positions))):
        raise ValueError('Periods must be adjacent.')

    if positions[0] < 6 and positions[-1] >= 6:
        raise ValueError('Cannot book across lunch.')

    return rows


def availability(day, slot_ids):
    rows = db.session.execute(
        text("""
            SELECT c.computer_id, c.computer_code, l.lab_name
            FROM computers c
            JOIN labs l ON l.lab_id = c.lab_id
            WHERE c.health_status = 'HEALTHY'
              AND NOT EXISTS (
                  SELECT 1
                  FROM booking_items bi
                  JOIN bookings b ON b.booking_id = bi.booking_id
                  WHERE bi.computer_id = c.computer_id
                    AND bi.slot_id IN :ids
                    AND b.booking_date = :day
                    AND b.status = 'CONFIRMED'
              )
            ORDER BY l.lab_name, c.computer_code
        """).bindparams(bindparam('ids', expanding=True)),
        {'ids': slot_ids, 'day': day}
    ).mappings().all()

    return [dict(row) for row in rows]


@app.get('/api/computers/available')
@roles('STUDENT', 'FACULTY')
def available_computers():
    try:
        day = date.fromisoformat(request.args['date'])

        if day < date.today():
            raise ValueError('Cannot book past dates.')

        raw_ids = request.args.get(
            'slot_ids',
            request.args.get('slot_id', '')
        )
        ids = [int(value) for value in raw_ids.split(',')]

        selected_slots(ids, day)

        return jsonify(
            date=day.isoformat(),
            slot_ids=ids,
            available_computers=availability(day, ids)
        )

    except (KeyError, TypeError, ValueError) as error:
        return jsonify(error=str(error)), 400


@app.post('/api/bookings')
@roles('STUDENT', 'FACULTY')
def create_booking():
    payload = request.get_json(silent=True) or {}

    try:
        day = date.fromisoformat(payload['date'])

        if day < date.today():
            raise ValueError('Cannot book past dates.')

        slot_ids = payload['slot_ids']
        selected_slots(slot_ids, day)

        computer_ids = payload['computer_ids']

        if (
            not isinstance(computer_ids, list)
            or not 1 <= len(computer_ids) <= 50
            or any(type(value) != int or value <= 0 for value in computer_ids)
            or len(set(computer_ids)) != len(computer_ids)
        ):
            raise ValueError('Select distinct computers.')

        if current_user.role == 'STUDENT' and len(computer_ids) != 1:
            raise ValueError('Students must select exactly one computer.')

        purpose = payload.get('purpose', 'Lab work')

        if not isinstance(purpose, str) or len(purpose) > 255:
            raise ValueError('Invalid purpose.')
        
        # Lock the user's row to prevent simultaneous booking requests
        # from bypassing the daily booking limit.
        if current_user.role == 'STUDENT':
            db.session.execute(
                text("""
                    SELECT user_id
                    FROM users
                    WHERE user_id = :uid
                    FOR UPDATE
                """),
                {'uid': current_user.id}
            )

            # Limit students to 2 confirmed bookings per day.
            daily_count = db.session.execute(
                text("""
                    SELECT COUNT(*)
                    FROM bookings
                    WHERE user_id = :uid
                      AND booking_date = :day
                      AND status = 'CONFIRMED'
                """),
                {'uid': current_user.id, 'day': day}
            ).scalar_one()

            if daily_count >= 2:
                db.session.rollback()
                return jsonify(
                    error='Daily limit reached. Students can make only 2 confirmed bookings per day.'
                ), 409

            # Prevent booking the same timetable periods twice,
            # even if the student chooses a different computer.
            overlap_count = db.session.execute(
                text("""
                    SELECT COUNT(DISTINCT b.booking_id)
                    FROM bookings b
                    JOIN booking_items bi
                      ON bi.booking_id = b.booking_id
                    WHERE b.user_id = :uid
                      AND b.booking_date = :day
                      AND b.status = 'CONFIRMED'
                      AND bi.slot_id IN :slot_ids
                """).bindparams(
                    bindparam('slot_ids', expanding=True)
                ),
                {
                    'uid': current_user.id,
                    'day': day,
                    'slot_ids': slot_ids
                }
            ).scalar_one()

            if overlap_count > 0:
                db.session.rollback()
                return jsonify(
                    error='You already have a confirmed booking for one or more selected periods.'
                ), 409


        locked = db.session.execute(
            text("""
                SELECT computer_id, health_status
                FROM computers
                WHERE computer_id IN :ids
                ORDER BY computer_id
                FOR UPDATE
            """).bindparams(bindparam('ids', expanding=True)),
            {'ids': sorted(computer_ids)}
        ).mappings().all()

        if (
            len(locked) != len(computer_ids)
            or any(row['health_status'] != 'HEALTHY' for row in locked)
        ):
            db.session.rollback()
            return jsonify(error='Computer missing or unhealthy.'), 409

        # Check current confirmed bookings while holding the computer row lock.
        conflict = db.session.execute(
            text("""
                SELECT bi.computer_id
                FROM booking_items bi
                JOIN bookings b ON b.booking_id = bi.booking_id
                WHERE bi.computer_id IN :computer_ids
                  AND bi.slot_id IN :slot_ids
                  AND b.booking_date = :day
                  AND b.status = 'CONFIRMED'
                LIMIT 1
                FOR UPDATE
            """).bindparams(
                bindparam('computer_ids', expanding=True),
                bindparam('slot_ids', expanding=True)
            ),
            {
                'computer_ids': sorted(computer_ids),
                'slot_ids': slot_ids,
                'day': day
            }
        ).first()

        if conflict:
            db.session.rollback()
            return jsonify(
                error='Computer already booked for at least one selected period.'
            ), 409

        result = db.session.execute(
            text("""
                INSERT INTO bookings
                    (user_id, booking_date, purpose, status)
                VALUES
                    (:uid, :day, :purpose, 'CONFIRMED')
            """),
            {
                'uid': current_user.id,
                'day': day,
                'purpose': purpose
            }
        )

        booking_id = result.lastrowid

        for computer_id in computer_ids:
            for slot_id in slot_ids:
                db.session.execute(
                    text("""
                        INSERT INTO booking_items
                            (booking_id, computer_id, slot_id)
                        VALUES (:bid, :cid, :sid)
                    """),
                    {
                        'bid': booking_id,
                        'cid': computer_id,
                        'sid': slot_id
                    }
                )

        db.session.commit()

        return jsonify(
            message='Booking confirmed',
            booking_id=booking_id
        ), 201

    except (ValueError, KeyError, TypeError) as error:
        db.session.rollback()
        return jsonify(error=str(error)), 400

    except Exception:
        db.session.rollback()
        app.logger.exception('Booking failed')
        return jsonify(error='Booking failed.'), 500


@app.get('/api/bookings/mine')
@roles('STUDENT', 'FACULTY')
def mine():
    rows = db.session.execute(
        text("""
            SELECT
                b.booking_id,
                DATE_FORMAT(b.booking_date, '%Y-%m-%d') AS booking_date,
                b.purpose,
                b.status,
                GROUP_CONCAT(
                    DISTINCT c.computer_code ORDER BY c.computer_code
                ) AS computers,
                GROUP_CONCAT(
                    DISTINCT s.slot_code ORDER BY s.start_time
                ) AS periods
            FROM bookings b
            JOIN booking_items bi ON bi.booking_id = b.booking_id
            JOIN computers c ON c.computer_id = bi.computer_id
            JOIN timetable_slots s ON s.slot_id = bi.slot_id
            WHERE b.user_id = :uid
            GROUP BY b.booking_id, b.booking_date, b.purpose, b.status
            ORDER BY b.booking_date DESC, b.booking_id DESC
        """),
        {'uid': current_user.id}
    ).mappings().all()

    return jsonify(bookings=[dict(row) for row in rows])


@app.post('/api/bookings/<int:booking_id>/cancel')
@roles('STUDENT', 'FACULTY')
def cancel(booking_id):
    result = db.session.execute(
        text("""
            UPDATE bookings
            SET status = 'CANCELLED'
            WHERE booking_id = :id
              AND user_id = :uid
              AND status = 'CONFIRMED'
        """),
        {
            'id': booking_id,
            'uid': current_user.id
        }
    )

    db.session.commit()

    if result.rowcount:
        flash('Booking cancelled successfully.')
    else:
        flash('Booking not found or already cancelled.')

    return redirect(url_for('my_bookings'))


@app.get('/api/computers')
@roles('STAFF', 'INCHARGE')
def computers():
    rows = db.session.execute(
        text("""
            SELECT
                c.computer_id,
                c.computer_code,
                c.health_status,
                l.lab_name,
                l.floor_number,
                (l.incharge_user_id = :uid) AS can_edit
            FROM computers c
            JOIN labs l ON l.lab_id = c.lab_id
            ORDER BY l.lab_name, c.computer_code
        """),
        {'uid': current_user.id}
    ).mappings().all()

    return jsonify(computers=[dict(row) for row in rows])


@app.post('/api/computers/<int:computer_id>/health')
@roles('INCHARGE')
def health(computer_id):
    data = request.get_json(silent=True) or {}
    status = data.get('health_status')

    if status not in ('HEALTHY', 'UNHEALTHY'):
        return jsonify(error='Invalid status'), 400

    description = str(data.get('description', '')).strip()[:2000]
    if not description:
        description = 'Marked ' + status.lower()

    row = db.session.execute(
        text("""
            SELECT c.computer_id
            FROM computers c
            JOIN labs l ON l.lab_id = c.lab_id
            WHERE c.computer_id = :cid
              AND l.incharge_user_id = :uid
            FOR UPDATE
        """),
        {
            'cid': computer_id,
            'uid': current_user.id
        }
    ).first()

    if not row:
        db.session.rollback()
        return jsonify(error='Not assigned to this lab'), 403

    db.session.execute(
        text("""
            UPDATE computers
            SET health_status = :status,
                health_updated_by = :uid,
                health_updated_at = CURRENT_TIMESTAMP
            WHERE computer_id = :cid
        """),
        {
            'status': status,
            'uid': current_user.id,
            'cid': computer_id
        }
    )

    active = db.session.execute(
        text("""
            SELECT maintenance_id
            FROM maintenance
            WHERE computer_id = :cid AND status IN ('OPEN', 'IN_PROGRESS')
            ORDER BY reported_at DESC
            LIMIT 1
            FOR UPDATE
        """),
        {'cid': computer_id}
    ).first()

    if status == 'UNHEALTHY':
        if active:
            db.session.execute(
                text("""
                    UPDATE maintenance
                    SET reported_by = COALESCE(reported_by, :uid),
                        description = :description
                    WHERE maintenance_id = :mid
                """),
                {'uid': current_user.id, 'description': description, 'mid': active[0]}
            )
        else:
            db.session.execute(
                text("""
                    INSERT INTO maintenance
                        (computer_id, reported_by, description, status, reported_at, resolved_at)
                    VALUES (:cid, :uid, :description, 'OPEN', CURRENT_TIMESTAMP, NULL)
                """),
                {'cid': computer_id, 'uid': current_user.id, 'description': description}
            )
    elif active:
        db.session.execute(
            text("""
                UPDATE maintenance
                SET status = 'RESOLVED', resolved_at = CURRENT_TIMESTAMP
                WHERE maintenance_id = :mid
            """),
            {'mid': active[0]}
        )

    db.session.commit()
    return jsonify(message='Health and maintenance updated')


@app.get('/test-db')
def test_db():
    return jsonify(
        status='connected',
        database=db.session.execute(text('SELECT DATABASE()')).scalar()
    )


if __name__ == '__main__':
    app.run(debug=True, port=5002)
