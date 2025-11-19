import streamlit as st
from datetime import datetime
import numpy as np
import pandas as pd
from PIL import Image
import tensorflow as tf
import cv2
import time
import hashlib
import json
import os
import streamlit as st
import yaml
from yaml.loader import SafeLoader
from streamlit_authenticator import Authenticate
import os
def main():
    # ==================== CHECK STRUCTURE (TEMP) ====================
    st.subheader("📁 Project Structure Check")
    st.write("Current directory:", os.getcwd())
    st.write("All items in directory:", os.listdir('.'))
    
    important_files = {
        'app.py': os.path.exists('app.py'),
        '.streamlit/config.toml': os.path.exists('.streamlit/config.toml'),
        'requirements.txt': os.path.exists('requirements.txt'),
        'config.yaml': os.path.exists('config.yaml'),
        'data folder': os.path.exists('data')
    }
    
    st.write("File Status:")
    for file, exists in important_files.items():
        status = "✅ EXISTS" if exists else "❌ MISSING"
        st.write(f"{status}: {file}")
    # ==================== END CHECK ====================
    
    # Your existing authentication code continues here...
    # Load config, authenticator, login, etc...

if __name__ == "__main__":
    main()
from streamlit_authenticator import Authenticate

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
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Login"
    if 'patients_data' not in st.session_state:
        st.session_state.patients_data = {}
    if 'user_profiles' not in st.session_state:
        st.session_state.user_profiles = {}

def hash_password(password):
    """Simple password hashing"""
    return hashlib.sha256(password.encode()).hexdigest()

def load_user_database():
    """Load user database from session state"""
    users_db = {
        "admin": {
            "password": hash_password("admin123"),
            "role": "admin",
            "profile": {
                "full_name": "System Administrator",
                "clinic_name": "Pinnalogy HQ",
                "phone": "+6012-3456789",
                "license_number": "MED-ADMIN-001"
            }
        }
    }
    return users_db

def validate_email(email):
    """Basic email validation"""
    return "@" in email and "." in email

def register_new_user(email, password, user_data):
    """Register new user"""
    users_db = load_user_database()
    
    if email in users_db:
        return False, "Email already registered"
    
    if not validate_email(email):
        return False, "Invalid email format"
    
    if len(password) < 6:
        return False, "Password must be at least 6 characters"
    
    # Add new user
    users_db[email] = {
        "password": hash_password(password),
        "role": "practitioner",
        "profile": user_data
    }
    
    # In production, save to database
    st.session_state.user_profiles = users_db
    return True, "Registration successful"

def login_user(email, password):
    """Authenticate user login"""
    users_db = load_user_database()
    
    if email not in users_db:
        return False, "User not found"
    
    if users_db[email]["password"] != hash_password(password):
        return False, "Invalid password"
    
    # Set session state
    st.session_state.authenticated = True
    st.session_state.current_user = email
    st.session_state.user_role = users_db[email]["role"]
    st.session_state.current_page = "Dashboard"
    
    return True, "Login successful"

# ===== PATIENT MANAGEMENT SYSTEM =====
def generate_patient_id():
    """Generate unique patient ID"""
    return f"PAT{datetime.now().strftime('%Y%m%d%H%M%S')}"

def add_new_patient(patient_data):
    """Add new patient to database"""
    patient_id = generate_patient_id()
    
    patient_record = {
        "patient_id": patient_id,
        "created_by": st.session_state.current_user,
        "created_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "personal_info": patient_data,
        "ear_analyses": [],
        "medical_history": []
    }
    
    # Add to session state
    if st.session_state.current_user not in st.session_state.patients_data:
        st.session_state.patients_data[st.session_state.current_user] = {}
    
    st.session_state.patients_data[st.session_state.current_user][patient_id] = patient_record
    return patient_id

def save_ear_analysis(patient_id, image_file, analysis_results):
    """Save ear analysis for patient"""
    analysis_id = f"ANA{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    analysis_record = {
        "analysis_id": analysis_id,
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "image_filename": image_file.name,
        "image_size": Image.open(image_file).size,
        "results": analysis_results
    }
    
    # Add to patient record
    user_patients = st.session_state.patients_data[st.session_state.current_user]
    if patient_id in user_patients:
        user_patients[patient_id]["ear_analyses"].append(analysis_record)
    
    return analysis_id

def get_user_patients():
    """Get all patients for current user"""
    if st.session_state.current_user in st.session_state.patients_data:
        return st.session_state.patients_data[st.session_state.current_user]
    return {}

# ===== EAR REFLEXOLOGY MAPPING =====
EAR_REFLEXOLOGY_MAP = {
    "earlobe": ["Head", "Brain", "Eye", "Ear", "Teeth", "Jaw"],
    "helix_rim": ["Spine", "Back", "Neck", "Shoulders", "Nervous System"],
    "anti_helix": ["Internal Organs", "Chest", "Abdomen", "Digestive System"],
    "tragus": ["Throat", "Thyroid", "Respiratory", "Sinuses"],
    "anti_tragus": ["Heart", "Circulation", "Blood Pressure", "Cardiovascular"],
    "concha": ["Digestive System", "Liver", "Kidneys", "Intestines", "Metabolism"],
    "scapha": ["Arms", "Hands", "Fingers", "Joints", "Muscles"],
    "lobule": ["Legs", "Feet", "Knees", "Hips", "Bones"]
}

EAR_SIGNS_DISEASE_CORRELATION = {
    "redness": ["Inflammation", "Infection", "Allergic Reaction", "Fever"],
    "pallor": ["Anemia", "Poor Circulation", "Fatigue", "Low Blood Pressure"],
    "cyanosis": ["Respiratory Issues", "Heart Problems", "Poor Oxygenation"],
    "swelling": ["Fluid Retention", "Inflammation", "Lymph Issues", "Allergies"],
    "flakiness": ["Skin Disorders", "Nutritional Deficiency", "Eczema", "Dehydration"],
    "lesions": ["Chronic Conditions", "Autoimmune Issues", "Metabolic Disorders"],
    "discoloration": ["Toxin Buildup", "Organ Stress", "Metabolic Imbalance"],
    "vein_prominence": ["Cardiovascular Strain", "Hypertension", "Circulation Issues"]
}

# ===== AI ANALYSIS FUNCTIONS =====
def analyze_ear_zones(img_array):
    """Detect and analyze different ear reflexology zones"""
    try:
        zones_detected = []
        height, width = img_array.shape[:2]
        
        if height > width * 0.8:
            zones_detected.append("earlobe")
        
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array
            
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges) / (width * height)
        
        if edge_density > 0.1:
            zones_detected.append("helix_rim")
        
        brightness = np.mean(gray)
        if brightness > 100:
            zones_detected.append("concha")
            
        return zones_detected if zones_detected else ["general_ear_structure"]
    except Exception as e:
        return ["analysis_error"]

def analyze_ear_coloration(img_array):
    """Analyze color patterns in ear for health indications"""
    try:
        color_analysis = {}
        
        if len(img_array.shape) == 3:
            hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)
            
            red_mask = cv2.inRange(hsv, (0, 50, 50), (10, 255, 255))
            redness_percentage = np.sum(red_mask > 0) / (img_array.shape[0] * img_array.shape[1])
            if redness_percentage > 0.1:
                color_analysis["redness"] = f"{redness_percentage:.1%} - Possible inflammation"
            
            value_channel = hsv[:,:,2]
            if np.mean(value_channel) > 180:
                color_analysis["pallor"] = "Paleness detected - Check circulation"
            
            blue_mask = cv2.inRange(hsv, (100, 50, 50), (130, 255, 255))
            blue_percentage = np.sum(blue_mask > 0) / (img_array.shape[0] * img_array.shape[1])
            if blue_percentage > 0.05:
                color_analysis["cyanosis"] = f"{blue_percentage:.1%} - Check oxygenation"
                
        return color_analysis
    except Exception as e:
        return {"error": "Color analysis failed"}

def analyze_ear_texture(img_array):
    """Analyze skin texture for health clues"""
    try:
        texture_analysis = {}
        
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array
            
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        if laplacian_var < 100:
            texture_analysis["smoothness"] = "Very smooth - Possible nutritional issues"
        elif laplacian_var > 500:
            texture_analysis["roughness"] = "Rough texture - Check for skin conditions"
        
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges) / (gray.shape[0] * gray.shape[1])
        if edge_density > 0.15:
            texture_analysis["flakiness"] = "Flaky texture detected"
            
        return texture_analysis
    except Exception as e:
        return {"error": "Texture analysis failed"}

def detect_structural_features(img_array):
    """Detect structural features in ear"""
    try:
        features = []
        
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array
            
        edges = cv2.Canny(gray, 30, 100)
        line_density = np.sum(edges) / (gray.shape[0] * gray.shape[1])
        if line_density > 0.2:
            features.append("Prominent vascular patterns")
        
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if len(contours) > 5:
            features.append("Complex structural patterns")
            
        return features
    except Exception as e:
        return ["Feature detection failed"]

def correlate_with_systemic_health(analysis):
    """Correlate ear findings with potential systemic health issues"""
    
    health_insights = {
        'potential_concerns': [],
        'recommended_checks': [],
        'lifestyle_suggestions': [],
        'confidence_level': 'moderate',
        'detected_zones': analysis.get('detected_zones', []),
        'color_findings': analysis.get('color_analysis', {}),
        'texture_findings': analysis.get('texture_analysis', {}),
        'structural_findings': analysis.get('structural_features', [])
    }
    
    for color, finding in analysis.get('color_analysis', {}).items():
        if color == "redness":
            health_insights['potential_concerns'].extend([
                "Inflammatory conditions",
                "Possible infection",
                "Allergic reactions"
            ])
            health_insights['recommended_checks'].append("Inflammation markers")
            
        elif color == "pallor":
            health_insights['potential_concerns'].extend([
                "Anemia possibility", 
                "Circulatory issues",
                "Nutritional deficiencies"
            ])
            health_insights['recommended_checks'].append("Complete blood count")
            
        elif color == "cyanosis":
            health_insights['potential_concerns'].extend([
                "Respiratory function check",
                "Cardiovascular assessment",
                "Oxygen saturation levels"
            ])
            health_insights['recommended_checks'].append("Pulse oximetry")
    
    for texture, finding in analysis.get('texture_analysis', {}).items():
        if texture == "roughness":
            health_insights['potential_concerns'].append("Skin health assessment")
            health_insights['lifestyle_suggestions'].append("Increase hydration")
            
        elif texture == "flakiness":
            health_insights['potential_concerns'].append("Nutritional status check")
            health_insights['lifestyle_suggestions'].extend([
                "Essential fatty acids",
                "Vitamin E rich foods"
            ])
    
    for feature in analysis.get('structural_features', []):
        if "vascular" in feature.lower():
            health_insights['potential_concerns'].append("Circulatory system evaluation")
            health_insights['recommended_checks'].append("Blood pressure monitoring")
    
    health_insights['potential_concerns'] = list(set(health_insights['potential_concerns']))
    health_insights['recommended_checks'] = list(set(health_insights['recommended_checks']))
    health_insights['lifestyle_suggestions'] = list(set(health_insights['lifestyle_suggestions']))
    
    return health_insights

def analyze_systemic_health_via_ear(image):
    """Analyze ear structure for systemic health indications"""
    img_array = np.array(image)
    
    analysis = {
        'detected_zones': analyze_ear_zones(img_array),
        'color_analysis': analyze_ear_coloration(img_array),
        'texture_analysis': analyze_ear_texture(img_array),
        'structural_features': detect_structural_features(img_array)
    }
    
    health_insights = correlate_with_systemic_health(analysis)
    return health_insights

# ===== PAGE FUNCTIONS =====
def login_page():
    """Login and registration page"""
    st.title("🔐 Pinnalogy AI Professional")
    st.subheader("Ear Reflexology Analysis System")
    
    tab1, tab2 = st.tabs(["🚪 Login", "📝 Register"])
    
    with tab1:
        st.subheader("Practitioner Login")
        
        with st.form("login_form"):
            email = st.text_input("📧 Email Address", placeholder="your@email.com")
            password = st.text_input("🔑 Password", type="password")
            login_button = st.form_submit_button("🚀 Login", use_container_width=True)
            
            if login_button:
                if email and password:
                    success, message = login_user(email, password)
                    if success:
                        st.success(f"Welcome back! {message}")
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.error("Please fill in all fields")
        
        st.markdown("---")
        st.info("**Demo Account:** admin@pinnalogy.com / admin123")
    
    with tab2:
        st.subheader("New Practitioner Registration")
        
        with st.form("register_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                full_name = st.text_input("👤 Full Name", placeholder="Dr. John Smith")
                clinic_name = st.text_input("🏥 Clinic Name", placeholder="Your Clinic Name")
                email = st.text_input("📧 Email Address", placeholder="your@email.com")
                
            with col2:
                phone = st.text_input("📞 Phone Number", placeholder="+6012-3456789")
                license_number = st.text_input("📄 License Number", placeholder="MED-12345")
                password = st.text_input("🔑 Password", type="password")
                confirm_password = st.text_input("✅ Confirm Password", type="password")
            
            agree_terms = st.checkbox("I agree to the Terms of Service and Privacy Policy")
            
            register_button = st.form_submit_button("📝 Create Account", use_container_width=True)
            
            if register_button:
                if not all([full_name, clinic_name, email, phone, license_number, password, confirm_password]):
                    st.error("Please fill in all fields")
                elif password != confirm_password:
                    st.error("Passwords do not match")
                elif len(password) < 6:
                    st.error("Password must be at least 6 characters")
                elif not agree_terms:
                    st.error("Please agree to the terms and conditions")
                else:
                    user_data = {
                        "full_name": full_name,
                        "clinic_name": clinic_name,
                        "phone": phone,
                        "license_number": license_number
                    }
                    
                    success, message = register_new_user(email, password, user_data)
                    if success:
                        st.success("Account created successfully! Please login.")
                    else:
                        st.error(message)

def dashboard_page():
    """Main dashboard after login"""
    st.header(f"🏠 Welcome, {st.session_state.current_user}")
    
    # User info
    users_db = load_user_database()
    user_profile = users_db[st.session_state.current_user]["profile"]
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Patients", len(get_user_patients()))
    
    with col2:
        st.metric("Today's Analyses", "0")
    
    with col3:
        st.metric("System Status", "🟢 Online")
    
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
        if st.button("📊 Reports", use_container_width=True):
            st.session_state.current_page = "Reports"
            st.rerun()
    
    # Recent activity
    st.subheader("📈 Recent Activity")
    patients = get_user_patients()
    if patients:
        recent_patients = list(patients.values())[-5:]  # Last 5 patients
        for patient in recent_patients:
            with st.expander(f"👤 {patient['personal_info'].get('name', 'Unknown')} - {patient['patient_id']}"):
                st.write(f"**Created:** {patient['created_date']}")
                st.write(f"**Analyses:** {len(patient['ear_analyses'])}")
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
                name = st.text_input("Full Name *", placeholder="Ahmad bin Abdullah")
                ic_number = st.text_input("IC/Passport Number *", placeholder="901231-01-1234")
                phone = st.text_input("Phone Number", placeholder="+6012-3456789")
                email = st.text_input("Email Address", placeholder="patient@email.com")
                
            with col2:
                gender = st.selectbox("Gender *", ["Male", "Female", "Other"])
                age = st.number_input("Age *", min_value=1, max_value=120, value=30)
                blood_type = st.selectbox("Blood Type", ["Unknown", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"])
                emergency_contact = st.text_input("Emergency Contact", placeholder="+6012-3456789")
            
            medical_history = st.text_area("Medical History", placeholder="Previous conditions, allergies, medications...")
            notes = st.text_area("Additional Notes", placeholder="Any other relevant information...")
            
            submit_button = st.form_submit_button("💾 Save Patient Record", use_container_width=True)
            
            if submit_button:
                if not all([name, ic_number, gender, age]):
                    st.error("Please fill in all required fields (*)")
                else:
                    patient_data = {
                        "name": name,
                        "ic_number": ic_number,
                        "phone": phone,
                        "email": email,
                        "gender": gender,
                        "age": age,
                        "blood_type": blood_type,
                        "emergency_contact": emergency_contact,
                        "medical_history": medical_history,
                        "notes": notes
                    }
                    
                    patient_id = add_new_patient(patient_data)
                    st.success(f"Patient registered successfully! ID: {patient_id}")
    
    with tab2:
        st.subheader("Patient Records")
        
        patients = get_user_patients()
        if patients:
            for patient_id, patient in patients.items():
                with st.expander(f"👤 {patient['personal_info']['name']} - {patient_id}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Personal Information:**")
                        st.write(f"IC: {patient['personal_info']['ic_number']}")
                        st.write(f"Age: {patient['personal_info']['age']}")
                        st.write(f"Gender: {patient['personal_info']['gender']}")
                        st.write(f"Blood Type: {patient['personal_info']['blood_type']}")
                    
                    with col2:
                        st.write("**Contact:**")
                        st.write(f"Phone: {patient['personal_info']['phone']}")
                        st.write(f"Email: {patient['personal_info']['email']}")
                        st.write(f"Emergency: {patient['personal_info']['emergency_contact']}")
                        st.write(f"Analyses: {len(patient['ear_analyses'])}")
                    
                    if st.button(f"🔍 Analyze Ear", key=patient_id):
                        st.session_state.selected_patient = patient_id
                        st.session_state.current_page = "Ear Analysis"
                        st.rerun()

def ear_analysis_page():
    """Ear analysis with patient selection"""
    st.header("🔍 Ear Analysis")
    
    patients = get_user_patients()
    
    if not patients:
        st.warning("No patients found. Please add a patient first.")
        if st.button("➕ Add New Patient"):
            st.session_state.current_page = "Patient Management"
            st.rerun()
        return
    
    # Patient selection
    patient_options = {pid: f"{data['personal_info']['name']} ({pid})" for pid, data in patients.items()}
    selected_patient = st.selectbox("👤 Select Patient", options=list(patient_options.keys()), 
                                  format_func=lambda x: patient_options[x])
    
    if selected_patient:
        patient_info = patients[selected_patient]['personal_info']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Patient Information")
            st.write(f"**Name:** {patient_info['name']}")
            st.write(f"**Age:** {patient_info['age']}")
            st.write(f"**Gender:** {patient_info['gender']}")
            st.write(f"**IC:** {patient_info['ic_number']}")
        
        with col2:
            st.subheader("Upload Ear Image")
            uploaded_file = st.file_uploader(
                "📷 Upload Clear Ear Image",
                type=['jpg', 'jpeg', 'png'],
                key=f"upload_{selected_patient}"
            )
            
            if uploaded_file is not None:
                image = Image.open(uploaded_file)
                st.image(image, caption="Uploaded Ear Image", use_column_width=True)
                
                if st.button("🧠 Analyze Ear", type="primary", use_container_width=True):
                    with st.spinner("🤖 AI is analyzing ear reflexology patterns..."):
                        time.sleep(2)
                        
                        analysis_results = analyze_systemic_health_via_ear(image)
                        analysis_id = save_ear_analysis(selected_patient, uploaded_file, analysis_results)
                        
                        st.success(f"Analysis completed! Record ID: {analysis_id}")
                        
                        # Display results
                        display_analysis_results(analysis_results, patient_info)

def display_analysis_results(insights, patient_info):
    """Display analysis results"""
    st.subheader("🎯 Analysis Results")
    
    st.write(f"**Patient:** {patient_info['name']} | **Age:** {patient_info['age']} | **Gender:** {patient_info['gender']}")
    
    if insights['detected_zones']:
        st.write("**📍 Detected Ear Zones:**")
        for zone in insights['detected_zones']:
            related_organs = EAR_REFLEXOLOGY_MAP.get(zone, ["General area"])
            st.write(f"• **{zone.title()}**: {', '.join(related_organs)}")
    
    if insights['color_findings']:
        st.write("**🎨 Color Analysis:**")
        for color, finding in insights['color_findings'].items():
            st.write(f"• **{color.title()}**: {finding}")
    
    if insights['potential_concerns']:
        st.warning("⚠️ **Areas for Further Investigation:**")
        for concern in insights['potential_concerns']:
            st.write(f"• {concern}")
    
    if insights['recommended_checks']:
        st.info("🩺 **Recommended Health Checks:**")
        for check in insights['recommended_checks']:
            st.write(f"• {check}")
    
    # Save report option
    if st.button("💾 Save Analysis Report"):
        st.success("Report saved to patient record!")

def reports_page():
    """Reports and analytics"""
    st.header("📊 Reports & Analytics")
    
    patients = get_user_patients()
    total_analyses = sum(len(patient['ear_analyses']) for patient in patients.values())
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Patients", len(patients))
    
    with col2:
        st.metric("Total Analyses", total_analyses)
    
    with col3:
        st.metric("Average per Patient", f"{total_analyses/len(patients):.1f}" if patients else "0")
    
    # Analysis history
    st.subheader("📈 Analysis History")
    if patients:
        for patient_id, patient in patients.items():
            if patient['ear_analyses']:
                with st.expander(f"👤 {patient['personal_info']['name']} - {len(patient['ear_analyses'])} analyses"):
                    for analysis in patient['ear_analyses']:
                        st.write(f"**{analysis['timestamp']}** - {analysis['image_filename']}")
    else:
        st.info("No analysis data available")

def logout_button():
    """Logout button in sidebar"""
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.current_user = None
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
        
        # Navigation menu
        page = st.sidebar.radio(
            "Navigate to:",
            ["Dashboard", "Patient Management", "Ear Analysis", "Reports"],
            index=["Dashboard", "Patient Management", "Ear Analysis", "Reports"].index(st.session_state.current_page)
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
        
        # Logout button
        st.sidebar.markdown("---")
        logout_button()
        
        # Footer
        st.sidebar.info("**Professional Edition** v2.0")

if __name__ == "__main__":
    main()
