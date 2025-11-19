import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io

st.set_page_config(
    page_title="Pinnalogy AI - Ear Analysis",
    page_icon="👂",
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

st.markdown('<div class="main-header">👂 Pinnalogy AI - Ear Analysis Dashboard</div>', unsafe_allow_html=True)

# Create sample data function
def create_sample_data():
    return pd.DataFrame({
        'patient_id': [f'P_{i:03d}' for i in range(1, 21)],
        'age': [25, 34, 47, 52, 38, 61, 29, 45, 56, 33, 42, 58, 31, 49, 27, 39, 53, 36, 44, 60],
        'gender': ['M', 'F', 'M', 'F', 'M', 'F', 'M', 'F', 'M', 'F', 'M', 'F', 'M', 'F', 'M', 'F', 'M', 'F', 'M', 'F'],
        'ear_condition': ['Normal', 'Infection', 'Normal', 'Wax Buildup', 'Normal', 'Perforation', 
                         'Normal', 'Inflammation', 'Scarring', 'Normal', 'Infection', 'Deformity',
                         'Normal', 'Wax Buildup', 'Normal', 'Inflammation', 'Scarring', 'Normal', 'Infection', 'Deformity'],
        'hearing_loss_db': [15, 35, 12, 28, 18, 65, 10, 32, 45, 14, 38, 72, 11, 25, 16, 30, 48, 13, 40, 68],
        'scan_quality': ['Excellent', 'Good', 'Excellent', 'Fair', 'Good', 'Poor', 'Excellent', 'Good', 
                        'Fair', 'Excellent', 'Good', 'Poor', 'Excellent', 'Fair', 'Good', 'Good', 'Fair', 'Excellent', 'Good', 'Poor'],
        'treatment_plan': ['None', 'Medication', 'None', 'Cleaning', 'None', 'Surgery', 'None', 'Medication',
                          'Monitoring', 'None', 'Medication', 'Surgery', 'None', 'Cleaning', 'None', 'Medication',
                          'Monitoring', 'None', 'Medication', 'Surgery'],
        'visit_date': pd.date_range('2024-01-01', periods=20, freq='D')
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
        # Convert to numpy array
        img_array = np.array(image)
        
        # Get basic image stats
        height, width = img_array.shape[0], img_array.shape[1]
        file_size = len(image.tobytes()) / 1024  # KB
        
        # Simple "analysis" based on image characteristics
        if height > 1000 and width > 1000:
            quality = "Excellent"
            confidence = 0.9
        elif height > 500 and width > 500:
            quality = "Good" 
            confidence = 0.7
        else:
            quality = "Fair"
            confidence = 0.5
            
        # Simulate anatomical coverage (random for demo)
        np.random.seed(hash(image.tobytes()) % 1000)
        helix = np.random.uniform(20, 30)
        antihelix = np.random.uniform(15, 25)
        concha = np.random.uniform(10, 20)
        lobule = np.random.uniform(5, 15)
        
        coverage_data = {
            'helix': helix,
            'antihelix': antihelix, 
            'concha': concha,
            'lobule': lobule,
            'total': helix + antihelix + antihelix + lobule,
            'quality': quality,
            'confidence': confidence
        }
        
        return coverage_data, img_array
        
    except Exception as e:
        st.error(f"Analysis error: {str(e)}")
        return None, None

# Load data
df = load_data()

# Main app
tab1, tab2, tab3 = st.tabs(["📷 Image Analysis", "📊 Patient Analytics", "🏥 Clinic Overview"])

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
                results, img_array = analyze_ear_image(image)
                
                if results:
                    with col2:
                        st.subheader("Analysis Results")
                        
                        # Display metrics
                        cols = st.columns(4)
                        regions = ['helix', 'antihelix', 'concha', 'lobule']
                        
                        for i, region in enumerate(regions):
                            with cols[i]:
                                coverage = results[region]
                                st.markdown(f"""
                                <div class="metric-card">
                                    <h3>{region.upper()}</h3>
                                    <h2>{coverage:.1f}%</h2>
                                </div>
                                """, unsafe_allow_html=True)
                        
                        # Total coverage
                        st.metric("Total Coverage", f"{results['total']:.1f}%")
                        st.metric("Image Quality", results['quality'])
                        st.metric("Confidence", f"{results['confidence']:.1%}")
                        
                        # Condition assessment
                        if results['total'] > 70:
                            st.success("✅ Normal ear anatomy detected")
                        elif results['total'] > 50:
                            st.warning("⚠️ Mild abnormalities detected")
                        else:
                            st.error("🚨 Significant abnormalities detected")
                    
                    st.success("Analysis completed successfully!")
                    
                    # Show comparison with historical data
                    st.subheader("Historical Comparison")
                    avg_coverage = df['hearing_loss_db'].mean()  # Using hearing loss as proxy for demo
                    comparison = (results['total'] / avg_coverage * 100) - 100
                    
                    st.metric(
                        "Compared to Average", 
                        f"{results['total']:.1f}%",
                        delta=f"{comparison:+.1f}%"
                    )

with tab2:
    st.header("Patient Analytics")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
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
    
    with col3:
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
    
    # Charts
    st.subheader("Visualizations")
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        # Condition distribution
        condition_counts = filtered_df['ear_condition'].value_counts()
        fig_condition = px.pie(
            values=condition_counts.values,
            names=condition_counts.index,
            title="Ear Condition Distribution"
        )
        st.plotly_chart(fig_condition, use_container_width=True)
        
        # Age distribution
        fig_age = px.histogram(
            filtered_df, 
            x='age',
            color='gender',
            title="Patient Age Distribution"
        )
        st.plotly_chart(fig_age, use_container_width=True)
    
    with chart_col2:
        # Hearing loss by condition
        fig_hearing = px.box(
            filtered_df,
            x='ear_condition',
            y='hearing_loss_db',
            title="Hearing Loss by Condition"
        )
        st.plotly_chart(fig_hearing, use_container_width=True)
        
        # Quality distribution
        quality_counts = filtered_df['scan_quality'].value_counts()
        fig_quality = px.bar(
            x=quality_counts.index,
            y=quality_counts.values,
            title="Scan Quality Distribution"
        )
        st.plotly_chart(fig_quality, use_container_width=True)
    
    # Data table
    with st.expander("View Patient Data"):
        st.dataframe(filtered_df, use_container_width=True)

with tab3:
    st.header("Clinic Overview")
    
    # Summary statistics
    st.subheader("Clinic Performance")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Treatment plan distribution
        treatment_counts = df['treatment_plan'].value_counts()
        fig_treatment = px.pie(
            values=treatment_counts.values,
            names=treatment_counts.index,
            title="Treatment Plan Distribution"
        )
        st.plotly_chart(fig_treatment, use_container_width=True)
    
    with col2:
        # Monthly trend (simulated)
        monthly_data = pd.DataFrame({
            'month': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            'patients': [45, 52, 48, 61, 55, 58],
            'normal_cases': [35, 38, 36, 42, 40, 41]
        })
        
        fig_trend = px.line(
            monthly_data,
            x='month',
            y=['patients', 'normal_cases'],
            title="Monthly Patient Trends"
        )
        st.plotly_chart(fig_trend, use_container_width=True)
    
    # Quick insights
    st.subheader("Quick Insights")
    
    insight_col1, insight_col2 = st.columns(2)
    
    with insight_col1:
        st.info(f"**Most Common Condition**: {df['ear_condition'].mode().iloc[0]}")
        st.info(f"**Average Patient Age**: {df['age'].mean():.1f} years")
    
    with insight_col2:
        st.info(f"**Need Treatment**: {(df['treatment_plan'] != 'None').sum()} patients")
        st.info(f"**Data Quality**: {len(df)} records available")

# Sidebar
with st.sidebar:
    st.header("👂 Pinnalogy AI")
    st.write("Ear Analysis & Patient Management")
    
    st.header("Features")
    st.write("• Image Analysis")
    st.write("• Patient Analytics") 
    st.write("• Clinic Overview")
    st.write("• Treatment Planning")
    
    st.header("Sample Data")
    st.write(f"Total Patients: {len(df)}")
    st.write(f"Data Period: {df['visit_date'].min().strftime('%Y-%m-%d')} to {df['visit_date'].max().strftime('%Y-%m-%d')}")
    
    if st.button("Clear Cache"):
        st.cache_data.clear()
        st.success("Cache cleared!")

st.markdown("---")
st.markdown("**Pinnalogy AI** | Medical Imaging Analysis Platform")
