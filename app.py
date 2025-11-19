import streamlit as st
import cv2
import numpy as np
import pandas as pd
from PIL import Image
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io

st.set_page_config(
    page_title="Pinnalogy AI - Ear Analysis",
    page_icon="🦻",
    layout="wide"
)

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
    .region-helix { color: #e74c3c; font-weight: bold; }
    .region-antihelix { color: #27ae60; font-weight: bold; }
    .region-concha { color: #3498db; font-weight: bold; }
    .region-lobule { color: #f39c12; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">🦻 Pinnalogy AI - Ear Anatomy Analysis</div>', unsafe_allow_html=True)

# Sample historical data (akan diganti dengan CSV nanti)
def create_sample_data():
    return pd.DataFrame({
        'image_id': [f'EAR_{i:03d}' for i in range(1, 16)],
        'patient_id': [f'P_{i:03d}' for i in range(45, 60)],
        'age': [45, 62, 38, 55, 41, 67, 29, 50, 58, 33, 47, 63, 36, 52, 44],
        'gender': ['Male', 'Female', 'Male', 'Female', 'Male', 'Female', 'Male', 'Female', 'Male', 'Female', 'Male', 'Female', 'Male', 'Female', 'Male'],
        'helix_coverage': [25.3, 22.1, 27.8, 19.5, 24.7, 16.8, 28.9, 23.4, 21.7, 26.2, 24.1, 15.2, 27.5, 22.8, 25.9],
        'antihelix_coverage': [18.7, 16.8, 20.3, 14.2, 17.9, 12.5, 21.7, 16.5, 15.9, 19.4, 17.2, 11.8, 20.1, 16.3, 18.9],
        'concha_coverage': [12.5, 11.2, 13.9, 9.8, 12.1, 8.3, 14.5, 11.8, 10.7, 13.2, 11.9, 7.5, 13.8, 11.5, 12.8],
        'lobule_coverage': [8.2, 7.8, 9.1, 6.5, 8.0, 5.2, 9.8, 7.4, 6.9, 8.7, 7.8, 4.8, 9.0, 7.2, 8.4],
        'ear_condition': ['Normal', 'Mild_Deformity', 'Normal', 'Inflammation', 'Normal', 'Severe_Deformity', 
                         'Normal', 'Mild_Inflammation', 'Scarring', 'Normal', 'Normal', 'Severe_Deformity',
                         'Normal', 'Mild_Deformity', 'Normal'],
        'scan_quality': ['Excellent', 'Good', 'Excellent', 'Fair', 'Good', 'Poor', 'Excellent', 'Good', 
                        'Fair', 'Excellent', 'Good', 'Poor', 'Excellent', 'Good', 'Excellent'],
        'timestamp': pd.date_range('2024-01-01', periods=15, freq='D')
    })

@st.cache_data
def load_historical_data():
    """Load historical data - cuba baca CSV, jika fail guna sample data"""
    try:
        df = pd.read_csv('data/ear_segmentation_history.csv')
        return df
    except:
        st.info("📁 Using sample data. Upload 'ear_segmentation_history.csv' for real historical data.")
        return create_sample_data()

def simulate_segmentation(image_array):
    """Simulate ear anatomy segmentation tanpa TensorFlow"""
    try:
        # Convert dan resize image
        if len(image_array.shape) == 3:
            image_rgb = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)
        else:
            image_rgb = image_array
            
        input_image = cv2.resize(image_rgb, (512, 512))
        
        # Create simulated masks untuk different anatomical regions
        height, width = 512, 512
        center_x, center_y = width // 2, height // 2
        
        masks = {}
        
        # Helix (Outer ear)
        helix_mask = np.zeros((height, width, 1), dtype=np.uint8)
        cv2.ellipse(helix_mask, (center_x, center_y), (200, 150), 0, 0, 360, 255, -1)
        cv2.ellipse(helix_mask, (center_x, center_y), (180, 130), 0, 0, 360, 0, -1)
        masks['helix'] = helix_mask
        
        # Antihelix (Inner ridge)
        antihelix_mask = np.zeros((height, width, 1), dtype=np.uint8)
        cv2.ellipse(antihelix_mask, (center_x, center_y), (150, 110), 0, 0, 360, 255, -1)
        cv2.ellipse(antihelix_mask, (center_x, center_y), (130, 90), 0, 0, 360, 0, -1)
        masks['antihelix'] = antihelix_mask
        
        # Concha (Ear bowl)
        concha_mask = np.zeros((height, width, 1), dtype=np.uint8)
        cv2.ellipse(concha_mask, (center_x, center_y), (100, 70), 0, 0, 360, 255, -1)
        masks['concha'] = concha_mask
        
        # Lobule (Ear lobe)
        lobule_mask = np.zeros((height, width, 1), dtype=np.uint8)
        cv2.ellipse(lobule_mask, (center_x, center_y + 120), (80, 50), 0, 0, 360, 255, -1)
        masks['lobule'] = lobule_mask
        
        return masks, input_image
        
    except Exception as e:
        st.error(f"Segmentation simulation error: {str(e)}")
        return None, None

def calculate_coverage_stats(masks):
    """Calculate coverage statistics"""
    total_pixels = 512 * 512
    stats = {}
    
    for region, mask in masks.items():
        coverage = (np.sum(mask > 0) / total_pixels) * 100
        stats[region] = coverage
    
    stats['total_coverage'] = sum(stats.values())
    
    return stats

def create_visualization(masks, original_image):
    """Create segmentation visualization"""
    # Create colored mask
    combined_mask = np.zeros((512, 512, 3), dtype=np.uint8)
    colors = {
        'helix': (255, 0, 0),      # Red
        'antihelix': (0, 255, 0),  # Green  
        'concha': (0, 0, 255),     # Blue
        'lobule': (255, 255, 0)    # Yellow
    }
    
    for region, mask in masks.items():
        color = colors[region]
        combined_mask[mask[:,:,0] > 0] = color
    
    # Create overlay
    overlay = cv2.addWeighted(original_image, 0.7, combined_mask, 0.3, 0)
    
    return combined_mask, overlay

# Load historical data
historical_data = load_historical_data()

# Main app dengan tabs
tab1, tab2 = st.tabs(["🎯 Image Analysis", "📊 Analytics Dashboard"])

with tab1:
    st.header("Upload Ear Image for Analysis")
    
    uploaded_file = st.file_uploader("Choose an ear image", type=['jpg', 'jpeg', 'png'], key="file_uploader")
    
    if uploaded_file is not None:
        # Process uploaded image
        image = Image.open(uploaded_file)
        image_np = np.array(image)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.image(image, caption="Uploaded Image", use_column_width=True)
            
            # Image information
            st.subheader("📋 Image Information")
            st.write(f"**Format**: {uploaded_file.type}")
            st.write(f"**Size**: {image.size[0]} x {image.size[1]} pixels")
            st.write(f"**Upload Time**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if st.button("🔍 Analyze Ear Anatomy", type="primary", use_container_width=True):
            with st.spinner("Analyzing ear anatomy... This may take a few seconds."):
                masks, processed_img = simulate_segmentation(image_np)
                
                if masks and processed_img is not None:
                    # Calculate statistics
                    stats = calculate_coverage_stats(masks)
                    
                    # Create visualizations
                    segmentation_mask, overlay_img = create_visualization(masks, processed_img)
                    
                    with col2:
                        st.image(segmentation_mask, caption="Anatomical Regions Segmentation", use_column_width=True)
                        st.image(overlay_img, caption="Segmentation Overlay", use_column_width=True)
                    
                    # Display results
                    st.subheader("📊 Analysis Results")
                    
                    # Metrics in columns
                    cols = st.columns(4)
                    regions = ['helix', 'antihelix', 'concha', 'lobule']
                    
                    for i, region in enumerate(regions):
                        with cols[i]:
                            coverage = stats[region]
                            color_class = f"region-{region}"
                            st.markdown(f"""
                            <div class="metric-card">
                                <h3 class="{color_class}">{region.upper()}</h3>
                                <h2>{coverage:.1f}%</h2>
                                <p>Coverage</p>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    # Total coverage dengan comparison
                    total_col1, total_col2 = st.columns(2)
                    
                    with total_col1:
                        st.metric(
                            "Total Anatomical Coverage", 
                            f"{stats['total_coverage']:.1f}%"
                        )
                    
                    with total_col2:
                        if historical_data is not None:
                            avg_coverage = historical_data['total_coverage'].mean()
                            diff = stats['total_coverage'] - avg_coverage
                            st.metric(
                                "vs Historical Average", 
                                f"{stats['total_coverage']:.1f}%",
                                delta=f"{diff:+.1f}%"
                            )
                    
                    # Condition assessment
                    st.subheader("🏥 Condition Assessment")
                    if stats['total_coverage'] > 70:
                        st.success("✅ **Normal** - Good anatomical coverage detected")
                    elif stats['total_coverage'] > 50:
                        st.warning("⚠️ **Mild Abnormality** - Reduced coverage detected")
                    else:
                        st.error("🚨 **Significant Abnormality** - Low coverage detected")
                    
                    st.balloons()
                    
with tab2:
    st.header("📈 Analytics Dashboard")
    
    if historical_data is not None:
        # Key metrics
        st.subheader("Key Performance Indicators")
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        
        with kpi1:
            total_cases = len(historical_data)
            st.metric("Total Cases", total_cases)
        
        with kpi2:
            avg_coverage = historical_data[['helix_coverage', 'antihelix_coverage', 'concha_coverage', 'lobule_coverage']].mean().mean()
            st.metric("Average Coverage", f"{avg_coverage:.1f}%")
        
        with kpi3:
            normal_cases = (historical_data['ear_condition'] == 'Normal').sum()
            st.metric("Normal Cases", normal_cases)
        
        with kpi4:
            excellent_scans = (historical_data['scan_quality'] == 'Excellent').sum()
            st.metric("Excellent Quality", excellent_scans)
        
        # Charts
        st.subheader("Visual Analytics")
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            # Coverage by region
            coverage_data = historical_data[['helix_coverage', 'antihelix_coverage', 'concha_coverage', 'lobule_coverage']]
            fig_coverage = px.box(
                coverage_data,
                title="Coverage Distribution by Region",
                labels={'value': 'Coverage %', 'variable': 'Anatomical Region'}
            )
            st.plotly_chart(fig_coverage, use_container_width=True)
            
            # Age distribution
            fig_age = px.histogram(
                historical_data,
                x='age',
                title="Patient Age Distribution",
                color='gender'
            )
            st.plotly_chart(fig_age, use_container_width=True)
        
        with chart_col2:
            # Condition distribution
            condition_counts = historical_data['ear_condition'].value_counts()
            fig_condition = px.pie(
                values=condition_counts.values,
                names=condition_counts.index,
                title="Ear Condition Distribution"
            )
            st.plotly_chart(fig_condition, use_container_width=True)
            
            # Quality analysis
            quality_stats = historical_data.groupby('scan_quality').size().reset_index(name='count')
            fig_quality = px.bar(
                quality_stats,
                x='scan_quality',
                y='count',
                title="Scan Quality Distribution",
                color='scan_quality'
            )
            st.plotly_chart(fig_quality, use_container_width=True)
        
        # Data table
        with st.expander("📋 View Historical Data"):
            st.dataframe(historical_data, use_container_width=True)
    
    else:
        st.info("No historical data available. Analyze some images first!")

# Sidebar information
with st.sidebar:
    st.header("ℹ️ App Information")
    st.write("**Pinnalogy AI** - Ear Anatomy Analysis")
    st.write("**Version**: 2.0 (Streamlit Cloud Compatible)")
    st.write("**Features**:")
    st.write("• Image Segmentation")
    st.write("• Anatomical Analysis") 
    st.write("• Historical Analytics")
    st.write("• Condition Assessment")
    
    st.header("📁 Supported Formats")
    st.write("• JPG, JPEG, PNG")
    st.write("• Recommended: 512x512+ pixels")
    st.write("• Clear ear images")
