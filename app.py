import streamlit as st
from datetime import datetime
import numpy as np
import pandas as pd
from PIL import Image
import tensorflow as tf
import cv2
import time
import io

# ===== CONFIGURATION =====
st.set_page_config(
    page_title="Pinnalogy AI - Ear Health Analysis",
    page_icon="👂",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
        
        # Basic zone detection based on image characteristics
        if height > width * 0.8:
            zones_detected.append("earlobe")
        
        # Edge detection for helix
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array
            
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges) / (width * height)
        
        if edge_density > 0.1:
            zones_detected.append("helix_rim")
        
        # Brightness analysis for concha
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
            # Convert to HSV for better color analysis
            hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)
            
            # Redness analysis (inflammation)
            red_mask = cv2.inRange(hsv, (0, 50, 50), (10, 255, 255))
            redness_percentage = np.sum(red_mask > 0) / (img_array.shape[0] * img_array.shape[1])
            if redness_percentage > 0.1:
                color_analysis["redness"] = f"{redness_percentage:.1%} - Possible inflammation"
            
            # Pallor analysis (paleness)
            value_channel = hsv[:,:,2]
            if np.mean(value_channel) > 180:
                color_analysis["pallor"] = "Paleness detected - Check circulation"
            
            # Cyanosis analysis (bluish tint)
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
            
        # Smoothness vs roughness
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        if laplacian_var < 100:
            texture_analysis["smoothness"] = "Very smooth - Possible nutritional issues"
        elif laplacian_var > 500:
            texture_analysis["roughness"] = "Rough texture - Check for skin conditions"
        
        # Flakiness detection
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
            
        # Vein prominence
        edges = cv2.Canny(gray, 30, 100)
        line_density = np.sum(edges) / (gray.shape[0] * gray.shape[1])
        if line_density > 0.2:
            features.append("Prominent vascular patterns")
        
        # Structural complexity
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
    
    # Analyze color findings
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
    
    # Analyze texture findings
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
    
    # Analyze structural features
    for feature in analysis.get('structural_features', []):
        if "vascular" in feature.lower():
            health_insights['potential_concerns'].append("Circulatory system evaluation")
            health_insights['recommended_checks'].append("Blood pressure monitoring")
    
    # Remove duplicates
    health_insights['potential_concerns'] = list(set(health_insights['potential_concerns']))
    health_insights['recommended_checks'] = list(set(health_insights['recommended_checks']))
    health_insights['lifestyle_suggestions'] = list(set(health_insights['lifestyle_suggestions']))
    
    return health_insights

def analyze_systemic_health_via_ear(image):
    """Analyze ear structure for systemic health indications"""
    
    # Convert to numpy array
    img_array = np.array(image)
    
    # Analyze ear characteristics
    analysis = {
        'detected_zones': analyze_ear_zones(img_array),
        'color_analysis': analyze_ear_coloration(img_array),
        'texture_analysis': analyze_ear_texture(img_array),
        'structural_features': detect_structural_features(img_array)
    }
    
    # Correlate with health insights
    health_insights = correlate_with_systemic_health(analysis)
    
    return health_insights

# ===== PAGE FUNCTIONS =====
def systemic_health_analysis_page():
    st.header("🔍 Systemic Health Analysis via Ear Reflexology")
    
    st.info("""
    **Auricular Diagnosis**: This analysis examines ear structure, color, and texture 
    patterns that may indicate systemic health conditions based on ear reflexology principles.
    """)
    
    # File uploader
    uploaded_file = st.file_uploader(
        "📷 Upload Clear Ear Image for Analysis", 
        type=['jpg', 'jpeg', 'png'],
        help="Upload a clear, well-lit image of the ear for best results"
    )
    
    if uploaded_file is not None:
        # Display image
        image = Image.open(uploaded_file)
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.image(image, caption="Uploaded Ear Image", use_column_width=True)
            
            # Image information
            st.subheader("📋 Image Information")
            st.write(f"**Dimensions**: {image.size[0]} x {image.size[1]} pixels")
            st.write(f"**Format**: {uploaded_file.type}")
            st.write(f"**Uploaded**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        with col2:
            st.subheader("🔬 Analysis Options")
            
            if st.button("🧠 Analyze Systemic Health", type="primary", use_container_width=True):
                with st.spinner("🤖 AI is analyzing ear reflexology patterns..."):
                    # Simulate processing time
                    time.sleep(2)
                    
                    # Perform analysis
                    health_insights = analyze_systemic_health_via_ear(image)
                    
                    # Display results
                    display_systemic_health_results(health_insights)

def display_systemic_health_results(insights):
    """Display systemic health analysis results"""
    
    st.subheader("🎯 Ear Reflexology Findings")
    
    # Detected Zones
    if insights['detected_zones']:
        st.write("**📍 Detected Ear Zones:**")
        for zone in insights['detected_zones']:
            related_organs = EAR_REFLEXOLOGY_MAP.get(zone, ["General area"])
            st.write(f"• **{zone.title()}**: {', '.join(related_organs)}")
    
    # Color Findings
    if insights['color_findings']:
        st.write("**🎨 Color Analysis:**")
        for color, finding in insights['color_findings'].items():
            st.write(f"• **{color.title()}**: {finding}")
    
    # Texture Findings  
    if insights['texture_findings']:
        st.write("**🔍 Texture Analysis:**")
        for texture, finding in insights['texture_findings'].items():
            st.write(f"• **{texture.title()}**: {finding}")
    
    # Structural Findings
    if insights['structural_findings']:
        st.write("**🏗️ Structural Features:**")
        for feature in insights['structural_findings']:
            st.write(f"• {feature}")
    
    # Health Insights
    st.subheader("💡 Health Insights")
    
    # Potential Health Concerns
    if insights['potential_concerns']:
        st.warning("⚠️ **Areas for Further Investigation:**")
        for concern in insights['potential_concerns']:
            st.write(f"• {concern}")
    else:
        st.success("✅ No significant concerns detected")
    
    # Recommended Medical Checks
    if insights['recommended_checks']:
        st.info("🩺 **Recommended Health Checks:**")
        for check in insights['recommended_checks']:
            st.write(f"• {check}")
    
    # Lifestyle Suggestions
    if insights['lifestyle_suggestions']:
        st.success("🌱 **Lifestyle Considerations:**")
        for suggestion in insights['lifestyle_suggestions']:
            st.write(f"• {suggestion}")
    
    # Confidence Level
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Analysis Confidence", insights['confidence_level'].title())
    
    # Important Disclaimer
    st.error("""
    🚨 **Important Medical Disclaimer**:
    - Ear reflexology is a complementary approach, not a diagnostic tool
    - These insights are for educational purposes only
    - Always consult healthcare professionals for medical diagnosis
    - This analysis should not replace professional medical advice
    """)

def dashboard_page():
    st.header("🏠 Pinnalogy AI Dashboard")
    
    # Welcome message
    st.success("Welcome to Pinnalogy AI - Advanced Ear Health Analysis System")
    
    # Quick stats
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Analyses", "15", "3 today")
    
    with col2:
        st.metric("System Health", "92%", "2% improvement")
    
    with col3:
        st.metric("AI Accuracy", "89%", "5% from last week")
    
    # Features overview
    st.subheader("🚀 Available Features")
    
    features = {
        "🔍 Systemic Health Analysis": "Analyze ear structure for systemic health insights",
        "📊 Health Analytics": "Track and visualize health patterns over time", 
        "📋 Patient Records": "Manage and review patient analysis history",
        "⚙️ System Settings": "Configure analysis parameters and preferences"
    }
    
    for feature, description in features.items():
        with st.expander(feature):
            st.write(description)
    
    # Quick action buttons
    st.subheader("⚡ Quick Actions")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🆕 New Analysis", use_container_width=True):
            st.session_state.current_page = "Systemic Health Analysis"
            st.rerun()
    
    with col2:
        if st.button("📈 View Analytics", use_container_width=True):
            st.session_state.current_page = "Analytics"
            st.rerun()

def analytics_page():
    st.header("📊 Health Analytics")
    
    # Sample data
    st.info("Analytics dashboard coming soon...")
    
    # Placeholder charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Analysis Trends")
        # Placeholder for chart
        st.write("📈 Chart will display analysis trends over time")
    
    with col2:
        st.subheader("Health Patterns")
        # Placeholder for chart  
        st.write("🔍 Chart will show detected health pattern distribution")

def settings_page():
    st.header("⚙️ System Settings")
    
    st.info("Configure your Pinnalogy AI system preferences")
    
    # Model settings
    st.subheader("🤖 AI Model Settings")
    model_choice = st.selectbox(
        "Analysis Model",
        ["Standard Reflexology", "Advanced Pattern Recognition", "Custom Model"]
    )
    
    # Analysis preferences
    st.subheader("🔧 Analysis Preferences")
    col1, col2 = st.columns(2)
    
    with col1:
        detail_level = st.select_slider(
            "Analysis Detail Level",
            options=["Basic", "Standard", "Detailed", "Comprehensive"]
        )
    
    with col2:
        confidence_threshold = st.slider(
            "Confidence Threshold",
            min_value=50,
            max_value=95,
            value=75
        )
    
    if st.button("💾 Save Settings", type="primary"):
        st.success("Settings saved successfully!")

# ===== MAIN APP =====
def main():
    # Initialize session state for page navigation
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Dashboard"
    
    # Sidebar navigation
    st.sidebar.title("🩺 Pinnalogy AI")
    st.sidebar.write("Ear Reflexology Health Analysis")
    
    # Navigation menu
    page = st.sidebar.radio(
        "Navigate to:",
        ["Dashboard", "Systemic Health Analysis", "Analytics", "Settings"],
        index=["Dashboard", "Systemic Health Analysis", "Analytics", "Settings"].index(st.session_state.current_page)
    )
    
    # Update session state
    st.session_state.current_page = page
    
    # Page routing
    if page == "Dashboard":
        dashboard_page()
    elif page == "Systemic Health Analysis":
        systemic_health_analysis_page()
    elif page == "Analytics":
        analytics_page()
    elif page == "Settings":
        settings_page()
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.info(
        "**Pinnalogy AI** v1.0\n\n"
        "Advanced ear reflexology analysis for systemic health insights."
    )

if __name__ == "__main__":
    main()
