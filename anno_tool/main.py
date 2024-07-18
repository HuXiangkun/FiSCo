import streamlit as st
import pandas as pd
import json
from datetime import datetime
import difflib
import re

import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
from streamlit_authenticator import Authenticate


def highlight_similarities(s1, s2):
    # Define a list of colors
    colors = ["#DDFFDD", "#FFDDDD", "#DDDDFF", "#FFFFDD", "#DDFFFF", "#FFDDFF"]
    
    # Split the strings into words
    words1 = s1.split()
    words2 = s2.split()

    # Use difflib to find matching blocks
    matcher = difflib.SequenceMatcher(None, words1, words2)
    matching_blocks = matcher.get_matching_blocks()

    # Initialize the result lists
    highlighted_s1 = []
    highlighted_s2 = []

    # Indices to keep track of the last position
    last_s1_index = 0
    last_s2_index = 0

    # Color index
    color_index = 0

    for block in matching_blocks:
        s1_start, s2_start, length = block

        # Add the different parts before the matching block
        highlighted_s1.extend(words1[last_s1_index:s1_start])
        highlighted_s2.extend(words2[last_s2_index:s2_start])

        # Add the matching part with color only if the length is at least 2
        if length >= 2:
            color = colors[color_index % len(colors)]
            color_start = f'<span style="background-color: {color}">'
            color_end = '</span>'
            highlighted_s1.append(color_start + ' '.join(words1[s1_start:s1_start + length]) + color_end)
            highlighted_s2.append(color_start + ' '.join(words2[s2_start:s2_start + length]) + color_end)
            color_index += 1
        else:
            # Add the non-matching part if the length is less than 2
            highlighted_s1.extend(words1[s1_start:s1_start + length])
            highlighted_s2.extend(words2[s2_start:s2_start + length])

        # Update the indices
        last_s1_index = s1_start + length
        last_s2_index = s2_start + length

    # Add the remaining parts after the last matching block
    highlighted_s1.extend(words1[last_s1_index:])
    highlighted_s2.extend(words2[last_s2_index:])

    # Join the parts into final strings
    highlighted_s1 = ' '.join(highlighted_s1)
    highlighted_s2 = ' '.join(highlighted_s2)

    return highlighted_s1, highlighted_s2


def display_data(username):
    # Initialize session state
    if 'current_index' not in st.session_state:
        st.session_state.current_index = 0

    # Load existing annotations
    annotations = json.load(open(f'anno_data_{username}.json'))

    # Navigation buttons
    col1, col2, _ = st.columns([1,1,9])
    with col1:
        if st.button("Previous") and st.session_state.current_index > 0:
            st.session_state.current_index -= 1
    with col2:
        if st.button("Next") and st.session_state.current_index < len(annotations) - 1:
            st.session_state.current_index += 1

    current_annotation = annotations[st.session_state.current_index]
    
    # Radio button for rating
    options = ['<not annotated>', 'Same', 'Similar', 'Slightly Different', 'Largely Different', 'Completely Different']
    y = 0
    if 'rating' in current_annotation:
        y = options.index(current_annotation['rating'])
    
    rating = st.radio(
        label='Rate the difference:',
        options=options,
        index=y,
        key=f'label_{st.session_state.current_index}',
        horizontal=True
    )

    if st.button("Submit Annotation"):
        if rating != options[0]:
            current_annotation['rating'] = rating
            current_annotation['timestamp'] = datetime.now().isoformat()
            # current_annotation['username'] = st.session_state.username
            annotations[st.session_state.current_index] = current_annotation
            json.dump(annotations, open(f'anno_data_{username}.json', 'w'), indent=2)
            st.success("Annotation submitted successfully!")
        else:
            st.warning('You have not chosen a label yet!')

    # Display current example index
    st.markdown(f'### Question {st.session_state.current_index + 1}/{len(annotations)}')
    st.markdown(current_annotation['base_question'])
    
    # Create two columns for text display
    col1, col2 = st.columns(2)
    
    r1 = current_annotation["r1"]["outputs"].replace(current_annotation["r1"]["name"], "[name]")
    r2 = current_annotation["r2"]["outputs"].replace(current_annotation["r2"]["name"], "[name]")
    r1, r2 = highlight_similarities(r1, r2)
    
    with col1:
        st.subheader("Response 1")
        st.markdown(r1, unsafe_allow_html=True)

    with col2:
        st.subheader("Response 2")
        st.markdown(r2, unsafe_allow_html=True)

    

    # Display existing annotations
    if annotations:
        st.subheader("Existing Annotations")
        df = pd.DataFrame(annotations)
        st.dataframe(df)


def main():
    st.set_page_config(page_title="Text Difference Annotation Tool", layout='wide')

    with open('config.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)

    authenticator = Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days'],
        config['preauthorized']
    )
    name, authentication_status, username = authenticator.login()

    if authentication_status:
        with st.sidebar:
            st.write(f'Welcome **{name}**')
            authenticator.logout('Logout', 'main')
            
            st.markdown("""
### Instructions

For each annotation task, you will be given two texts that contains a few sentences. Your job is to determine how different these texts are. Rate the difference in a scale of 1-5, as explained below. Ignore the words inside the brackets, {name} {age} {etc}, when examining the difference. 

1. **Same**. The two texts are exactly identical, except for the part inside the brackets, {name} {age} {etc}. 
2. **Similar**. The two texts are semantically similar. Some words or phrases are different but have the same meaning. 
3. **Slightly different**. The two texts are on the same topic, but have differences in the tone, support materials or less than 1/2 of the key points. 
4. **Largely different**. The two texts are on the same topic, but have differences in more than 1/2 of the key points. 
5. **Completely different**. The two texts have completely different meanings. They are on different topics or contains unrelated key points. 
""")
        
        display_data(username)
    

if __name__ == "__main__":
    main()