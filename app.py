import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image
import os
import requests
from streamlit_image_coordinates import streamlit_image_coordinates

# ==========================================
# STEP 1: WEB PAGE CONFIGURATION & TITLE
# ==========================================
st.set_page_config(page_title="Ultimate Shade Detector", layout="centered")
st.title("🎨 Ultimate Color Shade Detector")
st.write("Identify over 865+ unique shades using your webcam or an uploaded picture!")

# ==========================================
# STEP 2: DOWNLOAD & LOAD THE SHADE DATASET
# ==========================================
# ==========================================
# STEP 2: LOAD THE LOCAL SHADE DATASET
# ==========================================
CSV_FILE = "colors.csv"

@st.cache_data
def load_dataset():
    # Read the file directly from your repository without downloading anything
    return pd.read_csv(CSV_FILE, names=["color_name", "hex", "R", "G", "B"], header=None)

color_df = load_dataset()

CSV_URL = "https://githubusercontent.com"
CSV_FILE = "colors.csv"

@st.cache_data
def load_dataset():
    # If the file isn't on your computer yet, download it automatically
    if not os.path.exists(CSV_FILE):
        response = requests.get(CSV_URL)
        with open(CSV_FILE, "wb") as f:
            f.write(response.content)
    return pd.read_csv(CSV_FILE, names=["color_name", "hex", "R", "G", "B"], header=None)

color_df = load_dataset()

# ==========================================
# STEP 3: COLOR IDENTIFICATION MATH ENGINE
# ==========================================
def identify_shade(r, g, b):
    """Finds the closest color shade using 3D Euclidean distance."""
    # Measure the distance between your clicked pixel and all 865 shades
    distances = np.sqrt(
        (color_df['R'] - r) ** 2 + 
        (color_df['G'] - g) ** 2 + 
        (color_df['B'] - b) ** 2
    )
    # Find the row index of the smallest distance (the closest match)
    min_idx = distances.idxmin()
    min_distance = distances[min_idx]
    
    # Calculate accuracy percentage (Max possible distance in RGB space is ~441.67)
    max_possible_dist = 441.67
    accuracy = max(0.0, (1.0 - (min_distance / max_possible_dist)) * 100)
    
    return color_df.loc[min_idx, 'color_name'], round(accuracy, 2)

# ==========================================
# STEP 4: SIDEBAR & USER INPUT INTERFACE
# ==========================================
mode = st.sidebar.radio("Choose Input Method:", ("📤 Upload an Image", "📷 Take a Webcam Photo"))

target_image = None

if mode == "📤 Upload an Image":
    uploaded_file = st.file_uploader("Choose an image file...", type=["jpg", "jpeg", "png"])
    if uploaded_file is not None:
        target_image = Image.open(uploaded_file).convert("RGB")

elif mode == "📷 Take a Webcam Photo":
    webcam_file = st.camera_input("Snapshot an object")
    if webcam_file is not None:
        target_image = Image.open(webcam_file).convert("RGB")

# ==========================================
# STEP 5: INTERACTIVE CLICKING & ACCURACY LOGIC
# ==========================================
if target_image is not None:
    st.info("👇 Click directly on any object inside the image below to identify its shade!")
    
    # Scale image nicely to fit nicely on screens
    target_image.thumbnail((600, 600))
    img_width, img_height = target_image.size
    
    # Render image on webpage and capture the exact mouse click coordinates
    value = streamlit_image_coordinates(target_image, width=img_width, key="color_picker")
    
    if value is not None:
        x, y = value["x"], value["y"]
        
        # Verify the click coordinates are safely inside the image bounds
        if x < img_width and y < img_height:
            img_array = np.array(target_image)
            r, g, b = img_array[y, x]  # Extract red, green, and blue values
            
            # Send the values to our math engine to get the name and accuracy
            shade_name, accuracy_percentage = identify_shade(r, g, b)
            hex_color = f"#{r:02x}{g:02x}{b:02x}"
            
            # --- DISPLAY THE RESULT MATCH BOX ---
            st.markdown("---")
            st.subheader("🔍 Analysis Results")
            
            col1, col2 = st.columns()
            with col1:
                # Creates a visual colored square tile of the color you clicked
                st.markdown(f"""
                <div style="background-color: {hex_color}; width: 100px; height: 100px; 
                border-radius: 10px; border: 3px solid #fff; box-shadow: 0px 4px 10px rgba(0,0,0,0.3);">
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"**Identified Shade:** `{shade_name}`")
                st.markdown(f"**RGB Value:** `[{r}, {g}, {b}]` | **HEX Code:** `{hex_color}`")
            
            # --- ACCURACY ACCORDION BUTTON ---
            st.markdown(" ")
            if st.button("📊 Show Identification Accuracy"):
                if accuracy_percentage > 90:
                    st.success(f"Excellent Match! The system is **{accuracy_percentage}%** confident this shade is **{shade_name}**.")
                elif accuracy_percentage > 75:
                    st.warning(f"Good Match! The system is **{accuracy_percentage}%** confident this shade is **{shade_name}**.")
                else:
                    st.error(f"Low Certainty Match (**{accuracy_percentage}%**). Shadows or poor camera lighting might be affecting the calculation.")
