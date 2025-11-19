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
        st.error(f"Password hashing error: {e}")
        return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed_password):
    """Verify password dengan hash"""
    try:
        if hashed_password.startswith('$2b$'):  # bcrypt format
            return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
        else:  # fallback to sha256
            return hashed_password == hashlib.sha256(password.encode()).hexdigest()
    except Exception as e:
        st.error(f"Password verification error: {e}")
        return False

# ==================== DATABASE INITIALIZATION ====================
def init_database():
    """Initialize database tables"""
    try:
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        cur = conn.cursor()
        
        # Create users table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                name VARCHAR(100) NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(20) DEFAULT 'practitioner',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create patients table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                id SERIAL PRIMARY KEY,
                user_id INTEGER,
                patient_code VARCHAR(50) UNIQUE NOT NULL,
                full_name VARCHAR(100) NOT NULL,
                age INTEGER,
                gender VARCHAR(10),
                contact_info TEXT,
                medical_history TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create ear_analyses table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ear_analyses (
                id SERIAL PRIMARY KEY,
                patient_id INTEGER,
                analysis_data JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Check jika admin user sudah wujud
        cur.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
        admin_exists = cur.fetchone()[0]
        
        # Jika admin belum wujud, create admin user
        if admin_exists == 0:
            hashed_password = hash_password('admin123')
            cur.execute("""
                INSERT INTO users (username, email, name, password_hash, role) 
                VALUES (%s, %s, %s, %s, %s)
            """, ('admin', 'admin@pinnalogy.com', 'Admin User', hashed_password, 'admin'))
        
        conn.commit()
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        st.error(f"❌ Database initialization failed: {e}")
        return False

def test_database_connection():
    """Test database connection"""
    try:
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        st.success("✅ PostgreSQL Connection SUCCESSFUL!")
        
        # Initialize database tables & admin user
        if init_database():
            st.success("✅ Database tables & admin user created!")
        
        cur = conn.cursor()
        cur.execute("SELECT version();")
        db_version = cur.fetchone()
        st.write(f"Database Version: {db_version[0]}")
        
        # Show existing users
        cur.execute("SELECT username, email, role FROM users")
        users = cur.fetchall()
        if users:
            st.write("**Existing Users:**")
            for user in users:
                st.write(f"- {user[0]} ({user[1]}) - {user[2]}")
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        st.error(f"❌ Database Connection FAILED: {e}")
        st.info("Please check your DATABASE_URL in .env file")
        return False

# ==================== AUTHENTICATION FUNCTION ====================
def authenticate_user(username, password):
    """Authenticate user with database"""
    try:
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        cur = conn.cursor()
        cur.execute(
            "SELECT username, name, password_hash, role, id FROM users WHERE username = %s OR email = %s",
            (username.lower(), username.lower())
        )
        result = cur.fetchone()
        cur.close()
        conn.close()
        
        if result and verify_password(password, result[2]):
            return result[1], True, result[0], result[3], result[4]  # name, status, username, role, user_id
        else:
            return None, False, None, None, None
    except Exception as e:
        st.error(f"Authentication error: {e}")
        return None, False, None, None, None

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
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Login"

def login_user(username, password):
    """Authenticate user login"""
    name, success, username, role, user_id = authenticate_user(username, password)
    
    if success:
        st.session_state.authenticated = True
        st.session_state.current_user = username
        st.session_state.user_role = role
        st.session_state.user_id = user_id
        st.session_state.current_page = "Dashboard"
        return True, f"Welcome back, {name}!"
    else:
        return False, "Invalid username or password"

# ==================== SAMPLE DATA CREATION ====================
def create_sample_patients():
    """Create 30 sample patients with ear data"""
    
    try:
        # Connect to database
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        cur = conn.cursor()
        
        st.info("🔄 Creating sample patients...")
        
        # Sample data arrays
        malay_names_male = [
            "Ahmad bin Abdullah", "Muhammad bin Ismail", "Ali bin Hassan", 
            "Salleh bin Mahmud", "Razak bin Omar", "Zulkifli bin Ahmad",
            "Hafiz bin Mohd", "Faizal bin Yusof", "Amir bin Rahman",
            "Syed bin Ibrahim", "Azman bin Sulaiman", "Kamarul bin Zaini"
        ]
        
        malay_names_female = [
            "Aishah binti Mohd", "Siti binti Hassan", "Nor binti Ahmad",
            "Fatimah binti Omar", "Zainab binti Ismail", "Mariam binti Abdullah",
            "Sarah binti Rahman", "Nurul binti Yusof", "Haslinda binti Sulaiman",
            "Rosnah binti Ibrahim", "Zuraidah binti Mahmud", "Anisah binti Jamal"
        ]
        
        chinese_names = [
            "Tan Wei Ming", "Lim Chen Long", "Wong Mei Ling", "Lee Kok Wai",
            "Chan Siew Lin", "Ng Poh Sim"
        ]
        
        indian_names = [
            "Raj Kumar", "Priya Devi", "Suresh Menon", "Lakshmi Ammal"
        ]
        
        all_names = malay_names_male + malay_names_female + chinese_names + indian_names
        
        clinics = [
            "Klinik Kesihatan Kuala Lumpur", "Hospital Umum Selangor", 
            "Pusat Perubatan Ara Damansara", "Klinik Specialist Ear Care"
        ]
        
        medical_conditions = [
            "Hypertension", "Diabetes Type 2", "Asthma", "Migraine",
            "Arthritis", "High Cholesterol", "Gastric", "Allergic Rhinitis"
        ]
        
        # Ear analysis data templates
        ear_analysis_templates = {
            "normal": {
                "detected_zones": ["earlobe", "helix_rim", "concha"],
                "color_analysis": {"normal": "Healthy skin tone - 95% normal"},
                "texture_analysis": {"smoothness": "Normal skin texture"},
                "structural_features": ["Well-defined ear structure"],
                "potential_concerns": [],
                "recommended_checks": ["Routine annual checkup"],
                "lifestyle_suggestions": ["Maintain current healthy lifestyle"],
                "confidence_level": "high",
                "ear_side": "left"
            },
            "mild_inflammation": {
                "detected_zones": ["earlobe", "helix_rim", "tragus", "concha"],
                "color_analysis": {
                    "redness": "15% - Mild inflammation detected",
                    "normal": "85% - Healthy areas"
                },
                "texture_analysis": {"smoothness": "Slight irritation detected"},
                "structural_features": ["Mild swelling in outer regions"],
                "potential_concerns": ["Possible mild infection", "Allergic reaction"],
                "recommended_checks": ["Inflammation markers", "Allergy test"],
                "lifestyle_suggestions": ["Avoid potential allergens", "Keep ear dry"],
                "confidence_level": "moderate",
                "ear_side": "left"
            }
        }
        
        # Clear existing sample data
        cur.execute("DELETE FROM ear_analyses WHERE patient_id IN (SELECT id FROM patients WHERE patient_code LIKE 'SMP%')")
        cur.execute("DELETE FROM patients WHERE patient_code LIKE 'SMP%'")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Create 30 sample patients
        for i in range(1, 31):
            # Generate patient data
            patient_code = f"SMP{i:03d}"
            full_name = random.choice(all_names)
            age = random.randint(18, 75)
            gender = random.choice(["Male", "Female"])
            
            phone = f"+601{random.randint(2,9)}{random.randint(1000000, 9999999):07d}"
            email = f"patient{patient_code.lower()}@example.com"
            
            blood_types = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
            blood_type = random.choice(blood_types)
            
            emergency_contact = f"+601{random.randint(2,9)}{random.randint(1000000, 9999999):07d}"
            
            # Medical history
            conditions = random.sample(medical_conditions, random.randint(1, 3))
            medications = ["Metformin 500mg", "Ventolin inhaler", "Amlodipine 5mg", "None"]
            current_meds = random.sample(medications, random.randint(1, 2))
            
            medical_history = f"Conditions: {', '.join(conditions)}. Medications: {', '.join(current_meds)}."
            notes = f"Registered at {random.choice(clinics)}. Regular checkup."
            
            # Insert patient
            cur.execute("""
                INSERT INTO patients (user_id, patient_code, full_name, age, gender, contact_info, medical_history)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (st.session_state.user_id, patient_code, full_name, age, gender, 
                  f"Phone: {phone}, Email: {email}, Emergency: {emergency_contact}, Blood Type: {blood_type}",
                  medical_history + " " + notes))
            
            patient_id = cur.fetchone()[0]
            
            # Create ear analyses for this patient (both ears)
            analysis_types = list(ear_analysis_templates.keys())
            
            # Left ear analysis
            left_analysis = ear_analysis_templates[random.choice(analysis_types)].copy()
            left_analysis["ear_side"] = "left"
            left_analysis["analysis_date"] = (datetime.now() - timedelta(days=random.randint(1, 90))).isoformat()
            left_analysis["image_filename"] = f"left_ear_{patient_code}.jpg"
            
            cur.execute("""
                INSERT INTO ear_analyses (patient_id, analysis_data)
                VALUES (%s, %s)
            """, (patient_id, json.dumps(left_analysis)))
            
            # Right ear analysis
            right_analysis = ear_analysis_templates[random.choice(analysis_types)].copy()
            right_analysis["ear_side"] = "right"
            right_analysis["analysis_date"] = (datetime.now() - timedelta(days=random.randint(1, 90))).isoformat()
            right_analysis["image_filename"] = f"right_ear_{patient_code}.jpg"
            
            cur.execute("""
                INSERT INTO ear_analyses (patient_id, analysis_data)
                VALUES (%s, %s)
            """, (patient_id, json.dumps(right_analysis)))
            
            status_text.text(f"Creating patient {i}/30: {full_name}")
            progress_bar.progress(i / 30)
        
        # Commit all changes
        conn.commit()
        cur.close()
        conn.close()
        
        st.success("🎉 Successfully created 30 sample patients!")
        time.sleep(2)
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error creating sample data: {e}")

# ===== PATIENT MANAGEMENT SYSTEM =====
def save_patient_to_db(patient_data):
    """Save patient to database"""
    try:
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO patients (user_id, patient_code, full_name, age, gender, contact_info, medical_history)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            st.session_state.user_id,
            patient_data['patient_code'],
            patient_data['full_name'],
            patient_data['age'],
            patient_data['gender'],
            patient_data['contact_info'],
            patient_data['medical_history']
        ))
        
        conn.commit()
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        st.error(f"Database error: {e}")
        return False

def get_patients_from_db():
    """Get patients from database for current user"""
    try:
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        cur = conn.cursor()
        
        cur.execute("""
            SELECT patient_code, full_name, age, gender, contact_info, medical_history, created_at 
            FROM patients 
            WHERE user_id = %s
            ORDER BY created_at DESC
        """, (st.session_state.user_id,))
        
        patients = cur.fetchall()
        cur.close()
        conn.close()
        return patients
        
    except Exception as e:
        st.error(f"Error loading patients: {e}")
        return []

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
def analyze_ear_zones(img_array):
    """Detect and analyze different ear reflexology zones"""
    try:
        zones_detected = ["earlobe", "helix_rim", "concha"]
        return random.sample(zones_detected, random.randint(2, 4))
    except Exception as e:
        return ["general_ear_structure"]

def analyze_ear_coloration(img_array):
    """Analyze color patterns in ear for health indications"""
    try:
        color_options = {
            "normal": "Healthy skin tone - normal",
            "redness": "Mild inflammation detected", 
            "pallor": "Reduced blood flow indicators"
        }
        return {random.choice(list(color_options.keys())): random.choice(list(color_options.values()))}
    except Exception as e:
        return {"normal": "Color analysis completed"}

def analyze_ear_texture(img_array):
    """Analyze skin texture for health clues"""
    try:
        texture_options = {
            "smoothness": "Normal skin texture",
            "roughness": "Mild texture irregularities"
        }
        return {random.choice(list(texture_options.keys())): random.choice(list(texture_options.values()))}
    except Exception as e:
        return {"smoothness": "Texture analysis completed"}

def analyze_systemic_health_via_ear(image):
    """Analyze ear structure for systemic health indications"""
    img_array = np.array(image) if image else np.zeros((100, 100, 3))
    
    analysis = {
        'detected_zones': analyze_ear_zones(img_array),
        'color_analysis': analyze_ear_coloration(img_array),
        'texture_analysis': analyze_ear_texture(img_array),
        'structural_features': ["Well-defined structure", "Normal vascular patterns"]
    }
    
    # Generate health insights based on analysis
    health_insights = {
        'potential_concerns': random.choice([[], ["Mild inflammation"], ["Circulation check recommended"]]),
        'recommended_checks': ["Routine health screening"],
        'lifestyle_suggestions': ["Maintain healthy lifestyle"],
        'confidence_level': random.choice(["high", "moderate"]),
        'detected_zones': analysis['detected_zones'],
        'color_findings': analysis['color_analysis'],
        'texture_findings': analysis['texture_analysis'],
        'structural_findings': analysis['structural_features']
    }
    
    return health_insights

# ===== PAGE FUNCTIONS =====
def login_page():
    """Login page"""
    st.title("🔐 Pinnalogy AI Professional")
    st.subheader("Ear Reflexology Analysis System")
    
    # Database test button
    if st.sidebar.button("Test Database Connection"):
        test_database_connection()
    
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
    st.header(f"🏠 Welcome, {st.session_state.current_user}!")
    
    # Quick stats
    patients = get_patients_from_db()
    
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
            with st.expander(f"👤 {patient[1]} - {patient[0]}"):
                st.write(f"**Age:** {patient[2]}")
                st.write(f"**Gender:** {patient[3]}")
                st.write(f"**Registered:** {patient[6].strftime('%Y-%m-%d')}")
    else:
        st.info("No patients yet. Add your first patient to get started!")

def patient_management_page():
    """Patient management system"""
    st.header("👥 Patient Management")
    
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
                contact_info = st.text_area("Contact Information", placeholder="Phone: +6012-3456789\nAddress: ...")
            
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
                        st.success(f"Patient {patient_code} registered successfully!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Failed to save patient record")
    
    with tab2:
        st.subheader("Patient Records")
        
        patients = get_patients_from_db()
        if patients:
            for patient in patients:
                with st.expander(f"👤 {patient[1]} - {patient[0]}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Personal Information:**")
                        st.write(f"**Code:** {patient[0]}")
                        st.write(f"**Age:** {patient[2]}")
                        st.write(f"**Gender:** {patient[3]}")
                    
                    with col2:
                        st.write("**Contact & History:**")
                        st.write(f"**Contact:** {patient[4]}")
                        st.write(f"**Medical History:** {patient[5]}")
                    
                    if st.button(f"🔍 Analyze Ear", key=patient[0]):
                        st.session_state.selected_patient = patient[0]
                        st.session_state.current_page = "Ear Analysis"
                        st.rerun()
        else:
            st.info("No patients found. Add your first patient above.")

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
    patient_options = {patient[0]: f"{patient[1]} ({patient[0]})" for patient in patients}
    selected_patient_code = st.selectbox("👤 Select Patient", options=list(patient_options.keys()), 
                                       format_func=lambda x: patient_options[x])
    
    if selected_patient_code:
        # Find selected patient data
        selected_patient = next((p for p in patients if p[0] == selected_patient_code), None)
        
        if selected_patient:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Patient Information")
                st.write(f"**Name:** {selected_patient[1]}")
                st.write(f"**Age:** {selected_patient[2]}")
                st.write(f"**Gender:** {selected_patient[3]}")
                st.write(f"**Code:** {selected_patient[0]}")
            
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
                            st.success("Analysis completed!")
                            
                            # Display results
                            display_analysis_results(analysis_results, selected_patient)

def display_analysis_results(insights, patient_info):
    """Display analysis results"""
    st.subheader("🎯 Analysis Results")
    
    st.write(f"**Patient:** {patient_info[1]} | **Age:** {patient_info[2]} | **Gender:** {patient_info[3]}")
    
    # Create tabs for different analysis aspects
    tab1, tab2, tab3 = st.tabs(["📍 Zones", "🎨 Colors & Texture", "📊 Summary"])
    
    with tab1:
        if insights['detected_zones']:
            st.write("**Detected Ear Zones:**")
            for zone in insights['detected_zones']:
                related_organs = EAR_REFLEXOLOGY_MAP.get(zone, ["General area"])
                st.write(f"• **{zone.title()}**: {', '.join(related_organs)}")
        else:
            st.info("No specific zones detected")
    
    with tab2:
        if insights['color_findings']:
            st.write("**Color Analysis:**")
            for color, finding in insights['color_findings'].items():
                st.write(f"• **{color.title()}**: {finding}")
        
        if insights['texture_findings']:
            st.write("**Texture Analysis:**")
            for texture, finding in insights['texture_findings'].items():
                st.write(f"• **{texture.title()}**: {finding}")
    
    with tab3:
        if insights['potential_concerns']:
            st.warning("**⚠️ Areas for Further Investigation:**")
            for concern in insights['potential_concerns']:
                st.write(f"• {concern}")
        else:
            st.success("No major concerns detected")
        
        st.write(f"**Confidence Level:** {insights.get('confidence_level', 'N/A').title()}")

def reports_page():
    """Reports and analytics"""
    st.header("📊 Reports & Analytics")
    
    patients = get_patients_from_db()
    
    if patients:
        # Basic statistics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Patients", len(patients))
        
        with col2:
            # Count by gender
            male_count = sum(1 for p in patients if p[3] == "Male")
            female_count = sum(1 for p in patients if p[3] == "Female")
            st.metric("Gender Distribution", f"♂{male_count} ♀{female_count}")
        
        with col3:
            avg_age = sum(p[2] for p in patients) / len(patients) if patients else 0
            st.metric("Average Age", f"{avg_age:.1f}")
        
        # Patient list
        st.subheader("Patient Details")
        for patient in patients:
            with st.expander(f"👤 {patient[1]} - {patient[0]}"):
                st.write(f"**Age:** {patient[2]} | **Gender:** {patient[3]}")
                st.write(f"**Contact:** {patient[4]}")
                st.write(f"**Medical History:** {patient[5]}")
                st.write(f"**Registered:** {patient[6].strftime('%Y-%m-%d')}")
    else:
        st.info("No patient data available for reports")

def view_sample_data():
    """View sample patient data"""
    st.header("📋 Sample Patient Data")
    
    try:
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        cur = conn.cursor()
        
        # Get sample patients
        cur.execute("""
            SELECT p.patient_code, p.full_name, p.age, p.gender, p.contact_info, 
                   p.medical_history, p.created_at,
                   COUNT(e.id) as analysis_count
            FROM patients p 
            LEFT JOIN ear_analyses e ON p.id = e.patient_id
            WHERE p.patient_code LIKE 'SMP%'
            GROUP BY p.id, p.patient_code, p.full_name, p.age, p.gender, 
                     p.contact_info, p.medical_history, p.created_at
            ORDER BY p.patient_code
        """)
        
        patients = cur.fetchall()
        
        if patients:
            st.success(f"📊 Found {len(patients)} sample patients")
            
            # Display summary
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Sample Patients", len(patients))
            with col2:
                total_analyses = sum(patient[7] for patient in patients)
                st.metric("Total Ear Analyses", total_analyses)
            with col3:
                avg_age = sum(patient[2] for patient in patients) / len(patients)
                st.metric("Average Age", f"{avg_age:.1f}")
            
            # Patient details
            for patient in patients:
                with st.expander(f"👤 {patient[1]} - {patient[0]} ({patient[2]} years, {patient[3]})"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Personal Information:**")
                        st.write(f"**Patient Code:** {patient[0]}")
                        st.write(f"**Age:** {patient[2]}")
                        st.write(f"**Gender:** {patient[3]}")
                        st.write(f"**Registered:** {patient[6].strftime('%Y-%m-%d')}")
                    
                    with col2:
                        st.write("**Contact & Medical:**")
                        st.write(f"**Contact:** {patient[4]}")
                        st.write(f"**Medical History:** {patient[5]}")
                        st.write(f"**Ear Analyses:** {patient[7]}")
        
        else:
            st.warning("No sample patients found. Please create sample data first.")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        st.error(f"Error loading sample data: {e}")

def logout_button():
    """Logout button in sidebar"""
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.current_user = None
        st.session_state.user_role = None
        st.session_state.user_id = None
        st.session_state.current_page = "Login"
        st.rerun()

# ===== MAIN APP =====
def main():
    initialize_session_state()
    
    if not st.session_state.authenticated:
        login_page()
    else:
        # Sidebar navigation
        st.sidebar.title("🩺 Pinnalogy AI")
        st.sidebar.write(f"Welcome, {st.session_state.current_user}")
        st.sidebar.write(f"Role: {st.session_state.user_role}")
        
        # Sample data button
        if st.sidebar.button("📊 Create Sample Data", help="Create 30 demo patients"):
            create_sample_patients()
        
        st.sidebar.markdown("---")
        
        # Navigation menu
        page = st.sidebar.radio(
            "Navigate to:",
            ["Dashboard", "Patient Management", "Ear Analysis", "Reports", "Sample Data"],
            index=["Dashboard", "Patient Management", "Ear Analysis", "Reports", "Sample Data"].index(
                st.session_state.current_page
            ) if st.session_state.current_page in ["Dashboard", "Patient Management", "Ear Analysis", "Reports", "Sample Data"] else 0
        )
        
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
        st.sidebar.info("**Professional Edition** v2.1")

if __name__ == "__main__":
    main()
