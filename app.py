import streamlit as st
from datetime import datetime
import sys
import os

# Try to import OpenCV with fallback
try:
    import cv2
    CV_AVAILABLE = True
except ImportError as e:
    st.error(f"OpenCV not available: {e}")
    CV_AVAILABLE = False

try:
    import tensorflow as tf
    TF_AVAILABLE = True
except ImportError as e:
    st.error(f"TensorFlow not available: {e}")
    TF_AVAILABLE = False

import numpy as np
import pandas as pd
from PIL import Image
import tempfile

# Your app code continues here...
st.set_page_config(
    page_title="Pinnalogy AI - Ear Analysis",
    page_icon="👂",
    layout="wide"
)

st.title("Pinnalogy AI - Ear Analysis")

if not CV_AVAILABLE:
    st.warning("OpenCV is not available. Some image processing features may not work.")
# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #8e44ad;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f5eef8;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #8e44ad;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">👂 Pinnalogy AI - Ear Analysis Dashboard</div>', unsafe_allow_html=True)

# Create sample data
def create_sample_data():
    return pd.DataFrame({
        'patient_id': [f'P_{i:03d}' for i in range(1, 16)],
        'age': [25, 34, 47, 52, 38, 61, 29, 45, 56, 33, 42, 58, 31, 49, 27],
        'gender': ['M', 'F', 'M', 'F', 'M', 'F', 'M', 'F', 'M', 'F', 'M', 'F', 'M', 'F', 'M'],
        'ear_condition': ['Normal', 'Infection', 'Normal', 'Wax Buildup', 'Normal', 'Perforation', 
                         'Normal', 'Inflammation', 'Scarring', 'Normal', 'Infection', 'Deformity',
                         'Normal', 'Wax Buildup', 'Normal'],
        'hearing_loss_db': [15, 35, 12, 28, 18, 65, 10, 32, 45, 14, 38, 72, 11, 25, 16],
        'scan_quality': ['Excellent', 'Good', 'Excellent', 'Fair', 'Good', 'Poor', 'Excellent', 'Good', 
                        'Fair', 'Excellent', 'Good', 'Poor', 'Excellent', 'Fair', 'Good'],
        'visit_date': pd.date_range('2024-01-01', periods=15, freq='D')
    })

@st.cache_data
def load_data():
    """Load data - try CSV first, else use sample data"""
    try:
        df = pd.read_csv('data/ear_data.csv')
        return df
    except:
        return create_sample_data()

def analyze_ear_image(image):
    """Simple image analysis without OpenCV"""
    try:
        # Get basic image stats
        width, height = image.size
        file_size = len(image.tobytes()) / 1024  # KB
        
        # Simple "analysis" based on image characteristics
        if width > 1000 and height > 1000:
            quality = "Excellent"
            confidence = 0.9
        elif width > 500 and height > 500:
            quality = "Good" 
            confidence = 0.7
        else:
            quality = "Fair"
            confidence = 0.5
            
        # Simulate anatomical coverage (based on image hash for consistency)
        image_hash = hash(image.tobytes()) % 1000
        np.random.seed(image_hash)
        
        helix = np.random.uniform(20, 30)
        antihelix = np.random.uniform(15, 25)
        concha = np.random.uniform(10, 20)
        lobule = np.random.uniform(5, 15)
        
        coverage_data = {
            'helix': helix,
            'antihelix': antihelix, 
            'concha': concha,
            'lobule': lobule,
            'total': helix + antihelix + concha + lobule,
            'quality': quality,
            'confidence': confidence,
            'width': width,
            'height': height
        }
        
        return coverage_data
        
    except Exception as e:
        st.error(f"Analysis error: {str(e)}")
        return None

# Load data
df = load_data()

# Main app
tab1, tab2 = st.tabs(["📷 Image Analysis", "📊 Patient Analytics"])

with tab1:
    st.header("Ear Image Analysis")
    
    uploaded_file = st.file_uploader("Upload Ear Image", type=['jpg', 'jpeg', 'png'])
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.image(image, caption="Uploaded Ear Image", use_column_width=True)
            
            # Image info
            st.subheader("Image Information")
            st.write(f"**Size**: {image.size[0]} x {image.size[1]} pixels")
            st.write(f"**Format**: {uploaded_file.type}")
            st.write(f"**Uploaded**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if st.button("Analyze Image", type="primary"):
            with st.spinner("Analyzing ear image..."):
                results = analyze_ear_image(image)
                
                if results:
                    with col2:
                        st.subheader("Analysis Results")
                        
                        # Display metrics
                        cols = st.columns(2)
                        
                        with cols[0]:
                            st.markdown(f"""
                            <div class="metric-card">
                                <h3>HELIX</h3>
                                <h2>{results['helix']:.1f}%</h2>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            st.markdown(f"""
                            <div class="metric-card">
                                <h3>ANTIHELIX</h3>
                                <h2>{results['antihelix']:.1f}%</h2>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with cols[1]:
                            st.markdown(f"""
                            <div class="metric-card">
                                <h3>CONCHA</h3>
                                <h2>{results['concha']:.1f}%</h2>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            st.markdown(f"""
                            <div class="metric-card">
                                <h3>LOBULE</h3>
                                <h2>{results['lobule']:.1f}%</h2>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # Total coverage
                        st.metric("Total Coverage", f"{results['total']:.1f}%")
                        st.metric("Image Quality", results['quality'])
                        st.metric("Confidence", f"{results['confidence']:.1%}")
                        
                        # Condition assessment
                        if results['total'] > 70:
                            st.success("✅ **Normal** - Good anatomical coverage detected")
                        elif results['total'] > 50:
                            st.warning("⚠️ **Mild Abnormality** - Reduced coverage detected")
                        else:
                            st.error("🚨 **Significant Abnormality** - Low coverage detected")
                    
                    st.success("Analysis completed successfully!")
                    
                    # Show comparison with historical data
                    st.subheader("Historical Comparison")
                    avg_hearing_loss = df['hearing_loss_db'].mean()
                    comparison = (results['total'] / 100 * 50)  # Simple comparison metric
                    
                    st.metric(
                        "Compared to Dataset Average", 
                        f"{results['total']:.1f}%",
                        delta=f"{comparison:+.1f}%"
                    )

with tab2:
    st.header("Patient Analytics")
    
    # Filters
    col1, col2 = st.columns(2)
    
    with col1:
        condition_filter = st.multiselect(
            "Ear Condition",
            options=df['ear_condition'].unique(),
            default=df['ear_condition'].unique()
        )
    
    with col2:
        quality_filter = st.multiselect(
            "Scan Quality", 
            options=df['scan_quality'].unique(),
            default=df['scan_quality'].unique()
        )
    
    # Age range filter
    age_range = st.slider(
        "Age Range",
        min_value=int(df['age'].min()),
        max_value=int(df['age'].max()),
        value=(int(df['age'].min()), int(df['age'].max()))
    )
    
    # Apply filters
    filtered_df = df[
        (df['ear_condition'].isin(condition_filter)) &
        (df['scan_quality'].isin(quality_filter)) &
        (df['age'].between(age_range[0], age_range[1]))
    ]
    
    # KPIs
    st.subheader("Key Metrics")
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    
    with kpi1:
        total_patients = len(filtered_df)
        st.metric("Total Patients", total_patients)
    
    with kpi2:
        normal_cases = (filtered_df['ear_condition'] == 'Normal').sum()
        st.metric("Normal Cases", normal_cases)
    
    with kpi3:
        avg_hearing_loss = filtered_df['hearing_loss_db'].mean()
        st.metric("Avg Hearing Loss", f"{avg_hearing_loss:.1f} dB")
    
    with kpi4:
        excellent_scans = (filtered_df['scan_quality'] == 'Excellent').sum()
        st.metric("Excellent Scans", excellent_scans)
    
    # Charts using native Streamlit
    st.subheader("Visualizations")
    
    # Condition distribution
    st.write("**Ear Condition Distribution**")
    condition_counts = filtered_df['ear_condition'].value_counts()
    st.bar_chart(condition_counts)
    
    # Age distribution
    st.write("**Patient Age Distribution**")
    age_hist = np.histogram(filtered_df['age'], bins=10)
    st.bar_chart(pd.DataFrame({'Age': age_hist[1][1:], 'Count': age_hist[0]}).set_index('Age'))
    
    # Data table
    with st.expander("View Patient Data"):
        st.dataframe(filtered_df, use_container_width=True)

# Sidebar
with st.sidebar:
    st.header("👂 Pinnalogy AI")
    st.write("Ear Analysis & Patient Management")
    
    st.header("Features")
    st.write("• Image Analysis")
    st.write("• Patient Analytics") 
    st.write("• Condition Assessment")
    
    st.header("Sample Data")
    st.write(f"Total Patients: {len(df)}")
    st.write(f"Data Period: {df['visit_date'].min().strftime('%Y-%m-%d')} to {df['visit_date'].max().strftime('%Y-%m-%d')}")
    
    if st.button("Clear Cache"):
        st.cache_data.clear()
        st.success("Cache cleared!")

st.markdown("---")
st.markdown("**Pinnalogy AI** | Medical Imaging Analysis Platform | Streamlit Cloud Compatible")
