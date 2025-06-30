import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import io



def handling_missing(df):
    st.write("What do you want to do with these values?")
    Options = [
        "Choose an Option",
        "Remove the Rows with missing values !",
        "Fill them by the mean of the Column if exists!",
        "Remove the Column with missing values (recommended if more than 80% values are missing)",
        "Keep them as it is"
    ]

    has_NA = df.isnull().sum()
    columns_with_NAN = {k: v for k, v in has_NA.items() if v != 0}

    handling = st.selectbox("Choose One of them:", options=Options)
    if handling == Options[0]:
        st.warning("Please select a option !")
        return df
    elif handling == Options[1]:
        return df.dropna()
    elif handling == Options[2]:
        for key in columns_with_NAN:
            if pd.api.types.is_numeric_dtype(df[key]):
                df[key].fillna(df[key].mean(), inplace=True)
            else:
                df[key].fillna("No Data Provided", inplace=True)
        return df
    elif handling == Options[3]:
        return df.dropna(axis=1)
    else:
        st.write("Let's Move Forwards !")
        return df


def showing_pieChart(df):
    if st.checkbox("Show Missing Value Pie Chart"):
        missing = df.isnull().sum()
        missing = missing[missing > 0]
        if not missing.empty:
            fig, ax = plt.subplots()
            ax.pie(missing, labels=missing.index, autopct='%1.1f%%', startangle=90)
            ax.axis('equal')
            st.pyplot(fig)


def Outlier_Detection(df, apply_outlier_removal):
    if apply_outlier_removal:
        df = df.copy()
        numeric_cols = df.select_dtypes(include=['number']).columns
        before = df.shape[0]
        for col in numeric_cols:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            df = df[(df[col] >= lower_bound) & (df[col] <= upper_bound)]
        after = df.shape[0]
        if before == after:
            st.success("Your Data is Outlier Free")
        else:
            st.success(f"Removed {before - after} outlier rows.")
    return df


def remove_duplicate(df, apply_dup_removal):
    if apply_dup_removal:
        df = df.copy()
        before = df.shape[0]
        df = df.drop_duplicates()
        after = df.shape[0]
        if before == after:
            st.success("Your Data has 0 duplicate Rows")
        else:
            st.success(f"Removed {before - after} duplicate rows.")
    return df


st.title("*File Cleaner*")
st.write("Managing messy data in Excel or CSV files?")
st.text("Let this tool handle the hard part — upload your file, choose your cleaning options, and get a ready-to-use dataset in seconds!")

st.markdown("""
**Features of the App:**
- File Support:
  - `.csv`
  - `.xlsx`
- Clean missing values
- Remove duplicate rows
- View summary statistics
- Export cleaned data
""")

file_type = st.radio("Choose file type:", ["CSV", "Excel"], horizontal=True)
editable_or_not = st.radio("Do you want to edit on your own ?", ["NO", "YES"], horizontal=True)

st.write("Please Upload your Data File !")
uploaded_data = False

if file_type == "CSV":
    uploaded_csv = st.file_uploader("Choose your .csv file", type='csv')
    if uploaded_csv:
        df = pd.read_csv(uploaded_csv)
        uploaded_data = True
elif file_type == "Excel":
    uploaded_excel = st.file_uploader("Choose your .xlsx file", type='xlsx')
    if uploaded_excel:
        df = pd.read_excel(uploaded_excel)
        uploaded_data = True

if uploaded_data:
    final_df = df
    if editable_or_not == "NO":
        st.markdown(f" Data from your `{file_type}` File : ")
        st.write(df)

        has_nan = df.isnull().sum()
        if has_nan.sum() == 0:
            st.text("Nice ! , Your file has 0 missing values.")
        else:
            st.text(f"Your File has {has_nan.sum()} missing Values.")
            showing_pieChart(df)

        apply_outliers = st.checkbox("Remove Outliers (IQR Method)", key="outliers_checkbox")
        apply_duplicates = st.checkbox("Remove Duplicate Rows", key="duplicates_checkbox")

        cleaned_df = df.copy()
        cleaned_df = Outlier_Detection(cleaned_df, apply_outliers)
        cleaned_df = remove_duplicate(cleaned_df, apply_duplicates)
        cleaned_df = handling_missing(cleaned_df)

        st.text("You have missing values in these Sections : ")
        has_nan = cleaned_df.isnull().sum()
        if has_nan.sum()==0:
            st.write("Nice ! , now there is 0 missing value.")
        else:
            st.write(has_nan)

        st.markdown("### Cleaned Data Preview:")
        st.write(cleaned_df)

        # Final download section
        final_df = cleaned_df
        st.markdown("### 📥 Download Cleaned Data")

        export_format = st.radio("Select export format:", ["CSV", "Excel"], horizontal=True)
        if export_format == "CSV":
            csv_data = final_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📄 Download as CSV",
                data=csv_data,
                file_name="cleaned_data.csv",
                mime="text/csv"
            )
        elif export_format == "Excel":
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                final_df.to_excel(writer, index=False, sheet_name="CleanedData")
                writer.close()
            st.download_button(
                label="📊 Download as Excel",
                data=buffer.getvalue(),
                file_name="cleaned_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )


    else:
        st.write("Now, You can EDIT your data file:")
        st.text("Click 'RESET' to revert back to original data at any time.")

        # Initialize session_state
        if "original_df" not in st.session_state:
            st.session_state.original_df = df.copy()
        if "edited_df" not in st.session_state:
            st.session_state.edited_df = df.copy()
        if "table_key" not in st.session_state:
            st.session_state.table_key = "editor_1"

        # RESET BUTTON
        if st.button("🔁 RESET"):
            st.session_state.edited_df = st.session_state.original_df.copy()
            st.session_state.table_key = "editor_" + str(np.random.randint(10000))  # change key to refresh
            st.success("✅ Your data has been reset to the original file.")
            st.rerun()

        # Show editable table
        editable_df = st.data_editor(
            st.session_state.edited_df,
            num_rows="dynamic",
            key=st.session_state.table_key
        )

        # Store user edits in session
        st.session_state.edited_df = editable_df

        # Dynamic options
        apply_outliers = st.checkbox("Remove Outliers (IQR Method)", key="edit_outliers_checkbox")
        apply_duplicates = st.checkbox("Remove Duplicate Rows", key="edit_duplicates_checkbox")

        st.write("*Tip: You can RESET anytime to revert changes.*")

        # Live transformation copy
        final_df = editable_df.copy()
        final_df = Outlier_Detection(final_df, apply_outliers)
        final_df = remove_duplicate(final_df, apply_duplicates)
        final_df = handling_missing(final_df)

        # Show missing stats
        has_nan = final_df.isnull().sum()
        if has_nan.sum() == 0:
            st.success("Now your file is clean! ✅")
        else:
            st.warning("Remaining Missing Values:")
            st.write(has_nan)

        st.markdown("### Cleaned Data Preview:")
        st.write(final_df)

        # Final download section
        st.markdown("### 📥 Download Cleaned Data")

        export_format = st.radio("Select export format:", ["CSV", "Excel"], horizontal=True)

        if export_format == "CSV":
            csv_data = final_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📄 Download as CSV",
                data=csv_data,
                file_name="cleaned_data.csv",
                mime="text/csv"
            )
        elif export_format == "Excel":
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                final_df.to_excel(writer, index=False, sheet_name="CleanedData")
                writer.close()
            st.download_button(
                label="📊 Download as Excel",
                data=buffer.getvalue(),
                file_name="cleaned_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )




