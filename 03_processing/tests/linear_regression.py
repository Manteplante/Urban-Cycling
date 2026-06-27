# linear_regression.py
import matplotlib.pyplot as plt
import numpy as np
from sklearn.linear_model import LinearRegression
import streamlit as st

# Change this function to fit data from Jupyter Notebook located in folder "step2"

def run_linear_regression():
    # Data: Dependent variable (Y) = number of trips, Independent variable (X) = month (summer)
    months = np.array([5, 6, 7, 8])
    trips = np.array([32, 73, 67, 93])
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot actual data points
    ax.scatter(months, trips, color='blue', s=100, label='Turer')
    
    # Fit regression model
    X = months.reshape(-1, 1)
    model = LinearRegression()
    model.fit(X, trips)
    
    # Calculate R² score
    r2 = model.score(X, trips)
    
    # Create regression line between the min and max months
    line_x = np.array([months.min(), months.max()])
    line_y = model.predict(line_x.reshape(-1, 1))
    ax.plot(line_x, line_y, color='red', linestyle='--', label=f'Trend (R² = {r2:.3f})') # proportion of the variance in the dependent variable that is predictable from the independent variable(s)
    
    # Customize plot
    ax.set_title('Bakklandet -> Bakklandet: Bysykkeltur Trondheim sommeren 2024', fontsize=14, pad=20)
    ax.set_xlabel('Måned', fontsize=12)
    ax.set_ylabel('Antall turer', fontsize=12)
    ax.set_xticks(months)
    ax.set_xticklabels(['Mai', 'Juni', 'Juli', 'August'])
    ax.text(5.1, 90, f'Månedlig trend koeffisient: +{model.coef_[0]:.2f} trips', fontsize=10)
    ax.grid(True, linestyle='--', alpha=0.7)
    ax.legend()
    fig.tight_layout()
    
    # Display the plot using Streamlit
    st.pyplot(fig)