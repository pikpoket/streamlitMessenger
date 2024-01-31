# This is a sample Python script.

# Press Maj+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

import pandas as pd
import os
import plotly.express as px
import json
import streamlit as st



def main(name):
    # Use a breakpoint in the code line below to debug your script.

    st.title("Messenger analysis :sunglasses: \t")
    st.caption("To obtain messenger data, follow the instructions on this link https://www.facebook.com/help/212802592074644")
    st.caption("Then upload one of you conversation (found in messages/inbox/*<conversation_name>*/message_1.json)")
    st.caption("None of your data is stored on Streamlit server https://discuss.streamlit.io/t/how-long-are-are-the-files-uploaded-via-file-uploader-stored-on-streamlits-server/12897")
    st.caption("You can found the source code for this project on my github: https://github.com/pikpoket/streamlitMessenger/blob/master/main.py")

    with st.spinner('Wait for it...'):
        json_conv = st.file_uploader('Upload messenger file', type="json")  # 👈 this is a widget

        if json_conv != None:
            #with open(json_conv, "r", encoding='utf8') as f:
            jsonFile = json_conv.read()
            dictConv = json.loads(jsonFile)
            friend_df = pd.DataFrame()
            for i, msg in enumerate(dictConv["messages"]):
                emitter = msg["sender_name"].encode("latin1").decode()

                #                 if emitter not in friends[convName].keys():
                #                     friends[convName][emitter] = pd.DataFrame(columns=["content","timestamp"])

                df = friend_df
                row = {"content": "", "timestamp": "", "emitter": ""}

                row["emitter"] = emitter
                if "content" in msg.keys():
                    row["content"] = msg["content"].encode("latin1").decode()
                if "timestamp_ms" in msg.keys():
                    row["timestamp"] = msg["timestamp_ms"]

                row = pd.DataFrame.from_dict([row])

                df = pd.concat([row, df], sort=False)

                friend_df = df

            #st.dataframe(df)


            wdf = df
            wdf["date"] = pd.to_datetime(df["timestamp"], unit="ms")
            wdf.set_index("date")

            wdf["hour"] = wdf.date.dt.strftime('%H')
            wdf["day"] = wdf.date.dt.day_name()
            wdf["time_delta_s"] = (wdf['timestamp'] - wdf['timestamp'].shift()).fillna(0) / 1000
            wdf['emitter_changed'] = (wdf['emitter'] != wdf['emitter'].shift(1))
            wdf['previous_emitter'] = wdf['emitter'].shift(1)
            wdf["more_than_seven_hours"] = wdf["time_delta_s"] > 60 * 60 * 7
            wdf["hover_data"] = wdf.content.str.wrap(100).apply(lambda x: x.replace('\n', '<br>'))
            wdf["content_no_urls"] = wdf['content'].str.replace(
                'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', ' ')
            wdf["size"] = wdf.content_no_urls.str.len()

            groups = wdf['more_than_seven_hours'].ne(wdf['more_than_seven_hours'].shift()).cumsum()
            groupedConvDf = wdf.groupby(groups).apply(lambda x: x.reset_index(drop=True))

            groupedConvDf = groupedConvDf.rename(columns={"more_than_seven_hours": ">7h"})
            groupedConvDf = groupedConvDf.reset_index()
            groupedConvDf = groupedConvDf.rename(columns={"more_than_seven_hours": "convClusters"})
            groupedConvDf = groupedConvDf.drop("level_1", axis=1)

            convClustersDf = groupedConvDf.groupby("convClusters").agg({"content": "count", "size": "sum", "date": "min"})
            convClustersDf["clusterId"] = convClustersDf.index
            convClustersDf = groupedConvDf.rename(columns={"content": "count"})

            timeToAnswerDf = wdf[(wdf.emitter_changed == True) & (wdf.more_than_seven_hours == False)]

            stats = ""
            msgExchanged = 0

            stats = ""

            result = timeToAnswerDf.groupby("emitter")["time_delta_s"].mean()
            result = result.to_frame()
            for row in result.itertuples():
                stats += "On average, **{}** took :grey[**{}**] minutes to answer.  \n".format(row.Index, round(row.time_delta_s / 60, 1))

            stats += "  \n"

            initConvWdf = wdf[wdf["more_than_seven_hours"] == True]
            initConv = initConvWdf.groupby("emitter")["more_than_seven_hours"].count()
            initConv = initConv.to_frame()
            percent = None
            for row in initConv.itertuples():
                stats += "**{}** initiated the conversation :grey[**{}**] times ({}%).  \n".format(row.Index, row.more_than_seven_hours, round(
                    row.more_than_seven_hours / int(initConv.sum()[0]) * 100))

            stats += "  \n"

            initConvWdf = wdf[wdf["more_than_seven_hours"] == True]
            initConv = initConvWdf.groupby("previous_emitter")["more_than_seven_hours"].count()
            initConv = initConv.to_frame()
            for row in initConv.itertuples():
                stats += "**{}** closed the conversation :grey[**{}**] times ({}%).  \n".format(row.Index, row.more_than_seven_hours, round(
                    row.more_than_seven_hours / int(initConv.sum()[0]) * 100))
                msgExchanged = initConv.sum()[0]


            st.header("Conversation overview")
            st.caption("Make a selection rectangle to zoom in on a period")
            st.caption("Hover the dots to see message content, be aware that really long messages might not display (>2300 characters)")

            msgAll = px.scatter(wdf, y="size", x="date", color="emitter", hover_data="hover_data")
            st.plotly_chart(msgAll)


            st.markdown(stats)


            st.divider()

            st.header("Number of message per hour")
            msgHours = px.histogram(wdf, x="hour", color="emitter", barmode="group")
            st.plotly_chart(msgHours)
            st.divider()

            st.header("Number of message per day")
            msgDays = px.histogram(wdf, x="day", color="emitter", barmode="group")
            st.plotly_chart(msgDays)
            st.divider()

            st.header("Message count timeline")
            msgGlobal = px.histogram(wdf, x="date", color="emitter", barmode="group")
            st.plotly_chart(msgGlobal)
            st.divider()

            st.header("Total characters sent")
            msgCarac = px.histogram(wdf, x="date", y="size", color="emitter", barmode="group", histfunc="sum")
            st.plotly_chart(msgCarac)

            st.balloons()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main('PyCharm')

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
