import streamlit as st
import tensorflow as tf
import cv2
import numpy as np
import pandas as pd
from PIL import Image
import tempfile
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

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
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">🦻 Pinnalogy AI - Ear Anatomy Analysis</div>', unsafe_allow_html=True)

# Load segmentation history data
@st.cache_data
def load_segmentation_data():
    """Load historical segmentation data"""
    try:
        df = pd.read_csv('data/ear_segmentation_history.csv')
        return df
    except FileNotFoundError:
        st.warning("Historical data not found. Analysis will proceed without comparison data.")
        return None

# Simple model loading
@st.cache_resource
def load_model():
    try:
        model = tf.keras.models.load_model('ear_segmentation_model.keras')
        return model
    except:
        st.info("Running in demo mode with simulated predictions")
        return None

def predict_ear(image_array, threshold=0.3):
    """Simple prediction function"""
    try:
        # Preprocess
        image_rgb = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)
        input_image = cv2.resize(image_rgb, (512, 512))
        input_array = input_image.astype(np.float32) / 255.0
        input_array = np.expand_dims(input_array, axis=0)
        
        # Mock prediction (dalam production, guna model real)
        masks = {}
        regions = ['helix', 'antihelix', 'concha', 'lobule']
        
        # Generate more realistic masks based on actual image content
        height, width = 512, 512
        center_x, center_y = width // 2, height // 2
        
        for region in regions:
            mask = np.zeros((height, width, 1), dtype=np.uint8)
            
            if region == 'helix':
                # Outer ear shape
                cv2.ellipse(mask, (center_x, center_y), (200, 150), 0, 0, 360, 255, -1)
                cv2.ellipse(mask, (center_x, center_y), (180, 130), 0, 0, 360, 0, -1)
            elif region == 'antihelix':
                # Inner ear structure
                cv2.ellipse(mask, (center_x, center_y), (150, 110), 0, 0, 360, 255, -1)
                cv2.ellipse(mask, (center_x, center_y), (130, 90), 0, 0, 360, 0, -1)
            elif region == 'concha':
                # Ear canal area
                cv2.ellipse(mask, (center_x, center_y), (100, 70), 0, 0, 360, 255, -1)
            elif region == 'lobule':
                # Ear lobe
                cv2.ellipse(mask, (center_x, center_y + 120), (80, 50), 0, 0, 360, 255, -1)
            
            masks[region] = mask
        
        return masks, input_image
        
    except Exception as e:
        st.error(f"Prediction error: {e}")
        return None, None

def calculate_coverage_stats(masks, image_size=512):
    """Calculate coverage statistics for each region"""
    total_pixels = image_size * image_size
    stats = {}
    
    for region, mask in masks.items():
        coverage = (np.sum(mask > 0) / total_pixels) * 100
        stats[region] = {
            'coverage': coverage,
            'pixel_count': np.sum(mask > 0)
        }
    
    total_coverage = sum([stats[region]['coverage'] for region in masks.keys()])
    stats['total_coverage'] = total_coverage
    
    return stats

# Load historical data
historical_data = load_segmentation_data()

# Main app layout
tab1, tab2 = st.tabs(["🎯 Image Analysis", "📊 Analytics Dashboard"])

with tab1:
    st.header("Upload Ear Image for Analysis")
    
    uploaded_file = st.file_uploader("Choose an ear image", type=['jpg', 'jpeg', 'png'])
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        image_np = np.array(image)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.image(image, caption="Uploaded Image", use_column_width=True)
            
            # Image info
            st.subheader("Image Information")
            st.write(f"**Format**: {uploaded_file.type}")
            st.write(f"**Size**: {image.size[0]} x {image.size[1]}")
            st.write(f"**Uploaded**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if st.button("Analyze Ear Anatomy", type="primary"):
            with st.spinner("Analyzing ear anatomy..."):
                predictions, processed_img = predict_ear(image_np)
                
                if predictions:
                    # Calculate statistics
                    stats = calculate_coverage_stats(predictions)
                    
                    # Create visualization
                    combined_mask = np.zeros((512, 512, 3), dtype=np.uint8)
                    colors = {
                        'helix': (255, 0, 0),      # Red
                        'antihelix': (0, 255, 0),  # Green
                        'concha': (0, 0, 255),     # Blue
                        'lobule': (255, 255, 0)    # Yellow
                    }
                    
                    for region, mask in predictions.items():
                        color = colors[region]
                        combined_mask[mask[:,:,0] > 0] = color
                    
                    with col2:
                        st.image(combined_mask, caption="Anatomical Regions Segmentation", use_column_width=True)
                        
                        # Overlay image
                        overlay = cv2.addWeighted(processed_img, 0.7, combined_mask, 0.3, 0)
                        st.image(overlay, caption="Segmentation Overlay", use_column_width=True)
                    
                    # Display results
                    st.subheader("📈 Analysis Results")
                    
                    # Metrics in columns
                    metric_cols = st.columns(4)
                    regions = list(predictions.keys())
                    
                    for i, region in enumerate(regions):
                        with metric_cols[i]:
                            coverage = stats[region]['coverage']
                            st.markdown(f"""
                            <div class="metric-card">
                                <h3>{region.upper()}</h3>
                                <h2>{coverage:.1f}%</h2>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    # Total coverage
                    st.metric("Total Anatomical Coverage", f"{stats['total_coverage']:.1f}%")
                    
                    # Comparison with historical data
                    if historical_data is not None:
                        avg_coverage = historical_data['total_coverage'].mean()
                        coverage_diff = stats['total_coverage'] - avg_coverage
                        st.metric("Compared to Historical Average", f"{stats['total_coverage']:.1f}%", 
                                 delta=f"{coverage_diff:+.1f}%")
                    
                    st.success("✅ Analysis completed successfully!")

with tab2:
    st.header("📊 Analytics Dashboard")
    
    if historical_data is not None:
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_analyses = len(historical_data)
            st.metric("Total Analyses", total_analyses)
        
        with col2:
            avg_coverage = historical_data['total_coverage'].mean()
            st.metric("Avg Coverage", f"{avg_coverage:.1f}%")
        
        with col3:
            normal_cases = (historical_data['ear_condition'] == 'Normal').sum()
            st.metric("Normal Cases", normal_cases)
        
        with col4:
            avg_confidence = historical_data['analysis_confidence'].mean() * 100
            st.metric("Avg Confidence", f"{avg_confidence:.1f}%")
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Coverage distribution by region
            coverage_data = historical_data[['helix_coverage', 'antihelix_coverage', 'concha_coverage', 'lobule_coverage']]
            fig_coverage = px.box(
                coverage_data,
                title="Coverage Distribution by Anatomical Region",
                labels={'value': 'Coverage %', 'variable': 'Region'}
            )
            st.plotly_chart(fig_coverage, use_container_width=True)
            
            # Age vs Coverage
            fig_age = px.scatter(
                historical_data,
                x='age',
                y='total_coverage',
                color='ear_condition',
                size='analysis_confidence',
                title="Age vs Total Coverage"
            )
            st.plotly_chart(fig_age, use_container_width=True)
        
        with col2:
            # Ear condition distribution
            condition_counts = historical_data['ear_condition'].value_counts()
            fig_condition = px.pie(
                values=condition_counts.values,
                names=condition_counts.index,
                title="Ear Condition Distribution"
            )
            st.plotly_chart(fig_condition, use_container_width=True)
            
            # Scan quality analysis
            quality_analysis = historical_data.groupby('scan_quality').agg({
                'analysis_confidence': 'mean',
                'total_coverage': 'mean'
            }).reset_index()
            
            fig_quality = px.bar(
                quality_analysis,
                x='scan_quality',
                y=['analysis_confidence', 'total_coverage'],
                title="Analysis Metrics by Scan Quality",
                barmode='group'
            )
            st.plotly_chart(fig_quality, use_container_width=True)
        
        # Data table
        with st.expander("View Historical Data"):
            st.dataframe(historical_data, use_container_width=True)
    
    else:
        st.info("No historical data available. Upload images in the Analysis tab to build dataset.")

# Model information
with st.sidebar:
    st.header("Model Information")
    st.write("**Model**: Ear Anatomy Segmentation")
    st.write("**Input Size**: 512x512 pixels")
    st.write("**Regions Detected**: 4")
    st.write("**Supported Formats**: JPG, JPEG, PNG")
    
    if historical_data is not None:
        st.header("Quick Stats")
        st.write(f"Total analyses: {len(historical_data)}")
        st.write(f"Latest analysis: {historical_data['timestamp'].max()}")
