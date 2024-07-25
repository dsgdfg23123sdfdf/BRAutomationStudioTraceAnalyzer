import subprocess
import sys

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Install the specified Python package using pip.
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
                target_data_index = line.find('TARGET_DATA') + len('TARGET_DATA')
                unitx_index = line.find('XUNIT', target_data_index)
                if target_data_index != -1 and unitx_index != -1:
                    var_name = line[target_data_index:unitx_index].strip()
                    var_name = ' '.join(var_name.split())
                    variable_names.append(var_name)
                    print("Debug: Extracted variable name:", var_name)
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

def plot_data(time_data, value_data, variable_names, selections, scales, offsets, header_lines, fig, ax, initial=False):
    print("Debug: Plotting data...")
    if not initial:
        current_xlim = ax.get_xlim()
        current_ylim = ax.get_ylim()

    ax.clear()

    lines = []
    for i, (selected, scale, offset) in enumerate(zip(selections, scales, offsets)):
        if selected.get():
            print(f"Debug: Plotting variable {variable_names[i]}")
            scaled_data = value_data.iloc[:, i] * float(scale.get()) + float(offset.get())
            line, = ax.plot(time_data.iloc[:, i], scaled_data, label=variable_names[i])
            lines.append(line)
        else:
            print(f"Debug: Skipping variable {variable_names[i]}")

    ax.set_xlabel('Time')
    ax.set_ylabel('Value')
    ax.set_title('Data Plot')
    ax.legend()
    ax.grid(True)

    if initial:
        ax.set_xlim(time_data.min().min(), time_data.max().max())
        ax.set_ylim(value_data.min().min(), value_data.max().max())
    else:
        ax.set_xlim(current_xlim)
        ax.set_ylim(current_ylim)

    fig.canvas.draw()

    if not lines:
        print("Debug: No lines to plot.")  # Debug-Ausgabe

    # Cursors initialization
    cursor1 = ax.axvline(x=time_data.iloc[0, 0], color='r', linestyle='--')
    cursor2 = ax.axvline(x=time_data.iloc[0, 0], color='g', linestyle='--')
    cursor_values = {cursor1: {}, cursor2: {}}

    def on_click(event):
        if event.inaxes != ax:
            return  # Ignore clicks outside the axes

        if event.button == 1 and event.key == 'control':  # Check if the Control key is pressed
            cursor1.set_xdata([event.xdata])
            update_cursor_values(cursor1, lines, ax, cursor_values)

        elif event.button == 3:  # Right mouse button for Cursor 2
            cursor2.set_xdata([event.xdata])
            update_cursor_values(cursor2, lines, ax, cursor_values)

        update_time_difference(cursor1, cursor2, ax)
        update_legend(lines, ax, cursor_values, cursor1, cursor2, variable_names, selections)  # Corrected line
        fig.canvas.draw()

    fig.canvas.mpl_connect('button_press_event', on_click)
    plt.show()

def update_cursor_values(cursor, lines, ax, cursor_values):
    x_pos = cursor.get_xdata()[0]
    for i, line in enumerate(lines):
        x_data = line.get_xdata()
        y_data = line.get_ydata()
        nearest_index = np.searchsorted(x_data, x_pos)
        nearest_index = min(max(nearest_index, 0), len(x_data) - 1)
        y_value = y_data[nearest_index]
        cursor_values[cursor][i] = f'{y_value:.2f}'

def update_legend(lines, ax, cursor_values, cursor1, cursor2, variable_names, selections):
    # Update the legend to display only selected variables
    new_labels = []
    for i, line in enumerate(lines):
        if selections[i].get():  # Check if the variable is selected
            value1 = cursor_values[cursor1].get(i, 'N/A')
            value2 = cursor_values[cursor2].get(i, 'N/A')
            new_label = f'{variable_names[i]}: {value1} | {value2}'
            new_labels.append(new_label)
        else:
            line.set_visible(False)  # Hide lines that are not selected

    ax.legend(lines, new_labels)  # Set the new legend with the updated labels

def update_time_difference(cursor1, cursor2, ax):
    x1 = cursor1.get_xdata()[0]
    x2 = cursor2.get_xdata()[0]
    time_diff = abs(x2 - x1)
    ax.set_title(f'Data Plot - Time difference: {time_diff:.2f} seconds')

def gui():
    root = Tk()
    root.title("Signal Analyzer")

    frame = Frame(root)
    frame.pack(fill='both', expand=True)

    scrollbar = Scrollbar(frame, orient=VERTICAL)
    scrollbar.pack(side='right', fill='y')

    fig, ax = plt.subplots(figsize=(10, 5))

    # Variables for storing data and GUI elements
    selections = []
    scale_entries = []
    offset_entries = []
    variable_names = []
    time_data = pd.DataFrame()
    value_data = pd.DataFrame()
    header_lines = []

    def on_change(event=None):
        plot_data(time_data, value_data, variable_names, selections, scale_entries, offset_entries, header_lines, fig, ax, initial=False)

    def on_change_wrapper():
        on_change()  # Calls on_change without arguments

    def load_and_plot_data():
        nonlocal time_data, value_data, variable_names, header_lines, selections, scale_entries, offset_entries
        filepath = filedialog.askopenfilename(title="Select file", filetypes=[("CSV files", "*.csv")])
        if filepath:
            time_data, value_data, variable_names, header_lines = read_target_data(filepath)

            # Remove old GUI elements
            for widget in frame.winfo_children():
                widget.destroy()

            # Re-create GUI elements for the variables
            selections = []
            scale_entries = []
            offset_entries = []
            for name in variable_names:
                var_frame = Frame(frame)
                var_frame.pack(fill='x')

                selected = IntVar(value=1)
                chk = Checkbutton(var_frame, text=name, variable=selected, command=on_change_wrapper)
                chk.pack(side='left')

                scale_label = Label(var_frame, text="Scale:")
                scale_label.pack(side='left')

                scale_entry = Entry(var_frame, width=5)
                scale_entry.insert(0, '1.0')
                scale_entry.pack(side='left')
                scale_entry.bind('<Return>', on_change)

                offset_label = Label(var_frame, text="Offset:")
                offset_label.pack(side='left')

                offset_entry = Entry(var_frame, width=5)
                offset_entry.insert(0, '0.0')
                offset_entry.pack(side='left')
                offset_entry.bind('<Return>', on_change)

                selections.append(selected)
                scale_entries.append(scale_entry)
                offset_entries.append(offset_entry)

            plot_data(time_data, value_data, variable_names, selections, scale_entries, offset_entries, header_lines, fig, ax, initial=True)

    # Button to load a new file
    load_button = Button(root, text="Load Data", command=load_and_plot_data)
    load_button.pack()

    root.mainloop()

if __name__ == "__main__":
    gui()