import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

header = st.container()
header.title("Time Series Forecaster")
header.write("""<div class='fixed-header'/>""", unsafe_allow_html=True)

### Custom CSS for the sticky header
st.markdown(
    """
<style>
    div[data-testid="stVerticalBlock"] div:has(div.fixed-header) {
        position: sticky;
        top: 0.555rem;
        background-color: white;
        z-index: 999;
    }
    .fixed-header {
        border-bottom: 1px solid black;
    }
</style>
    """,
    unsafe_allow_html=True
)
#st.header(':blue[Database Volume Forecaster]', divider='rainbow')

# Header
# st.title('Time Series Forecaster')

# Footer
#st.markdown('All rights reserved @2024')

# Date pickers
st.sidebar.subheader('Select Time Range:')
start_date = st.sidebar.date_input('Start Date')
end_date = st.sidebar.date_input('End Date')

# Button for forecasting
# Button for forecasting with blue background
st.sidebar.button(':blue[Forecast]')


# Generate some example data
date_range = pd.date_range(start='2024-01-01', end='2024-12-31')
data = np.sin(np.arange(len(date_range)) * np.pi / 180)
df = pd.DataFrame({'Date': date_range, 'Value': data})
df.set_index('Date', inplace=True)

# Line graph
# st.subheader('Line Graph:')
# st.write(df)

fig, ax = plt.subplots()
ax.plot(df.index, df['Value'])
ax.set_xlabel('Date')
ax.set_ylabel('Value')
st.pyplot(fig)

footer="""<style>
a:link , a:visited{
color: blue;
background-color: transparent;
text-decoration: underline;
}


.footer {
position: fixed;
left: 0;
bottom: 0;
width: 100%;
background-color: lightblue;
color: black;
text-align: center;
}
</style>
<div class="footer">
<p> All Right Reserved @2024</a></p>
</div>
"""
#st.markdown(footer,unsafe_allow_html=True)