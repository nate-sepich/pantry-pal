import streamlit as st
import time 
# Display Streamlit content
st.title("Streamlit App with Gradio Integration")

import subprocess
aaa = subprocess.Popen(["gradio", "gradio_interface.py"])

# Replace the Gradio interface URL with your generated share link
gradio_interface_url = "http://localhost:7860/"  # Example URL

# Load the Gradio interface using an iframe
st.write(f'<iframe src="{gradio_interface_url}" width="800" height="600"></iframe>',
         unsafe_allow_html=True) 