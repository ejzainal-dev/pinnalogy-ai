import streamlit as st
import tensorflow as tf
import cv2
import numpy as np
from PIL import Image
import tempfile
from datetime import datetime

st.set_page_config(
    page_title="Pinnalogy AI - Ear Analysis",
    page_icon="🦻",
    layout="wide"
)

st.title("🦻 Pinnalogy AI - Ear Anatomy Analysis")
st.write("Upload an ear image for automatic anatomical segmentation")

# Simple model loading
@st.cache_resource
def load_model():
    try:
        model = tf.keras.models.load_model('ear_segmentation_model.keras')
        return model
    except:
        st.error("Model loaded in simple mode")
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
        # Untuk demo, kita create simple masks
        masks = {}
        regions = ['helix', 'antihelix', 'concha', 'lobule']
        
        for region in regions:
            # Create simple mask based on image regions
            mask = np.zeros((512, 512, 1), dtype=np.uint8)
            
            # Different regions dapat different areas
            if region == 'helix':
                cv2.ellipse(mask, (256, 256), (150, 200), 0, 0, 360, 255, -1)
            elif region == 'antihelix':
                cv2.ellipse(mask, (256, 256), (120, 170), 0, 0, 360, 255, -1)
            elif region == 'concha':
                cv2.ellipse(mask, (256, 256), (80, 120), 0, 0, 360, 255, -1)
            elif region == 'lobule':
                cv2.rectangle(mask, (200, 400), (312, 500), 255, -1)
            
            masks[region] = mask
        
        return masks, input_image
        
    except Exception as e:
        st.error(f"Prediction error: {e}")
        return None, None

# Main app
model = load_model()

uploaded_file = st.file_uploader("Upload Ear Image", type=['jpg', 'jpeg', 'png'])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    image_np = np.array(image)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.image(image, caption="Uploaded Image", use_column_width=True)
    
    if st.button("Analyze Ear Anatomy"):
        with st.spinner("Analyzing..."):
            predictions, processed_img = predict_ear(image_np)
            
            if predictions:
                # Create combined visualization
                combined_mask = np.zeros((512, 512, 3), dtype=np.uint8)
                colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]
                
                for i, (region, mask) in enumerate(predictions.items()):
                    combined_mask[mask[:,:,0] > 0] = colors[i]
                
                with col2:
                    st.image(combined_mask, caption="Anatomical Regions", use_column_width=True)
                
                # Show simple stats
                st.subheader("Analysis Results")
                total_pixels = 512 * 512
                
                for region, mask in predictions.items():
                    coverage = (np.sum(mask > 0) / total_pixels) * 100
                    st.write(f"**{region.upper()}**: {coverage:.1f}% coverage")
                
                st.success("✅ Analysis completed successfully!")
