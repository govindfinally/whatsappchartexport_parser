import streamlit as st
import pandas as pd
from io import BytesIO
from file_reader import FileReader
import traceback

# Page configuration
st.set_page_config(
    page_title="WhatsApp Chat to Excel Converter",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header">💬 WhatsApp Chat Parser</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Convert your placement WhatsApp chats to Excel format</div>', unsafe_allow_html=True)

# Sidebar - Instructions
with st.sidebar:
    st.header("📋 Instructions")
    st.markdown("""
    ### How to use:
    1. **Export your WhatsApp chat** (without media)
    2. **Upload the .txt file** using the uploader
    3. **Click Process** to extract company data
    4. **Download** the Excel file
    
    ### Expected Format:
    ```
    DD/MM/YY, HH:MM - +91 XXXXX: *Company Name | Job Type*
    
    *Job Role:* Role Name
    *CTC:* Amount
    *Stipend:* Amount
    ...
    ```
    
    ### Extracted Fields:
    - Company Name
    - Job Role
    - CTC
    - Stipend
    - Eligible Batch
    - Eligible Courses
    - Eligible Branches
    - Internship Duration
    - Location
    - Application Link
    """)
    
    st.divider()
    st.markdown("### 🔧 Settings")
    show_preview = st.checkbox("Show file preview", value=True)
    show_logs = st.checkbox("Show processing logs", value=False)

# Main content
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    # File uploader
    uploaded_file = st.file_uploader(
        "Upload WhatsApp Chat Export (.txt)",
        type=['txt'],
        help="Export your WhatsApp chat without media and upload the .txt file"
    )

if uploaded_file is not None:
    try:
        # Read file content
        try:
            content = uploaded_file.read().decode('utf-8')
        except UnicodeDecodeError:
            try:
                uploaded_file.seek(0)  # Reset file pointer
                content = uploaded_file.read().decode('utf-8-sig')  # Try with BOM
            except UnicodeDecodeError:
                st.error("❌ Unable to decode the file. Please ensure it's a valid text file.")
                st.stop()
        
        # Show preview if enabled
        if show_preview:
            with st.expander("📄 File Preview (First 20 lines)", expanded=False):
                preview_lines = content.split('\n')[:20]
                st.text('\n'.join(preview_lines))
        
        # Statistics
        total_lines = len(content.split('\n'))
        st.info(f"📊 File loaded: **{uploaded_file.name}** | Total lines: **{total_lines}**")
        
        # Process button
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            process_button = st.button("🚀 Process File", type="primary", use_container_width=True)
        
        if process_button:
            with st.spinner("🔄 Processing your chat data..."):
                try:
                    # Create FileReader instance
                    reader = FileReader()
                    
                    # Process content
                    if show_logs:
                        result, logs = reader.process_content(content, verbose=True)
                        df = result if isinstance(result, pd.DataFrame) else result[0]
                        
                        # Show processing logs
                        with st.expander("📝 Processing Logs", expanded=True):
                            for log_line in logs:
                                st.text(log_line)
                    else:
                        result = reader.process_content(content, verbose=False)
                        df = result if isinstance(result, pd.DataFrame) else result[0]
                    
                    # Check if any companies were found
                    if len(df) == 0:
                        st.error("❌ No companies found in the uploaded file. Please check the file format.")
                    else:
                        # Success message
                        st.success(f"✅ Successfully extracted data from **{len(df)} companies**!")
                        
                        # Display statistics
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Companies Found", len(df))
                        with col2:
                            filled_roles = df['Job Role'].notna().sum()
                            st.metric("With Job Roles", filled_roles)
                        with col3:
                            filled_ctc = df['CTC'].notna().sum()
                            st.metric("With CTC Info", filled_ctc)
                        with col4:
                            filled_links = df['Application Link'].notna().sum()
                            st.metric("With App Links", filled_links)
                        
                        st.divider()
                        
                        # Display DataFrame
                        st.subheader("📊 Extracted Data")
                        st.dataframe(
                            df,
                            use_container_width=True,
                            height=400,
                            hide_index=True
                        )
                        
                        # Download section
                        st.divider()
                        st.subheader("💾 Download Options")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            # Excel download
                            buffer = BytesIO()
                            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                                df.to_excel(writer, index=False, sheet_name='Companies')
                            buffer.seek(0)
                            
                            st.download_button(
                                label="📥 Download as Excel (.xlsx)",
                                data=buffer,
                                file_name="company_data.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True
                            )
                        
                        with col2:
                            # CSV download
                            csv = df.to_csv(index=False).encode('utf-8')
                            st.download_button(
                                label="📥 Download as CSV",
                                data=csv,
                                file_name="company_data.csv",
                                mime="text/csv",
                                use_container_width=True
                            )
                        
                        # Additional analysis
                        with st.expander("📈 Quick Analysis", expanded=False):
                            st.subheader("Field Completion Rate")
                            
                            completion_data = []
                            for col in df.columns:
                                if col != 'name':
                                    filled = df[col].notna().sum()
                                    total = len(df)
                                    percentage = (filled / total * 100) if total > 0 else 0
                                    completion_data.append({
                                        'Field': col,
                                        'Filled': filled,
                                        'Total': total,
                                        'Completion %': f"{percentage:.1f}%"
                                    })
                            
                            completion_df = pd.DataFrame(completion_data)
                            st.dataframe(completion_df, use_container_width=True, hide_index=True)
                            
                            # Most common values
                            st.subheader("Most Common Values")
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                if df['Eligible Batch'].notna().sum() > 0:
                                    st.write("**Eligible Batches:**")
                                    batch_counts = df['Eligible Batch'].value_counts().head(5)
                                    st.write(batch_counts)
                            
                            with col2:
                                if df['Eligible Courses'].notna().sum() > 0:
                                    st.write("**Eligible Courses:**")
                                    course_counts = df['Eligible Courses'].value_counts().head(5)
                                    st.write(course_counts)
                
                except Exception as e:
                    st.error(f"❌ An error occurred during processing: {str(e)}")
                    with st.expander("🔍 Error Details"):
                        st.code(traceback.format_exc())
    
    except Exception as e:
        st.error(f"❌ Error reading file: {str(e)}")
        with st.expander("🔍 Error Details"):
            st.code(traceback.format_exc())

else:
    # Show example when no file is uploaded
    st.info("👆 Upload a WhatsApp chat export file to get started")
    
    with st.expander("📖 Example Format"):
        st.code("""08/09/25, 17:11 - +91 97773 92266: *AB InBev | Summer Internship | On-Campus*

*Job Role:* Supply Excellence Trainee Intern

*Stipend:* INR 60 KPM + INR 15000 (Reimbursement against rent, utilities)

*CTC (On PPO Conversion):* 17.5 LPA

*Eligible Batch:* 2027

*Eligible Courses:* B.Tech

*Eligible Branches:*
* EC, EI, EE, ME, CH, CE, MM, FP

*Application Form:* https://forms.gle/example

*Deadline:* 11.59PM, 9th September, 2025
""", language="text")

# Footer
st.divider()
st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.9rem;">
        Made with ❤️ using Streamlit | Export your WhatsApp chats without media for best results
    </div>
""", unsafe_allow_html=True)