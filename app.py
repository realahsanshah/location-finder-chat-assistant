import streamlit as st
import plotly.graph_objects as go
from openai import OpenAI
import time
import json


client = OpenAI(api_key=st.secrets['OPENAI_API_KEY'])

st.title('Where to go?')

left_col, right_col = st.columns(2)

if "map" not in st.session_state:
    st.session_state['map'] = {
        'latitude': 33.6844,
        'longitude': 73.0479,
        'zoom':10
    }

if "conversation" not in st.session_state: 
    st.session_state['conversation'] = []

if "assistant" not in st.session_state:
    st.session_state['assistant'] = client.beta.assistants.retrieve(st.secrets['TRAVEL_ASSISTANT_ID'])
    st.session_state['thread'] = client.beta.threads.create()
    st.session_state['run'] = None


# with st.sidebar:
#     st.header("Debug")
#     st.write(st.session_state.to_dict())


with left_col:
    st.subheader("What's your mood?")

    for role,message in st.session_state['conversation']:
        with st.chat_message(role):
            st.write(message)
    

with right_col:
    fig = go.Figure(go.Scattermapbox())
    fig.update_layout(
        mapbox=dict(
            accesstoken = st.secrets["MAPBOX_PUBLIC_KEY"],
            center=go.layout.mapbox.Center(
                lat=st.session_state['map']['latitude'],
                lon=st.session_state['map']['longitude']
            ),
            zoom=st.session_state['map']['zoom']
        ),
        margin=dict(l=0, r=0, t=0, b=0)
    )

    st.plotly_chart(fig,config={'displayModeBar': False},use_container_width=True,key="plotly")


def update_map(latitude:float,longitude:float,zoom:int)->str:
    print("latitude",latitude)
    print("longitude",longitude)
    print("zoom",zoom)

    st.session_state['map']['latitude'] = latitude
    st.session_state['map']['longitude'] = longitude
    st.session_state['map']['zoom'] = zoom

    return "Map updated"

def on_text_submit():
    st.session_state['conversation'].append(
        ('user',st.session_state['user_input'])
    )

    client.beta.threads.messages.create(
        thread_id=st.session_state['thread'].id,
        role="user",
        content=st.session_state['user_input']
    )

    st.session_state['run'] = client.beta.threads.runs.create(
        thread_id=st.session_state['thread'].id,
        assistant_id=st.session_state['assistant'].id,
    )

    run = client.beta.threads.runs.retrieve(
        thread_id=st.session_state['thread'].id,
        run_id=st.session_state['run'].id
    )
    while run.status != "completed":
        time.sleep(0.1)

        run = client.beta.threads.runs.retrieve(
            thread_id=st.session_state['thread'].id,
            run_id=st.session_state['run'].id
        )

        if run.status == 'requires_action':
            tools_output = []

            for tool_call in run.required_action.submit_tool_outputs.tool_calls:
                f = tool_call.function
                print("f",f)
                f_name = f.name
                print("f_name",f_name)
                f_args = json.loads(f.arguments)
                print("f_args",f_args)

                tool_result = tool_to_function[f_name](**f_args)
                print("tool_result",tool_result)

                tools_output.append(
                    {
                        "tool_call_id": tool_call.id,
                        "output": tool_result,
                    }
                )

            client.beta.threads.runs.submit_tool_outputs(
                thread_id=st.session_state['thread'].id,
                run_id=st.session_state['run'].id,
                tool_outputs=tools_output
            )


    st.session_state['conversation'] = [
        (m.role,m.content[0].text.value)
        for m in reversed(client.beta.threads.messages.list(thread_id=st.session_state['thread'].id).data)
    ]
                    
            


user_input = st.chat_input(
    placeholder='Enter your text here',
    key="user_input",
    on_submit=on_text_submit
)

tool_to_function = {
    "update_map": update_map
}
