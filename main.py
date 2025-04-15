import streamlit as st
import pandas as pd
import datetime
from datetime import date
import csv
import os
import matplotlib.pyplot as plt

# Page configuration
st.set_page_config(
    page_title="Personal Expense Tracker",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Files
EXPENSE_FILE = "expenses.csv"
CATEGORIES_FILE = "categories.csv"

# Initialize default categories
DEFAULT_CATEGORIES = [
    "Food", "Transport", "Housing", "Entertainment",
    "Shopping", "Healthcare", "Education", "Other"
]

# Initialize files if they don't exist
def init_files():
    # Expense file
    if not os.path.exists(EXPENSE_FILE):
        with open(EXPENSE_FILE, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Date", "Category", "Amount", "Description"])
    
    # Categories file
    if not os.path.exists(CATEGORIES_FILE):
        with open(CATEGORIES_FILE, mode='w', newline='') as file:
            writer = csv.writer(file)
            for category in DEFAULT_CATEGORIES:
                writer.writerow([category])

# Load categories from CSV
def load_categories():
    try:
        df = pd.read_csv(CATEGORIES_FILE, header=None)
        return df[0].tolist()
    except:
        return DEFAULT_CATEGORIES.copy()

# Save categories to CSV
def save_categories(categories):
    with open(CATEGORIES_FILE, mode='w', newline='') as file:
        writer = csv.writer(file)
        for category in categories:
            writer.writerow([category])

# Load expenses from CSV
def load_expenses():
    try:
        return pd.read_csv(EXPENSE_FILE)
    except:
        return pd.DataFrame(columns=["Date", "Category", "Amount", "Description"])

# Save expenses to CSV
def save_expense(date, category, amount, description):
    with open(EXPENSE_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([date, category, amount, description])

# Main app
def main():
    st.title("Personal Expense Tracker")
    
    # Initialize files
    init_files()
    
    # Load categories
    categories = load_categories()
    
    # Sidebar for navigation
    menu = ["Add Expense", "View Expenses", "Expense Analysis", "Manage Categories"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Add Expense":
        st.subheader("Add New Expense")

        with st.form("expense_form", clear_on_submit=True):
            col1, col2 = st.columns(2)

            with col1:
                expense_date = st.date_input("Date", date.today())
            with col2:
                category = st.selectbox("Category", categories)

            amount = st.number_input("Amount ($)", min_value=0.0, format="%.2f")
            description = st.text_input("Description (optional)")

            submitted = st.form_submit_button("Save Expense")

            if submitted:
                if amount > 0:
                    save_expense(
                        expense_date.strftime("%Y-%m-%d"), 
                        category, 
                        amount, 
                        description
                    )
                    st.success("Expense added successfully!")
                else:
                    st.warning("Please enter a valid amount greater than 0.")

    elif choice == "View Expenses":
        st.subheader("Expense History")

        expenses = load_expenses()

        if not expenses.empty:
            expenses['Date'] = pd.to_datetime(expenses['Date'])

            st.sidebar.subheader("Filter Options")

            all_categories = ['All'] + sorted(expenses['Category'].unique().tolist())
            selected_category = st.sidebar.selectbox("Select Category", all_categories)

            min_date = expenses['Date'].min().date()
            max_date = expenses['Date'].max().date()

            date_range = st.sidebar.date_input(
                "Select Date Range",
                value=[min_date, max_date]
            )

            if selected_category != 'All':
                expenses = expenses[expenses['Category'] == selected_category]

            if len(date_range) == 2:
                start_date, end_date = date_range
                start_date = max(start_date, min_date)
                end_date = min(end_date, max_date)
                expenses = expenses[
                    (expenses['Date'].dt.date >= start_date) & 
                    (expenses['Date'].dt.date <= end_date)
                ]

            expenses = expenses.sort_values('Date', ascending=False)

            st.dataframe(
                expenses.reset_index(drop=True),
                column_config={
                    "Date": st.column_config.DateColumn("Date"),
                    "Amount": st.column_config.NumberColumn("Amount", format="$%.2f")
                },
                hide_index=True,
                use_container_width=True
            )

            total = expenses['Amount'].sum()
            st.metric("Total Expenses", f"${total:,.2f}")

            if st.button("Export to CSV"):
                csv_data = expenses.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv_data,
                    file_name="expenses_export.csv",
                    mime="text/csv"
                )
        else:
            st.info("No expenses recorded yet.")

    elif choice == "Expense Analysis":
        st.subheader("Expense Analysis")

        expenses = load_expenses()

        if not expenses.empty:
            expenses['Date'] = pd.to_datetime(expenses['Date'])

            # Monthly Expenses Bar Chart
            st.markdown("### Monthly Expenses")
            expenses['Month'] = expenses['Date'].dt.to_period('M')
            monthly_expenses = expenses.groupby('Month')['Amount'].sum().reset_index()
            monthly_expenses['Month'] = monthly_expenses['Month'].astype(str)

            fig, ax = plt.subplots()
            ax.bar(monthly_expenses['Month'], monthly_expenses['Amount'], color='skyblue')
            ax.set_xlabel("Month")
            ax.set_ylabel("Amount ($)")
            ax.set_title("Monthly Expenses")
            plt.xticks(rotation=45)
            st.pyplot(fig)

            # Category Breakdown with Pie Chart
            st.markdown("### Category Breakdown")
            category_expenses = expenses.groupby('Category')['Amount'].sum().reset_index()

            col1, col2 = st.columns([1, 2])

            with col1:
                st.dataframe(
                    category_expenses.sort_values('Amount', ascending=False),
                    column_config={
                        "Amount": st.column_config.NumberColumn("Amount", format="$%.2f")
                    },
                    hide_index=True,
                    use_container_width=True
                )

            with col2:
                fig2, ax2 = plt.subplots()
                explode = [0.1 if i == category_expenses['Amount'].idxmin() else 0 
                           for i in range(len(category_expenses))]
                
                ax2.pie(category_expenses['Amount'], 
                       labels=category_expenses['Category'], 
                       autopct='%1.1f%%',
                       startangle=90,
                       explode=explode,
                       shadow=True,
                       colors=plt.cm.Pastel1.colors)
                ax2.set_title("Expense Distribution by Category")
                ax2.axis('equal')
                st.pyplot(fig2)

            # Recent Spending Trends Line Chart
            st.markdown("### Recent Spending Trends")
            recent_expenses = expenses[expenses['Date'] >= (datetime.datetime.now() - datetime.timedelta(days=30))]

            if not recent_expenses.empty:
                daily_expenses = recent_expenses.groupby('Date')['Amount'].sum().reset_index()
                fig3, ax3 = plt.subplots()
                ax3.plot(daily_expenses['Date'], daily_expenses['Amount'], marker='o', linestyle='-', color='coral')
                ax3.set_xlabel("Date")
                ax3.set_ylabel("Amount ($)")
                ax3.set_title("Spending in the Last 30 Days")
                plt.xticks(rotation=45)
                st.pyplot(fig3)
            else:
                st.info("No expenses in the last 30 days.")
        else:
            st.info("No expenses recorded yet.")

    elif choice == "Manage Categories":
        st.subheader("Manage Categories")
        
        st.write("Current Categories:")
        st.write(categories)
        
        with st.form("category_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_category = st.text_input("Add New Category")
                add_button = st.form_submit_button("Add Category")
                
            with col2:
                if categories:
                    category_to_delete = st.selectbox("Select Category to Delete", categories)
                    delete_button = st.form_submit_button("Delete Category")
                else:
                    st.warning("No categories to delete")
        
        if add_button and new_category:
            if new_category.strip() == "":
                st.warning("Please enter a category name")
            elif new_category in categories:
                st.warning("Category already exists")
            else:
                categories.append(new_category)
                save_categories(categories)
                st.success(f"Category '{new_category}' added successfully!")
                st.experimental_rerun()
        
        if 'delete_button' in locals() and delete_button:
            if category_to_delete in DEFAULT_CATEGORIES:
                st.warning("Default categories cannot be deleted")
            else:
                categories.remove(category_to_delete)
                save_categories(categories)
                st.success(f"Category '{category_to_delete}' deleted successfully!")
                st.experimental_rerun()

if __name__ == "__main__":
    main()