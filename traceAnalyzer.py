import subprocess
import sys

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Versuche, die benötigten Pakete zu importieren, und installiere sie, falls sie fehlen
try:
    import pandas as pd
except ImportError:
    install('pandas')
    import pandas as pd

try:
    import numpy as np
except ImportError:
    install('numpy')
    import numpy as np

try:
    import matplotlib.pyplot as plt
except ImportError:
    install('matplotlib')
    import matplotlib.pyplot as plt

from tkinter import Tk, Checkbutton, Button, Entry, Label, IntVar, Frame, Scrollbar, VERTICAL, filedialog
try:
    from matplotlib.widgets import SpanSelector
except ImportError:
    install('matplotlib')
    from matplotlib.widgets import SpanSelector

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from tkinter import Tk, Checkbutton, Button, Entry, Label, IntVar, Frame, Scrollbar, VERTICAL, filedialog
from matplotlib.widgets import SpanSelector
import sys

def read_target_data(filepath):
    with open(filepath, 'r') as file:
        lines = file.readlines()

    variable_names = []
    data_lines = []
    header_lines = []
    reading_data = False

    for line in lines:
        line = line.strip()
        if line.startswith('%'):
            header_lines.append(line)
            if 'TARGET_DATA' in line:
                parts = line.split('TARGET_DATA')
                if len(parts) > 1:
                    var_name = parts[1].split(',')[0].strip()
                    variable_names.append(var_name)
        elif line:
            data_lines.append(line)
            reading_data = True

    if reading_data:
        data = pd.DataFrame([list(map(float, filter(None, line.split(',')))) for line in data_lines])
        time_data = data.iloc[:, 0::2]
        value_data = data.iloc[:, 1::2]
    else:
        time_data = pd.DataFrame()
        value_data = pd.DataFrame()

    return time_data, value_data, variable_names, header_lines

def export_data(combined_data, start, end, filepath, header_lines):
    selected_data = combined_data.iloc[start:end+1]
    num_columns = len(combined_data.columns)
    num_pairs = num_columns // 2
    with open(filepath, 'w') as file:
        for line in header_lines:
            file.write(line + '\n')
        for index, row in selected_data.iterrows():
            line = ''
            for i in range(num_pairs):
                time_col = combined_data.columns[i]
                value_col = combined_data.columns[num_pairs + i]
                line += f"{row[time_col]},{row[value_col]},"
            file.write(line.rstrip(',') + '\n')

def plot_data(time_data, value_data, variable_names, selections, scales, offsets, header_lines):
    fig, ax = plt.subplots(figsize=(10, 5))
    lines = []
    for i, (selected, scale, offset) in enumerate(zip(selections, scales, offsets)):
        if selected.get():
            scaled_data = value_data.iloc[:, i] * float(scale.get()) + float(offset.get())
            line, = ax.plot(time_data.iloc[:, i], scaled_data, label=variable_names[i])
            lines.append(line)
    ax.set_xlabel('Time')
    ax.set_ylabel('Value')
    ax.set_title('Data Plot')
    ax.legend()
    ax.grid(True)
    plt.draw()

    def onselect(xmin, xmax):
        indmin, indmax = np.searchsorted(time_data.iloc[:, 0], (xmin, xmax))
        indmax = min(len(time_data) - 1, indmax)
        export_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if export_path:
            export_data(pd.concat([time_data, value_data], axis=1), indmin, indmax, export_path, header_lines)

    span = SpanSelector(ax, onselect, 'horizontal', useblit=True)

    plt.show()

def gui():
    root = Tk()
    root.title("Signal Analyzer")

    filepath = filedialog.askopenfilename(title="Select file", filetypes=[("CSV files", "*.csv")])
    if not filepath:
        return

    time_data, value_data, variable_names, header_lines = read_target_data(filepath)

    frame = Frame(root)
    frame.pack(fill='both', expand=True)

    scrollbar = Scrollbar(frame, orient=VERTICAL)
    scrollbar.pack(side='right', fill='y')

    selections = []
    scale_entries = []
    offset_entries = []

    for name in variable_names:
        var_frame = Frame(frame)
        var_frame.pack(fill='x')

        selected = IntVar(value=1)
        chk = Checkbutton(var_frame, text=name, variable=selected)
        chk.pack(side='left')

        scale_label = Label(var_frame, text="Scale:")
        scale_label.pack(side='left')

        scale_entry = Entry(var_frame, width=5)
        scale_entry.insert(0, '1.0')
        scale_entry.pack(side='left')

        offset_label = Label(var_frame, text="Offset:")
        offset_label.pack(side='left')

        offset_entry = Entry(var_frame, width=5)
        offset_entry.insert(0, '0.0')
        offset_entry.pack(side='left')

        selections.append(selected)
        scale_entries.append(scale_entry)
        offset_entries.append(offset_entry)

    def on_show():
        plot_data(time_data, value_data, variable_names, selections, scale_entries, offset_entries, header_lines)

    show_button = Button(root, text="Anzeigen", command=on_show)
    show_button.pack()

    root.mainloop()

if __name__ == "__main__":
    gui()