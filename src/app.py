from flask import Flask, render_template, Response
import threading
import time
import pandas as pd
import math
import matplotlib.pyplot as plt
import io
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from load_checking import start_load_checking
from db_interactions import ensure_db_exist, get_loads_df



db_name = 'mysqlite.db'

ensure_db_exist(db_name)  

thread = threading.Thread(target=start_load_checking, args=(db_name, 5))
thread.start()

plt.rcParams["figure.figsize"] = [7.50, 5.50]
plt.rcParams["figure.autolayout"] = True

my_app = Flask(__name__)

@my_app.route('/')
def page():
    return render_template('index.html')
    
@my_app.route('/get_graphs', methods=['POST'])
def plot_graphs():
    current_time = time.time_ns()
    bound_time = current_time - 60*60*10**9

    loads_df = get_loads_df(db_name, bound_time)
    fig, axis = plt.subplots(2)
    loads_df.index = pd.Series([pd.Timestamp(i, tz='Europe/Moscow') for i in loads_df.index])
    times = (loads_df.index).tolist()
    times = [i.to_pydatetime() for i in times]
    current_time = pd.Timestamp(current_time, tz='Europe/Moscow').to_pydatetime()
    bound_time = pd.Timestamp(bound_time, tz='Europe/Moscow').to_pydatetime()
    row_loads = loads_df['percent'].tolist()
    axis[0].plot(times, row_loads, marker="o", markersize=1)
    axis[0].set_title('Row data')
    axis[0].set_xlim([bound_time, current_time])
    axis[0].grid()
    
    smooth_loads = loads_df.rolling('1min').mean()['percent'].tolist()
    for i in range(len(smooth_loads)):
        if math.isnan(row_loads[i]):
            smooth_loads[i] = math.nan
    axis[1].plot(times, smooth_loads, marker="o", markersize=1)
    axis[1].set_title('Smooth data')
    axis[1].set_xlim([bound_time, current_time])
    axis[1].grid()
    
    output = io.BytesIO()
    FigureCanvas(fig).print_png(output)
    image = output.getvalue()
    output.close()
    return Response(image, mimetype='image/png')