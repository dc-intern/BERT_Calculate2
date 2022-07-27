from audioop import avg
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from matplotlib.backends.backend_pdf import PdfPages
import math
import io

# get rluc and eyfp from the file 
@st.cache
def readfile(file):
    rluc = {0:{}}
    eyfp = {0:{}}
    df = pd.read_excel(file, usecols='A')
    label1_row = df.index[df['Method name: Method 1'] == 'Label 1'][0] + 5
    label2_row = df.index[df['Method name: Method 1'] == 'Label 2'][0] + 5

    # check is there any data in cols[H:J] and cols[K:M] for graph 2 and 3
    temp = pd.read_excel(file, skiprows=np.append(np.arange(label1_row), np.arange(label1_row+9, 400)), usecols="A,H:J", index_col=0) 
    table2_exist = not temp.isnull().values.any()
    temp = pd.read_excel(file, skiprows=np.append(np.arange(label1_row), np.arange(label1_row+9, 400)), usecols="A,K:M", index_col=0) 
    table3_exist = not temp.isnull().values.any()
    
    if table2_exist:
        rluc[1] = {}
        eyfp[1] = {}
    
    if table3_exist:
        rluc[2] = {}
        eyfp[2] = {}

    for i in range(6):
        rluc[0][i] = pd.read_excel(file, skiprows=np.append(np.arange(label1_row+i*13), np.arange(label1_row+9+i*13,275)), usecols="A:D", index_col=0) 
        rluc[0][i+6] = pd.read_excel(file, skiprows=np.append(np.arange(label1_row+i*13), np.arange(label1_row+9+i*13,275)), usecols="A,E:G", index_col=0) 
        eyfp[0][i] = pd.read_excel(file, skiprows=np.append(np.arange(label2_row+i*13), np.arange(label2_row+9+i*13,275)), usecols="A:D", index_col=0) 
        eyfp[0][i+6] = pd.read_excel(file, skiprows=np.append(np.arange(label2_row+i*13), np.arange(label2_row+9+i*13,275)), usecols="A,E:G", index_col=0) 

        if table2_exist:
            rluc[1][i] = pd.read_excel(file, skiprows=np.append(np.arange(label1_row+i*13), np.arange(label1_row+9+i*13,275)), usecols="A:D", index_col=0) 
            rluc[1][i+6] = pd.read_excel(file, skiprows=np.append(np.arange(label1_row+i*13), np.arange(label1_row+9+i*13,275)), usecols="A,H:J", index_col=0) 
            eyfp[1][i] = pd.read_excel(file, skiprows=np.append(np.arange(label2_row+i*13), np.arange(label2_row+9+i*13,275)), usecols="A:D", index_col=0) 
            eyfp[1][i+6] = pd.read_excel(file, skiprows=np.append(np.arange(label2_row+i*13), np.arange(label2_row+9+i*13,275)), usecols="A,H:J", index_col=0) 
        
        if table3_exist:
            rluc[2][i] = pd.read_excel(file, skiprows=np.append(np.arange(label1_row+i*13), np.arange(label1_row+9+i*13,275)), usecols="A:D", index_col=0) 
            rluc[2][i+6] = pd.read_excel(file, skiprows=np.append(np.arange(label1_row+i*13), np.arange(label1_row+9+i*13,275)), usecols="A,K:M", index_col=0) 
            eyfp[2][i] = pd.read_excel(file, skiprows=np.append(np.arange(label2_row+i*13), np.arange(label2_row+9+i*13,275)), usecols="A:D", index_col=0) 
            eyfp[2][i+6] = pd.read_excel(file, skiprows=np.append(np.arange(label2_row+i*13), np.arange(label2_row+9+i*13,275)), usecols="A,K:M", index_col=0) 
    
    return rluc, eyfp, table2_exist, table3_exist 

@st.cache
# calculate bret
def get_bret(rluc, eyfp):
    bret = {}
    for i in range(12):
        bret[i] = eyfp[i].divide(rluc[i])

    corrected_bret = {}
    for i in range(12):
        corrected_bret[i] = bret[i].mean(1)

    bret_ratio = {}
    for i in range(6):
        bret_ratio[i] = corrected_bret[i+6].subtract(corrected_bret[i])

    avg_bret_ratio = bret_ratio[0]
    for i in range(1,6):
        avg_bret_ratio = avg_bret_ratio.add(bret_ratio[i])
    avg_bret_ratio = avg_bret_ratio.divide(6) 

    return bret, corrected_bret, bret_ratio, avg_bret_ratio

def plot_abs_graph(bret_ratio, avg_bret_ratio, xlabel):
    #merge all bret table to calucate SD for error bar
    sd = bret_ratio[0].to_frame() 
    for i in range(1,6):
        df = bret_ratio[i].to_frame()
        df.columns = [i]
        sd = pd.concat([sd, df], axis=1) 
    sd = sd.std(axis = 1)
    
    # plot bar graph and error bar
    fig,ax = plt.subplots()
    ax.bar(range(1,9), avg_bret_ratio)
    pline, capline, barlinecols = ax.errorbar(range(1,9), avg_bret_ratio, yerr = sd, color = 'black',capsize=3, linestyle='', lolims=True)
    y_bottom_lim = avg_bret_ratio.min() * 0.97
    ax.set_ylim(bottom = y_bottom_lim, top = (sd.add(avg_bret_ratio).max() - y_bottom_lim) * 1.05 + y_bottom_lim)
    plt.xlabel(xlabel)
    plt.ylabel('BRET Ratio')
    capline[0].set_marker('_')
    capline[0].set_markersize(10)

    return fig 
    
def plot_relative_graph(bret, ref_pt, xlabel):
    # calculate avg of BRET of Rluc8
    avg1 = bret[0]
    for i in range(1,6):
        avg1 = avg1.add(bret[i])
    avg1 = avg1.divide(6)

    # calculate avg of BRET of eYFP
    avg2 = bret[6]
    for i in range(7, 12):
        avg2 = avg2.add(bret[i])
    avg2 = avg2.divide(6)
    
    # calculate relative y_axis and sd from avg1 and avg2
    avg2.columns = ['1','2','3']
    y_axis = avg2.subtract(avg1).divide(ref_pt).multiply(100)
    sd = y_axis.std(axis = 1)
    y_axis = y_axis.mean(1)

    # plot relative bar graph and error bar
    fig,ax = plt.subplots()
    ax.bar(range(1,9), y_axis)
    ax.set_ylim(bottom = y_axis.min() * 0.97, top = (sd.add(y_axis).max() - y_axis.min() * 0.97) * 1.05 + y_axis.min() * 0.97 )
    pline, capline, barlinecols = plt.errorbar(range(1,9), y_axis, yerr = sd, color = 'black',capsize=3, linestyle='', lolims=True)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter())
    plt.xlabel(xlabel)
    plt.ylabel('BRET Ratio')

    capline[0].set_marker('_')
    capline[0].set_markersize(10)

    return fig

def generate_download_button(fig):
    # save grpah for download
    img = io.BytesIO()
    pp = PdfPages(img)
    pp.savefig(fig)
    pp.close()

    # crete a download button
    btn = st.download_button(
        label="Download graph as PDF",
        data=img,
        file_name="BERT_result.pdf",
        mime="image/pdf"
    )




# streamlit start ########################
st.set_page_config(page_title="BRET Calculator", layout="centered")
st.title("BRET Calculator")

# ask for input and file
file = st.file_uploader("Excel File")

if (not file):
    st.stop()

# calculate rluc, eyfp, brets 
rluc, eyfp, table2_exist, table3_exist = readfile(file)

bret = {}
corrected_bret = {}
bret_ratio = {}
avg_bret_ratio = {}
for i in range(3):
    if ((i == 1 and not table2_exist) or (i == 2 and not table3_exist)):
        continue
    bret[i], corrected_bret[i], bret_ratio[i], avg_bret_ratio[i] = get_bret(rluc[i], eyfp[i])

# ask for method (relavtive / absolute) and x-axis label
with st.sidebar:
    method = st.selectbox("Relative / Absolute :",['Relative', 'Absolute'])
    xlabel = {}
    xlabel[0] = st.text_input('X Label 1', 'X Axis')
    if (table2_exist):
        xlabel[1] = st.text_input('X Label 2', 'X Axis')
    if (table3_exist):
        xlabel[2] = st.text_input('X Label 3', 'X Axis')

# plot and save graph
if method == 'Absolute':
    for i in range(3):
        if ((i == 1 and not table2_exist) or (i == 2 and not table3_exist)):
            continue
        fig = plot_abs_graph(bret_ratio[i], avg_bret_ratio[i], xlabel[i])
        st.pyplot(fig)
        generate_download_button(fig)

elif method == 'Relative':
    for i in range(3):
        if ((i == 1 and not table2_exist) or (i == 2 and not table3_exist)):
            continue
        fig = plot_relative_graph(bret[i], avg_bret_ratio[i][0], xlabel[i])
        st.pyplot(fig)
        generate_download_button(fig)

