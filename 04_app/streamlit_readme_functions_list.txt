1. Page Structure and Text Elements

# Text and Headers
st.title() --> allows you to set the title of your app
st.header() --> allows you to set the header of your app
st.subheader() --> allows you to set the subheader of your app
st.text() --> allows you to set the text of your app
st.markdown() --> allows you to set the markdown of your app
st.caption() --> adds small text below other elements
st.write() --> allows you to display text, dataframes, and other objects
st.code() --> allows you to display code snippets
st.latex() --> allows you to display mathematical expressions using LaTeX

# Page Configuration
st.set_page_config() --> configure the page title, favicon, layout, etc.
st.columns() --> create columnar layout
st.tabs() --> create tabbed interface


2. Data Display and Visualization

# Tables and Data Display
st.dataframe() --> allows you to display interactive dataframes
st.table() --> allows you to display static tables
st.json() --> allows you to display JSON data
st.metric() --> allows you to display metrics with optional delta values

# Basic Visualizations
st.map() --> allows you to display a map with data points
st.line_chart() --> display simple line charts
st.area_chart() --> display simple area charts
st.bar_chart() --> display simple bar charts
st.pyplot() --> display matplotlib figures
st.altair_chart() --> display Altair charts
st.vega_lite_chart() --> display Vega-Lite charts
st.plotly_chart() --> display Plotly figures
st.bokeh_chart() --> display Bokeh charts
st.pydeck_chart() --> display PyDeck charts
st.graphviz_chart() --> display Graphviz charts

3. Input Widgets and Interactive Controls

# Selection Widgets
st.selectbox() --> allows you to create a select box
st.multiselect() --> allows you to create a multiselect box
st.radio() --> allows you to create a radio button
st.checkbox() --> allows you to create a checkbox

# Input Widgets
st.slider() --> allows you to create a slider
st.text_input() --> allows you to create a text input box
st.text_area() --> allows you to create a text area
st.number_input() --> allows you to create a number input box
st.date_input() --> allows you to create a date input box
st.time_input() --> allows you to create a time input box
st.color_picker() --> allows you to create a color picker

# Button Widgets
st.button() --> allows you to create a button
st.download_button() --> allows you to create a download button
st.form() --> create a form that batches widget values
st.form_submit_button() --> submit button for a form


4. Layout and Containers

# Layout Components
st.sidebar() --> allows you to create a sidebar for controls
st.expander() --> allows you to create an expandable container
st.container() --> allows you to create a container for elements
st.empty() --> allows you to create an empty container for later placement
st.columns() --> create multiple columns layout
st.tabs() --> create tabbed interface for organizing content

# Custom Layouts
st.beta_container() --> create a container for custom layout (legacy)
st.beta_columns() --> create columns for custom layout (legacy)
st.beta_expander() --> create expandable sections (legacy)


5. Media and Files

# Media Elements
st.image() --> allows you to display images
st.video() --> allows you to display videos
st.audio() --> allows you to display audio

# File Operations
st.file_uploader() --> allows you to create a file uploader
st.download_button() --> allow users to download data

6. State Management and Performance

# State Management
st.session_state() --> allows you to create a session state
st.experimental_rerun() --> rerun the app from top to bottom

# Caching and Performance
st.cache() --> allows you to cache the results of a function
st.cache_data() --> cache data to improve app performance
st.cache_resource() --> cache resources like database connections


7. Advanced Dashboard Features

# Filters and Cross-Filtering
st.query_params --> access and modify URL query parameters
st.experimental_connection() --> connect to data sources
st.experimental_data_editor() --> editable data tables

# Custom Components
st.components.v1.html() --> embed custom HTML
st.components.v1.iframe() --> embed an iframe
st.pydeck_chart() --> create interactive maps

# Dashboard Analytics
st.experimental_get_query_params() --> get query parameters for analytics
st.experimental_set_query_params() --> set query parameters for shareable filters

8. Notifications and Decorative Elements

# Notifications
st.success() --> display success message
st.info() --> display informational message
st.warning() --> display warning message
st.error() --> display error message
st.exception() --> display an exception

# Decorative Elements
st.progress() --> allows you to display a progress bar
st.spinner() --> allows you to display a spinner during processing
st.balloons() --> allows you to display balloons animation
st.snow() --> display a snow animation


9. Theme and Styling

# Styling
st.markdown("", unsafe_allow_html=True) --> for custom CSS
st.set_page_config(theme="light"/"dark") --> set theme
st.markdown("""<style>...</style>""", unsafe_allow_html=True) --> custom CSS

# Responsive Design
st.beta_columns([1, 2, 1]) --> responsive column widths
st.empty().markdown("<div class='custom-class'>...</div>", unsafe_allow_html=True) --> for responsive containers