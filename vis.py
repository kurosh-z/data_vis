import os, sys

# import plotly.graph_objects as go
import pandas as pd
import plotly.express as px
import streamlit as st
import requests as rq

# fileDay = "26_06_2022"


PHONE_NAME = "sonimKstVoda"

st.title("Data Visualization for Bad Oldesloe")

st.markdown(
    """### Quick guide:
- change the date to generate plots for a different day
- hover on the plot to see additional Infos
- hovering on the plot also triggers additional tools on the top right corner sof the plot to download the plot as an image, make full screen, etc.
              
            """
)

st.markdown("### Enter the date in dd_mm_yyyy format (eg. 16_07_2022): ")
fileDay = st.text_input("", "")
# fileName = f"data/sim_{fileDay}.csv"


def main():
    url = f"http://212.227.175.162/smartphone_hub_app/sim_{fileDay}.csv"

    payload = {}
    headers = {}

    response = rq.request("GET", url, headers=headers, data=payload)

    # with open(fileName, "r") as f:
    #     lines = f.readlines()

    if not response.status_code == 200:
        st.markdown(f"""Error: Could not find the file sim_{fileDay}.csv in our database!""")

    else:

        lines = response.text.split("\n")
        data = {"pc": [], "datetime": [], "name": [], "lat": [], "lon": [], "loc_validity": []}
        for line in lines:
            if len(line) == 0:
                continue
            l = line.strip()
            llist = l.split(" ")
            name = llist[4]
            if name == PHONE_NAME:
                data["name"].append(name)
                data["pc"].append(int(llist[1]))
                data["datetime"].append(formatTime(llist[2], llist[3]))
                lat = float(llist[5])
                lon = float(llist[6])
                data["lat"].append(lat)
                data["lon"].append(lon)
                loc_validity = 0 if lat == 0 and lon == 0 else 1
                data["loc_validity"].append(loc_validity)

        df = pd.DataFrame.from_dict(data)

        if len(df) == 0:
            st.markdown("#### There is no valid data for this day!")
        else:
            create_plots(df)


def formatTime(date, time):
    dlist = date.split(".")
    dlist.reverse()
    dStr = "-".join(dlist)

    return dStr + " " + time


def calAvaragePcs(df, seconds=900):

    date0 = df["datetime"][0]
    lastTime = df["datetime"][len(df) - 1]

    averagePackets = []
    timeList = []

    currentTime = date0
    delta = pd.Timedelta(seconds=seconds)

    while currentTime < lastTime:
        cnt = len(df[(df["datetime"] >= currentTime) & (df["datetime"] < currentTime + delta)]["pc"])
        averagePackets.append(cnt)
        currentTime = currentTime + delta
        timeList.append(currentTime)

    return timeList, averagePackets


def create_plots(df):
    df["datetime"] = df["datetime"].astype("datetime64[ns]")

    st.markdown("### Change the duration for the 2nd plot (default 15 minutes)")
    dur_minutes = st.text_input("", "15")
    dur_minutes = int(dur_minutes)
    timeList, avarages = calAvaragePcs(df, seconds=60 * dur_minutes)
    df2 = pd.DataFrame.from_dict({"pc": avarages, "datetime": timeList})

    # fig = go.Figure()

    # fig.add_trace(go.Scatter(x=list(df.datetime), y=list(df.pc)))
    fig = px.scatter(
        df,
        x="datetime",
        y=df.index,
        labels={
            "pc": "Number of packets",
            "datetime": "date and time",
            "index": "packet count",
            "loc_validity": "location's validity",
        },
        # template="plotly_white",
        template="ggplot2",
        color_discrete_sequence=["blue"],
    )
    fig.update_layout(title_text=f"<b>Time series of the number of packets on {fileDay}</b>")
    fig.update_layout(
        font_color="black",
        # title_font_family="Times New Roman",
        # title_font_color="black",
        # legend_title_font_color="green",
    )

    # fig2 = go.Figure()

    # fig2.add_trace(go.Scatter(x=timeList, y=avarages))
    fig2 = px.line(
        df2,
        x="datetime",
        y="pc",
        labels={
            "pc": f"packets received every {dur_minutes} minutes",
            "datetime": "date and time",
        },
        template="ggplot2",
    )
    fig2.update_layout(title_text=f"<b>Number of packets sent every {dur_minutes} minutes for {fileDay} </b>")

    # Add range slider
    fig.update_layout(
        dragmode="zoom",
        hovermode="x",
        # template="ggplot2",
        xaxis=dict(
            rangeselector=dict(
                buttons=list(
                    [
                        dict(count=1, label="1h", step="hour", stepmode="backward"),
                        dict(count=6, label="6h", step="hour", stepmode="backward"),
                        dict(count=10, label="12h", step="hour", stepmode="backward"),
                        dict(count=12, label="16h", step="hour", stepmode="backward"),
                        dict(step="all"),
                    ]
                )
            ),
            rangeslider=dict(visible=True),
            type="date",
        ),
    )

    # Add range slider
    fig2.update_layout(
        dragmode="zoom",
        hovermode="x",
        # height=600,
        template="ggplot2",
        # template="plotly_white",
        xaxis=dict(
            rangeselector=dict(
                buttons=list(
                    [
                        dict(count=1, label="1h", step="hour", stepmode="backward"),
                        dict(count=6, label="6h", step="hour", stepmode="backward"),
                        dict(count=10, label="12h", step="hour", stepmode="backward"),
                        dict(count=12, label="16h", step="hour", stepmode="backward"),
                        dict(step="all"),
                    ]
                )
            ),
            rangeslider=dict(visible=True),
            type="date",
        ),
    )

    loc_validity_fig = px.scatter(
        df,
        x="datetime",
        y=df.loc_validity,
        labels={
            "pc": "Number of packets",
            "datetime": "date and time",
            "index": "packet count",
            "loc_validity": "location's validity",
        },
        # template="plotly_white",
        template="ggplot2",
        color_discrete_sequence=["blue"],
    )
    loc_validity_fig.update_layout(title_text=f"<b>Validity of recieved location '1 True, 0 False'</b>")
    loc_validity_fig.update_layout(
        font_color="black",
        # title_font_family="Times New Roman",
        # title_font_color="black",
        # legend_title_font_color="green",
    )

    df_map = df[df["loc_validity"] == 1]
    map_fig = px.scatter_mapbox(
        df_map,
        lat="lat",
        lon="lon",
        hover_name="name",
        hover_data=["datetime"],
        color_discrete_sequence=["red"],
        zoom=12,
        height=500,
    )
    map_fig.update_layout(mapbox_style="open-street-map")
    map_fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

    # fig.show()
    # fig2.show()

    st.markdown("----")
    st.markdown(
        """### Plot1: Numer of recieved packets against time
            """
    )

    st.plotly_chart(fig)

    st.markdown("----")
    st.markdown(
        f"""### Plot2: Numer of recieved every {dur_minutes} minutes
            """
    )
    st.plotly_chart(fig2)

    st.markdown("----")
    st.markdown(
        """### Plot3: Validity of recieved location data
            """
    )

    st.plotly_chart(loc_validity_fig)

    st.markdown("----")
    st.markdown(
        """### Plot4: Map of valid locations
            """
    )

    if len(df_map) == 0:
        st.write("There is no valid location to show!")
    else:
        st.plotly_chart(map_fig)
    #  yaxis2=dict(anchor="x",
    #     autorange=True,
    #     domain=[0.2, 0.4],
    #     linecolor="#E91E63",
    #     mirror=True,
    #     range=[0, 200],
    #     showline=True,
    #     side="right",
    #     tickfont={"color": "#E91E63"},
    #     tickmode="auto",
    #     zeroline=False,
    #     type="linear",
    # ),


if __name__ == "__main__":
    main()
