import streamlit as st
import mysql.connector
import bcrypt
import pandas as pd
from datetime import datetime
import base64

hide_streamlit_cloud_elements = """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
    a[title="View source"] {display: none !important;}
    button[kind="icon"] {display: none !important;}
    </style>
"""
st.markdown(hide_streamlit_cloud_elements, unsafe_allow_html=True)
# --- BACKGROUND IMAGE FUNCTION ---
def set_bg_from_local(image_file):
    with open(image_file, "rb") as image:
        encoded = base64.b64encode(image.read()).decode()
    st.markdown(f"""
        <style>
        .stApp {{
            background: linear-gradient(rgba(255, 255, 255, 0.6), rgba(255, 255, 255, 0.3)),
            url("data:image/jpg;base64,{encoded}");
            background-size: cover;
            background-repeat: no-repeat;
            background-attachment: fixed;
            font-weight: bold !important;
            padding: 20px;
            margin: 5px;
        }}
        .stButton > button {{
            background-color: blue;
            color: white;
            padding: 12px 24px;
            margin: 10px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }}
        .stButton > button:hover {{
            background-color: #45a049;
        }}
        .stTextInput > div > div > input, .stTextArea > div > div > textarea {{
            padding: 10px;
            margin: 5px;
            border-radius: 5px;
            border: 1px solid black;
        }}
        label {{
            font-weight: bold;
            color: green;
        }}
        .stSelectbox > div > div > select {{
            padding: 10px;
            margin: 5px;
            border-radius: 5px;
            border: 1px solid #ccc;
        }}
        .stDataFrame {{
            background-color: lightblue;
            padding: 10px;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }}
        .stSubheader {{
            font-size: 50px;
            color: #333;
            padding: 30px;
            background-color: blue;
            border-radius: 5px;
            margin-bottom: 15px;
        }}
        </style>
    """, unsafe_allow_html=True)

# ---------------- Database Connection ----------------
def connect_to_mysql():
    try:
        return mysql.connector.connect(
            host='localhost',
            user='root',
            password='root',
            database='hospital_managementt'
        )
    except mysql.connector.Error as err:
        st.error(f"Database Error: {err}")
        return None

# ---------------- Utility Functions ----------------
def hash_password(password):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def authenticate_user(username, password):
    conn = connect_to_mysql()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, password, role FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        if user and bcrypt.checkpw(password.encode('utf-8'), user[1].encode('utf-8')):
            return True, user[2], user[0]
    return False, None, None

# ---------------- User Operations ----------------
def register_user(username, password, role):
    if not username.strip():
        st.error("Username cannot be empty.")
        return
    conn = connect_to_mysql()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                           (username, hash_password(password), role))
            conn.commit()
            if role == "doctor":
                user_id = cursor.lastrowid
                cursor.execute("INSERT INTO doctors (name, specialty, user_id) VALUES (%s, %s, %s)",
                               (username, "General", user_id))
                conn.commit()
            st.success("User registered successfully!")
        except mysql.connector.Error as e:
            conn.rollback()
            st.error(f"Database error: {e}")
        finally:
            cursor.close()
            conn.close()

# ---------------- Doctor Operations ----------------
def add_doctor(name, specialty):
    conn = connect_to_mysql()
    if conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO doctors (name, specialty) VALUES (%s, %s)", (name, specialty))
        conn.commit()
        cursor.close()
        conn.close()

def get_doctors():
    conn = connect_to_mysql()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, specialty FROM doctors")
        doctors = cursor.fetchall()
        cursor.close()
        conn.close()
        return doctors
    return []

def delete_doctor(doctor_id):
    conn = connect_to_mysql()
    if conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM doctors WHERE id = %s", (doctor_id,))
        conn.commit()
        cursor.close()
        conn.close()

def get_doctor_id_by_user(user_id):
    conn = connect_to_mysql()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM doctors WHERE user_id = %s", (user_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if row:
            return row[0]
    return None

# ---------------- Patient Operations ----------------
def add_patient(name, age, gender, address, doctor_id=None):
    conn = connect_to_mysql()
    if conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO patients (name, age, gender, address, doctor_id) VALUES (%s, %s, %s, %s, %s)",
                       (name, age, gender, address, doctor_id))
        conn.commit()
        cursor.close()
        conn.close()

def view_patients():
    conn = connect_to_mysql()
    if conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.id, p.name, p.age, p.gender, d.name AS doctor_name, d.specialty 
            FROM patients p 
            LEFT JOIN doctors d ON p.doctor_id = d.id
        """)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return pd.DataFrame(rows, columns=["ID", "Name", "Age", "Gender", "Doctor Name", "Doctor Specialty"])
    return pd.DataFrame()

def delete_patient(patient_id):
    conn = connect_to_mysql()
    if conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM patients WHERE id = %s", (patient_id,))
        conn.commit()
        cursor.close()
        conn.close()

# ---------------- Appointment Operations ----------------
def book_appointment(patient_id, doctor_id, appointment_time):
    conn = connect_to_mysql()
    if conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO appointments (patient_id, doctor_id, appointment_time) VALUES (%s, %s, %s)",
                       (patient_id, doctor_id, appointment_time))
        conn.commit()
        cursor.close()
        conn.close()

def delete_appointment(app_id):
    conn = connect_to_mysql()
    if conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM appointments WHERE id = %s", (app_id,))
        conn.commit()
        cursor.close()
        conn.close()

def get_doctor_appointments(doctor_id):
    conn = connect_to_mysql()
    if conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.id, p.name AS patient_name, a.appointment_time 
            FROM appointments a
            JOIN patients p ON a.patient_id = p.id
            WHERE a.doctor_id = %s
            ORDER BY a.appointment_time ASC
        """, (doctor_id,))
        appointments = cursor.fetchall()
        cursor.close()
        conn.close()
        return pd.DataFrame(appointments, columns=["Appointment ID", "Patient Name", "Appointment Time"])
    return pd.DataFrame()

# ---------------- Main Streamlit App ----------------
def main():
    set_bg_from_local("sa.jpg")
  
    st.title("🏥 Hospital Management System")

    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    menu = ["Login", "Register"]

    if st.session_state.logged_in:
        set_bg_from_local("sa.jpg")
        role = st.session_state.role
        menu = []
        if role == "admin":
            menu += ["Admin Dashboard"]
        elif role == "doctor":
            menu += ["View Appointments"]
        elif role == "receptionist":
            menu += ["Receptionist Dashboard"]
        menu.append("Logout")

    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Login":
        set_bg_from_local("a5.jpg")
        st.subheader("🔐 Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            auth, role, user_id = authenticate_user(username, password)
            if auth:
                st.session_state.logged_in = True
                st.session_state.role = role
                st.session_state.user_id = user_id
                st.success(f"Welcome {username} ({role})")
                st.rerun()
            else:
                st.error("Invalid credentials.")

    elif choice == "Register":
        set_bg_from_local("a2.jpg")
        st.subheader("📝 Register")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        role = st.selectbox("Role", ["admin", "doctor", "receptionist"])
        if st.button("Register"):
            register_user(username, password, role)

    elif choice == "Admin Dashboard":
        set_bg_from_local("a1.jpg")
        st.subheader("📊 Admin Dashboard")
        tab1, tab2, tab3 = st.tabs(["👨‍⚕️ Doctors", "🧑‍🤝‍🧑 Patients", "📅 Appointments"])

        with tab1:
            st.markdown("### View & Delete Doctors")
            docs = get_doctors()
            if docs:
                df = pd.DataFrame(docs, columns=["ID", "Name", "Specialty"])
                st.dataframe(df)
                del_id = st.number_input("Enter Doctor ID to Delete", min_value=1, step=1, key="doc_del_id")
                if st.button("Delete Doctor"):
                    delete_doctor(del_id)
                    st.success("Doctor deleted.")
            else:
                st.info("No doctors found.")

        with tab2:
            st.markdown("### View & Delete Patients")
            df = view_patients()
            if not df.empty:
                st.dataframe(df)
                del_pid = st.number_input("Enter Patient ID to Delete", min_value=1, step=1, key="pt_del_id")
                if st.button("Delete Patient"):
                    delete_patient(del_pid)
                    st.success("Patient deleted.")
            else:
                st.info("No patient records found.")

        with tab3:
            st.markdown("### View Appointments")
            conn = connect_to_mysql()
            if conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT a.id, p.name, d.name, a.appointment_time 
                    FROM appointments a
                    JOIN patients p ON a.patient_id = p.id
                    JOIN doctors d ON a.doctor_id = d.id
                    ORDER BY a.appointment_time
                """)
                rows = cursor.fetchall()
                cursor.close()
                conn.close()
                df = pd.DataFrame(rows, columns=["Appointment ID", "Patient", "Doctor", "Appointment Time"])
                st.dataframe(df)

    elif choice == "Receptionist Dashboard":
        st.subheader("📋 Receptionist Dashboard")
        tab1, tab2, tab3 = st.tabs(["➕ Add Doctor & View", "➕ Add Patient & View", "📅 Appointments"])

        with tab1:
            st.markdown("### Add Doctor")
            name = st.text_input("Doctor Name", key="rec_doc_name")
            specialty = st.text_input("Specialty", key="rec_doc_spec")
            if st.button("Add Doctor", key="rec_add_doc"):
                if name and specialty:
                    add_doctor(name, specialty)
                    st.success("Doctor added successfully.")
                else:
                    st.warning("Please fill all fields.")
            st.markdown("### View Doctors")
            docs = get_doctors()
            if docs:
                df = pd.DataFrame(docs, columns=["ID", "Name", "Specialty"])
                st.dataframe(df)

        with tab2:
            st.markdown("### Add Patient")
            pname = st.text_input("Patient Name", key="rec_pt_name")
            page = st.number_input("Age", min_value=0, key="rec_pt_age")
            pgender = st.selectbox("Gender", ["Male", "Female", "Other"], key="rec_pt_gender")
            paddress = st.text_area("Address", key="rec_pt_address")
            doctors = get_doctors()
            if doctors:
                doctor_map = {f"{doc[1]} ({doc[2]})": doc[0] for doc in doctors}
                doctor_choice = st.selectbox("Assign Doctor", list(doctor_map.keys()), key="rec_doc_assign")
                doctor_id = doctor_map[doctor_choice]
            else:
                doctor_id = None
            if st.button("Add Patient", key="rec_add_pt"):
                if pname and paddress:
                    add_patient(pname, page, pgender, paddress, doctor_id)
                    st.success("Patient added successfully.")
                else:
                    st.warning("Please fill all fields.")
            df = view_patients()
            if not df.empty:
                st.markdown("### View Patients")
                st.dataframe(df)

        with tab3:
            st.markdown("### Book Appointment")
            doctors = get_doctors()
            df_patients = view_patients()
            if doctors and not df_patients.empty:
                patient_map = {f"{row['Name']} (ID: {row['ID']})": row['ID'] for _, row in df_patients.iterrows()}
                doctor_map = {f"{doc[1]} ({doc[2]})": doc[0] for doc in doctors}
                patient_choice = st.selectbox("Select Patient", list(patient_map.keys()), key="rec_sel_pt")
                doctor_choice = st.selectbox("Select Doctor", list(doctor_map.keys()), key="rec_sel_doc")
                app_date = st.date_input("Appointment Date", min_value=datetime.now().date())
                app_time_only = st.time_input("Appointment Time")
                app_time = datetime.combine(app_date, app_time_only)
                if st.button("Book Appointment", key="rec_book_app"):
                    book_appointment(patient_map[patient_choice], doctor_map[doctor_choice], app_time)
                    st.success("Appointment booked successfully.")
            st.markdown("### View All Appointments")
            conn = connect_to_mysql()
            if conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT a.id, p.name, d.name, a.appointment_time 
                    FROM appointments a
                    JOIN patients p ON a.patient_id = p.id
                    JOIN doctors d ON a.doctor_id = d.id
                    ORDER BY a.appointment_time
                """)
                rows = cursor.fetchall()
                cursor.close()
                conn.close()
                df = pd.DataFrame(rows, columns=["Appointment ID", "Patient", "Doctor", "Appointment Time"])
                st.dataframe(df)

    elif choice == "View Appointments":
        st.subheader("📆 Doctor's Appointments")
        doctor_id = get_doctor_id_by_user(st.session_state.user_id)
        if doctor_id:
            df = get_doctor_appointments(doctor_id)
            if not df.empty:
                st.dataframe(df)
            else:
                st.info("No appointments found.")
        else:
            st.error("Doctor record not found.")

    elif choice == "Logout":
        st.session_state.logged_in = False
        st.session_state.role = None
        st.session_state.user_id = None
        st.success("You have been logged out.")
        st.rerun()

if __name__ == '__main__':
    main()
