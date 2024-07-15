import streamlit as st
import pandas as pd
import json
from datetime import datetime

# Initialize session state
if 'username' not in st.session_state:
    st.session_state.username = ''
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0

def load_data(file):
    with open(file, 'r') as f:
        data = json.load(f)
    return data


def save_data(file, data):
    with open(file, 'w') as f:
        json.dump(data, f, indent=2)

def login():
    username = st.text_input("Enter your username:")
    if st.button("Login"):
        if username:
            st.session_state.username = username
            st.success(f"Logged in as {username}")
            st.experimental_rerun()
        else:
            st.error("Please enter a username")

def main():
    st.set_page_config(page_title="Text Difference Annotation Tool", layout='wide')

    # if not st.session_state.username:
    #     login()
    # else:
    #     st.write(f"Logged in as: {st.session_state.username}")
    #     if st.button("Logout"):
    #         st.session_state.username = ''
    #         st.experimental_rerun()

    st.markdown("""
### Instructions

For each annotation task, you will be given two texts that contains a few sentences. Your job is to determine how different these texts are. Rate the difference in a scale of 1-5, as explained below. Ignore the words inside the brackets, {name} {age} {etc}, when examining the difference. 

1. Same. The two texts are exactly identical, except for the part inside the brackets, {name} {age} {etc}. 
2. Similar. The two texts are semantically similar. Some words or phrases are different but have the same meaning. 
3. Slightly different. The two texts are on the same topic, but have differences in the tone, support materials or less than 1/2 of the key points. 
4. Largely different. The two texts are on the same topic, but have differences in more than 1/2 of the key points. 
5. Completely different. The two texts have completely different meanings. They are on different topics or contains unrelated key points. 
""")

    # Load existing annotations
    annotations = load_data('anno_data.json')

    # Navigation buttons
    col1, col2, col3 = st.columns([1,2,1])
    with col1:
        if st.button("Previous") and st.session_state.current_index > 0:
            st.session_state.current_index -= 1
    with col3:
        if st.button("Next") and st.session_state.current_index < len(annotations) - 1:
            st.session_state.current_index += 1

    current_annotation = annotations[st.session_state.current_index]

    # Display current example index
    st.write(f"Current example: {st.session_state.current_index + 1}/{len(annotations)}")

    st.markdown('### Question')
    st.markdown(current_annotation['base_question'])

    st.divider()
    
    # Create two columns for text display
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Response 1")
        # text1 = st.text_area("", value=current_annotation["r1"]["outputs"], height=300, key="text1", disabled=True)
        st.markdown(current_annotation["r1"]["outputs"])

    with col2:
        st.subheader("Response 2")
        # text2 = st.text_area("", value=current_annotation["r2"]['outputs'], height=300, key="text2", disabled=True)
        st.markdown(current_annotation["r2"]["outputs"])

    # Radio button for rating
    options = ['<not annotated>', 'Same', 'Similar', 'Slightly Different', 'Largely Different', 'Completely Different']
    y = 0
    if 'rating' in current_annotation:
        y = options.index(current_annotation['rating'])
    
    rating = st.radio(
        label='Rate the difference:',
        options=options,
        index=y,
        key=f'label_{st.session_state.current_index}'
    )

    if st.button("Submit Annotation"):
        if rating != options[0]:
            current_annotation['rating'] = rating
            current_annotation['timestamp'] = datetime.now().isoformat()
            # current_annotation['username'] = st.session_state.username
            annotations[st.session_state.current_index] = current_annotation
            save_data('anno_data.json', annotations)
            st.success("Annotation submitted successfully!")
        else:
            st.warning('You have not chosen a label yet!')

    # Display existing annotations
    if annotations:
        st.subheader("Existing Annotations")
        df = pd.DataFrame(annotations)
        st.dataframe(df)

if __name__ == "__main__":
    main()