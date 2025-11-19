import streamlit as st
from datetime import datetime
import numpy as np
import pandas as pd
from PIL import Image
import cv2
import time
import hashlib
import json
import os
import psycopg2
from dotenv import load_dotenv
import bcrypt
import random
from datetime import timedelta

# Load environment variables
load_dotenv()

# ==================== PASSWORD FUNCTIONS ====================
def hash_password(password):
    """Hash password menggunakan bcrypt"""
    try:
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    except Exception as e:
        return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed_password):
    """Verify password dengan hash"""
    try:
        if hashed_password.startswith('$2b$'):  # bcrypt format
            return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
        else:  # fallback to sha256
            return hashed_password == hashlib.sha256(password.encode()).hexdigest()
    except Exception as e:
        return False

# ==================== DATABASE FUNCTIONS ====================
def init_database():
    """Initialize database tables jika perlu"""
    try:
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        cur = conn.cursor()
        
        # Check jika tables sudah wujud dengan structure yang betul
        cur.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'patients' AND column_name = 'user_id'
        """)
        has_user_id = cur.fetchone() is not None
        
        if not has_user_id:
            # Update patients table jika perlu
            cur.execute("""
                ALTER TABLE patients ADD COLUMN IF NOT EXISTS user_id INTEGER
            """)
        
        conn.commit()
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Database init warning: {e}")
        return True  # Continue anyway

def test_database_connection():
    """Test database connection dan show current structure"""
    try:
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        cur = conn.cursor()
        
        st.success("✅ PostgreSQL Connection SUCCESSFUL!")
        
        # Get database info
        cur.execute("SELECT version(), current_database()")
        db_info = cur.fetchone()
        st.write(f"**Database Version:** {db_info[0]}")
        st.write(f"**Database Name:** {db_info[1]}")
        
        # Get table structures
        st.write("**📊 Table Structures:**")
        
        # Check patients table
        cur.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'patients' 
            ORDER BY ordinal_position
        """)
        patient_columns = cur.fetchall()
        
        st.write("**Patients Table Columns:**")
        for col in patient_columns:
            st.write(f"- `{col[0]}` ({col[1]}, nullable: {col[2]})")
        
        # Check users table
        cur.execute("SELECT COUNT(*) FROM users")
        user_count = cur.fetchone()[0]
        st.write(f"**Total Users:** {user_count}")
        
        # Show existing users
        cur.execute("SELECT username, email, role, created_at FROM users")
        users = cur.fetchall()
        if users:
            st.write("**👥 Existing Users:**")
            for user in users:
                st.write(f"- **{user[0]}** ({user[1]}) - {user[2]} - {user[3].strftime('%Y-%m-%d')}")
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        st.error(f"❌ Database Connection FAILED: {e}")
        return False

def get_user_id_from_db(username):
    """Get user ID from database"""
    try:
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE username = %s", (username,))
        result = cur.fetchone()
        cur.close()
        conn.close()
        return result[0] if result else 1  # Default to 1 jika tidak jumpa
    except Exception as e:
        print(f"Error getting user ID: {e}")
        return 1

# ==================== AUTHENTICATION FUNCTION ====================
def authenticate_user(username, password):
    """Authenticate user with database"""
    try:
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        cur = conn.cursor()
        cur.execute(
            "SELECT id, username, name, password_hash, role FROM users WHERE username = %s OR email = %s",
            (username.lower(), username.lower())
        )
        result = cur.fetchone()
        cur.close()
        conn.close()
        
        if result and verify_password(password, result[3]):
            return {
                'user_id': result[0],
                'username': result[1], 
                'name': result[2],
                'role': result[4],
                'authenticated': True
            }
        else:
            return {'authenticated': False}
    except Exception as e:
        st.error(f"Authentication error: {e}")
        return {'authenticated': False}

# ===== CONFIGURATION =====
st.set_page_config(
    page_title="Pinnalogy AI - Professional Ear Analysis",
    page_icon="👂",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===== AUTHENTICATION SYSTEM =====
def initialize_session_state():
    """Initialize session state variables"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None
    if 'user_role' not in st.session_state:
        st.session_state.user_role = None
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'user_name' not in st.session_state:
        st.session_state.user_name = None
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Login"

def login_user(username, password):
    """Authenticate user login"""
    auth_result = authenticate_user(username, password)
    
    if auth_result['authenticated']:
        st.session_state.authenticated = True
        st.session_state.current_user = auth_result['username']
        st.session_state.user_name = auth_result['name']
        st.session_state.user_role = auth_result['role']
        st.session_state.user_id = auth_result['user_id']
        st.session_state.current_page = "Dashboard"
        return True, f"Welcome back, {auth_result['name']}!"
    else:
        return False, "Invalid username or password"

# ==================== PATIENT MANAGEMENT SYSTEM ====================
def save_patient_to_db(patient_data):
    """Save patient to database - compatible dengan existing structure"""
    try:
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        cur = conn.cursor()
        
        # Check jika user_id column wujud
        cur.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'patients' AND column_name = 'user_id'
        """)
        has_user_id = cur.fetchone() is not None
        
        if has_user_id:
            # Insert dengan user_id
            cur.execute("""
                INSERT INTO patients (user_id, patient_code, full_name, age, gender, contact_info, medical_history)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                st.session_state.user_id,
                patient_data['patient_code'],
                patient_data['full_name'],
                patient_data['age'],
                patient_data['gender'],
                patient_data['contact_info'],
                patient_data['medical_history']
            ))
        else:
            # Insert tanpa user_id (backward compatibility)
            cur.execute("""
                INSERT INTO patients (patient_code, full_name, age, gender, contact_info, medical_history)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                patient_data['patient_code'],
                patient_data['full_name'],
                patient_data['age'],
                patient_data['gender'],
                patient_data['contact_info'],
                patient_data['medical_history']
            ))
        
        patient_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        
        return True
        
    except Exception as e:
        st.error(f"Database error: {str(e)}")
        return False

def get_patients_from_db():
    """Get patients from database - compatible dengan existing structure"""
    try:
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        cur = conn.cursor()
        
        # Check jika user_id column wujud
        cur.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'patients' AND column_name = 'user_id'
        """)
        has_user_id = cur.fetchone() is not None
        
        if has_user_id and st.session_state.user_role != "admin":
            # Filter by user_id untuk non-admin users
            cur.execute("""
                SELECT id, patient_code, full_name, age, gender, contact_info, medical_history, created_at 
                FROM patients 
                WHERE user_id = %s
                ORDER BY created_at DESC
            """, (st.session_state.user_id,))
        else:
            # Get all patients (untuk admin atau jika tiada user_id column)
            cur.execute("""
                SELECT id, patient_code, full_name, age, gender, contact_info, medical_history, created_at 
                FROM patients 
                ORDER BY created_at DESC
            """)
        
        patients = cur.fetchall()
        cur.close()
        conn.close()
        return patients
        
    except Exception as e:
        st.error(f"Error loading patients: {e}")
        return []

# ==================== SAMPLE DATA CREATION ====================
def create_sample_patients():
    """Create sample patients dengan structure yang compatible"""
    
    try:
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        cur = conn.cursor()
        
        st.info("🔄 Creating sample patients...")
        
        # Sample data
        malay_names = [
            "Ahmad bin Abdullah", "Siti binti Hassan", "Mohammad bin Ismail", 
            "Aishah binti Mohd", "Ali bin Ahmad", "Nor binti Omar",
            "Razak bin Mahmud", "Zainab binti Sulaiman", "Hafiz bin Rahman",
            "Fatimah binti Yusof"
        ]
        
        # Clear existing sample data
        cur.execute("DELETE FROM patients WHERE patient_code LIKE 'SMP%'")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Create 10 sample patients (boleh adjust)
        for i in range(1, 11):
            patient_code = f"SMP{i:03d}"
            full_name = random.choice(malay_names)
            age = random.randint(20, 65)
            gender = random.choice(["Male", "Female"])
            
            phone = f"+601{random.randint(2,9)}{random.randint(1000000, 9999999):07d}"
            contact_info = f"Phone: {phone}, Email: patient{patient_code}@example.com"
            
            conditions = ["Hypertension", "Diabetes", "Asthma", "None"]
            medical_history = f"Conditions: {random.choice(conditions)}. Regular checkup patient."
            
            # Check user_id column
            cur.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'patients' AND column_name = 'user_id'
            """)
            has_user_id = cur.fetchone() is not None
            
            if has_user_id:
                cur.execute("""
                    INSERT INTO patients (user_id, patient_code, full_name, age, gender, contact_info, medical_history)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (st.session_state.user_id, patient_code, full_name, age, gender, contact_info, medical_history))
            else:
                cur.execute("""
                    INSERT INTO patients (patient_code, full_name, age, gender, contact_info, medical_history)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (patient_code, full_name, age, gender, contact_info, medical_history))
            
            status_text.text(f"Creating patient {i}/10: {full_name}")
            progress_bar.progress(i / 10)
        
        conn.commit()
        cur.close()
        conn.close()
        
        st.success("🎉 Successfully created sample patients!")
        time.sleep(2)
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error creating sample data: {e}")

# ===== EAR REFLEXOLOGY MAPPING =====
EAR_REFLEXOLOGY_MAP = {
    "earlobe": ["Head", "Brain", "Eye", "Ear", "Teeth", "Jaw"],
    "helix_rim": ["Spine", "Back", "Neck", "Shoulders", "Nervous System"],
    "anti_helix": ["Internal Organs", "Chest", "Abdomen", "Digestive System"],
    "tragus": ["Throat", "Thyroid", "Respiratory", "Sinuses"],
    "anti_tragus": ["Heart", "Circulation", "Blood Pressure", "Cardiovascular"],
    "concha": ["Digestive System", "Liver", "Kidneys", "Intestines", "Metabolism"]
}

# ===== AI ANALYSIS FUNCTIONS =====
def analyze_systemic_health_via_ear(image):
    """Simple ear analysis simulation"""
    try:
        zones = random.sample(list(EAR_REFLEXOLOGY_MAP.keys()), random.randint(2, 4))
        
        analysis_results = {
            'detected_zones': zones,
            'color_analysis': {"status": "Normal coloration patterns detected"},
            'texture_analysis': {"status": "Healthy skin texture observed"},
            'structural_features': ["Well-defined ear structure"],
            'potential_concerns': random.choice([[], ["Recommend hydration improvement"], ["Good overall health"]]),
            'recommended_checks': ["Routine health screening"],
            'lifestyle_suggestions': ["Maintain balanced diet and exercise"],
            'confidence_level': random.choice(["high", "moderate"]),
            'analysis_date': datetime.now().isoformat()
        }
        
        return analysis_results
        
    except Exception as e:
        return {
            'detected_zones': ["general_ear_structure"],
            'color_analysis': {"status": "Analysis completed"},
            'texture_analysis': {"status": "Analysis completed"},
            'structural_features': ["Standard ear anatomy"],
            'potential_concerns': [],
            'recommended_checks': ["Routine checkup"],
            'confidence_level': "moderate"
        }

# ===== PAGE FUNCTIONS =====
def login_page():
    """Login page"""
    st.title("🔐 Pinnalogy AI Professional")
    st.subheader("Ear Reflexology Analysis System")
    
    # Initialize database
    init_database()
    
    st.subheader("Practitioner Login")
    
    with st.form("login_form"):
        username = st.text_input("👤 Username", placeholder="admin")
        password = st.text_input("🔑 Password", type="password", placeholder="admin123")
        login_button = st.form_submit_button("🚀 Login", use_container_width=True)
        
        if login_button:
            if username and password:
                success, message = login_user(username, password)
                if success:
                    st.success(message)
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(message)
            else:
                st.error("Please fill in all fields")
    
    st.markdown("---")
    st.info("**Demo Account:** username: `admin` / password: `admin123`")

def dashboard_page():
    """Main dashboard after login"""
    st.header(f"🏠 Welcome, {st.session_state.user_name}!")
    
    patients = get_patients_from_db()
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Patients", len(patients))
    
    with col2:
        st.metric("Today's Analyses", "0")
    
    with col3:
        st.metric("System Status", "🟢 Online")
    
    with col4:
        st.metric("User Role", st.session_state.user_role)
    
    # Quick actions
    st.subheader("⚡ Quick Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("➕ New Patient", use_container_width=True):
            st.session_state.current_page = "Patient Management"
            st.rerun()
    
    with col2:
        if st.button("🔍 Ear Analysis", use_container_width=True):
            st.session_state.current_page = "Ear Analysis"
            st.rerun()
    
    with col3:
        if st.button("📊 View Reports", use_container_width=True):
            st.session_state.current_page = "Reports"
            st.rerun()
    
    # Recent patients
    st.subheader("📈 Recent Patients")
    if patients:
        for patient in patients[:5]:
            with st.expander(f"👤 {patient[2]} - {patient[1]}"):
                st.write(f"**Age:** {patient[3]}")
                st.write(f"**Gender:** {patient[4]}")
                st.write(f"**Registered:** {patient[7].strftime('%Y-%m-%d')}")
    else:
        st.info("No patients yet. Add your first patient to get started!")

def patient_management_page():
    """Patient management system"""
    st.header("👥 Patient Management")
    
    patients = get_patients_from_db()
    
    tab1, tab2 = st.tabs(["➕ Add New Patient", "📋 Patient List"])
    
    with tab1:
        st.subheader("Register New Patient")
        
        with st.form("new_patient_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                patient_code = st.text_input("Patient Code *", placeholder="PAT001")
                full_name = st.text_input("Full Name *", placeholder="Ahmad bin Abdullah")
                age = st.number_input("Age *", min_value=1, max_value=120, value=30)
                
            with col2:
                gender = st.selectbox("Gender *", ["Male", "Female", "Other"])
                contact_info = st.text_area("Contact Information", placeholder="Phone: +6012-3456789")
            
            medical_history = st.text_area("Medical History", placeholder="Previous conditions, allergies, medications...")
            
            submit_button = st.form_submit_button("💾 Save Patient Record", use_container_width=True)
            
            if submit_button:
                if not all([patient_code, full_name, age, gender]):
                    st.error("Please fill in all required fields (*)")
                else:
                    patient_data = {
                        'patient_code': patient_code,
                        'full_name': full_name,
                        'age': age,
                        'gender': gender,
                        'contact_info': contact_info,
                        'medical_history': medical_history
                    }
                    
                    if save_patient_to_db(patient_data):
                        st.success(f"✅ Patient {patient_code} registered successfully!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Failed to save patient record. Patient code might already exist.")
    
    with tab2:
        st.subheader("Patient Records")
        
        if patients:
            st.success(f"✅ Found {len(patients)} patients")
            for patient in patients:
                with st.expander(f"👤 {patient[2]} - {patient[1]}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Personal Information:**")
                        st.write(f"**Code:** {patient[1]}")
                        st.write(f"**Age:** {patient[3]}")
                        st.write(f"**Gender:** {patient[4]}")
                    
                    with col2:
                        st.write("**Contact & History:**")
                        st.write(f"**Contact:** {patient[5]}")
                        st.write(f"**Medical History:** {patient[6]}")
                    
                    if st.button(f"🔍 Analyze Ear", key=patient[0]):
                        st.session_state.selected_patient = patient[1]
                        st.session_state.current_page = "Ear Analysis"
                        st.rerun()
        else:
            st.info("📝 No patients found. Add your first patient above.")

def ear_analysis_page():
    """Ear analysis with patient selection"""
    st.header("🔍 Ear Analysis")
    
    patients = get_patients_from_db()
    
    if not patients:
        st.warning("No patients found. Please add a patient first.")
        if st.button("➕ Add New Patient"):
            st.session_state.current_page = "Patient Management"
            st.rerun()
        return
    
    # Patient selection
    patient_options = {patient[1]: f"{patient[2]} ({patient[1]})" for patient in patients}
    selected_patient_code = st.selectbox("👤 Select Patient", options=list(patient_options.keys()), 
                                       format_func=lambda x: patient_options[x])
    
    if selected_patient_code:
        selected_patient = next((p for p in patients if p[1] == selected_patient_code), None)
        
        if selected_patient:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Patient Information")
                st.write(f"**Name:** {selected_patient[2]}")
                st.write(f"**Age:** {selected_patient[3]}")
                st.write(f"**Gender:** {selected_patient[4]}")
                st.write(f"**Code:** {selected_patient[1]}")
            
            with col2:
                st.subheader("Upload Ear Image")
                uploaded_file = st.file_uploader(
                    "📷 Upload Clear Ear Image",
                    type=['jpg', 'jpeg', 'png'],
                    key=f"upload_{selected_patient_code}"
                )
                
                if uploaded_file is not None:
                    image = Image.open(uploaded_file)
                    st.image(image, caption="Uploaded Ear Image", use_column_width=True)
                    
                    if st.button("🧠 Analyze Ear", type="primary", use_container_width=True):
                        with st.spinner("🤖 AI is analyzing ear reflexology patterns..."):
                            time.sleep(2)
                            
                            analysis_results = analyze_systemic_health_via_ear(image)
                            st.success("✅ Analysis completed!")
                            
                            # Display results
                            display_analysis_results(analysis_results, selected_patient)

def display_analysis_results(insights, patient_info):
    """Display analysis results"""
    st.subheader("🎯 Analysis Results")
    
    st.write(f"**Patient:** {patient_info[2]} | **Age:** {patient_info[3]} | **Gender:** {patient_info[4]}")
    
    tab1, tab2, tab3 = st.tabs(["📍 Detected Zones", "📋 Findings", "💡 Recommendations"])
    
    with tab1:
        if insights['detected_zones']:
            st.write("**Detected Ear Zones:**")
            for zone in insights['detected_zones']:
                related_organs = EAR_REFLEXOLOGY_MAP.get(zone, ["General area"])
                st.write(f"• **{zone.title()}**: {', '.join(related_organs)}")
    
    with tab2:
        if insights['color_analysis']:
            st.write("**Color Analysis:**")
            for key, value in insights['color_analysis'].items():
                st.write(f"• **{key.title()}**: {value}")
        
        if insights['texture_analysis']:
            st.write("**Texture Analysis:**")
            for key, value in insights['texture_analysis'].items():
                st.write(f"• **{key.title()}**: {value}")
    
    with tab3:
        if insights['potential_concerns']:
            st.warning("**⚠️ Areas for Attention:**")
            for concern in insights['potential_concerns']:
                st.write(f"• {concern}")
        else:
            st.success("✅ No major concerns detected")
        
        if insights['recommended_checks']:
            st.info("**🩺 Recommended Checks:**")
            for check in insights['recommended_checks']:
                st.write(f"• {check}")
        
        st.write(f"**Confidence Level:** {insights.get('confidence_level', 'N/A').title()}")

def reports_page():
    """Reports and analytics"""
    st.header("📊 Reports & Analytics")
    
    patients = get_patients_from_db()
    
    if patients:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Patients", len(patients))
        
        with col2:
            male_count = sum(1 for p in patients if p[4] == "Male")
            female_count = sum(1 for p in patients if p[4] == "Female")
            st.metric("Gender Distribution", f"♂{male_count} ♀{female_count}")
        
        with col3:
            avg_age = sum(p[3] for p in patients) / len(patients)
            st.metric("Average Age", f"{avg_age:.1f}")
        
        # Patient list
        st.subheader("Patient Details")
        for patient in patients:
            with st.expander(f"👤 {patient[2]} - {patient[1]}"):
                st.write(f"**Age:** {patient[3]} | **Gender:** {patient[4]}")
                st.write(f"**Contact:** {patient[5]}")
                st.write(f"**Medical History:** {patient[6]}")
                st.write(f"**Registered:** {patient[7].strftime('%Y-%m-%d')}")
    else:
        st.info("No patient data available for reports")

def view_sample_data():
    """View sample patient data"""
    st.header("📋 Sample Data Management")
    
    patients = get_patients_from_db()
    
    if patients:
        st.success(f"📊 Found {len(patients)} patients in database")
        
        # Filter sample patients
        sample_patients = [p for p in patients if p[1].startswith('SMP')]
        regular_patients = [p for p in patients if not p[1].startswith('SMP')]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Sample Patients", len(sample_patients))
        
        with col2:
            st.metric("Regular Patients", len(regular_patients))
        
        if sample_patients:
            st.subheader("Sample Patients")
            for patient in sample_patients:
                with st.expander(f"👤 {patient[2]} - {patient[1]}"):
                    st.write(f"**Age:** {patient[3]} | **Gender:** {patient[4]}")
                    st.write(f"**Contact:** {patient[5]}")
                    st.write(f"**Registered:** {patient[7].strftime('%Y-%m-%d')}")
    else:
        st.info("No patients found in database")

def logout_button():
    """Logout button in sidebar"""
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# ===== MAIN APP =====
def main():
    initialize_session_state()
    
    if not st.session_state.authenticated:
        login_page()
    else:
        # Sidebar navigation
        st.sidebar.title("🩺 Pinnalogy AI")
        st.sidebar.write(f"Welcome, {st.session_state.user_name}")
        st.sidebar.write(f"Role: {st.session_state.user_role}")
        
        # Database test button
        if st.sidebar.button("🔧 Database Info"):
            test_database_connection()
        
        # Sample data button
        if st.sidebar.button("📊 Create Sample Data"):
            create_sample_patients()
        
        st.sidebar.markdown("---")
        
        # Navigation menu
        page_options = ["Dashboard", "Patient Management", "Ear Analysis", "Reports", "Sample Data"]
        current_index = page_options.index(st.session_state.current_page) if st.session_state.current_page in page_options else 0
        
        page = st.sidebar.radio("Navigate to:", page_options, index=current_index)
        st.session_state.current_page = page
        
        # Page routing
        if page == "Dashboard":
            dashboard_page()
        elif page == "Patient Management":
            patient_management_page()
        elif page == "Ear Analysis":
            ear_analysis_page()
        elif page == "Reports":
            reports_page()
        elif page == "Sample Data":
            view_sample_data()
        
        # Logout button
        st.sidebar.markdown("---")
        logout_button()
        
        # Footer
        st.sidebar.info("**Professional Edition** v2.3")

if __name__ == "__main__":
    main()
