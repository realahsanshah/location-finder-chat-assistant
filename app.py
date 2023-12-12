import streamlit as st
import plotly.graph_objects as go

st.title('Multimodel Chat Bot')

left_col, right_col = st.columns(2)


with left_col:
    st.subheader('User Input')
    

with right_col:
    fig = go.Figure(go.Scattermapbox())
    fig.update_layout(
        mapbox=dict(
            accesstoken = st.secrets["MAPBOX_PUBLIC_KEY"],
            center=go.layout.mapbox.Center(lat=45, lon=-73),
        ),
        margin=dict(l=0, r=0, t=0, b=0)
    )

    st.plotly_chart(fig,config={'displayModeBar': False},use_container_width=True,key="plotly")

user_input = st.chat_input('Enter your text here')