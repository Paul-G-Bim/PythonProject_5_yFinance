from tkinter import ttk, messagebox, filedialog
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from typing import Dict, Optional


# -----------------------------
# Fetch cryptocurrency data
# -----------------------------
def fetch_crypto_data(symbols, period="1mo", interval="1d"):
    data_dict = {}
    for sym in symbols:
        try:
            # Explicitly setting auto_adjust=True to silence the yfinance FutureWarning
            data: pd.DataFrame = yf.download(sym, period=period, interval=interval, progress=False, auto_adjust=True)

            if data is not None and not data.empty:
                data["Symbol"] = sym
                data_dict[sym] = data
        except Exception as e:
            print(f"Error fetching data for {sym}: {e}")
    return data_dict


# -----------------------------
# Global variables (with Type Hints)
# -----------------------------
latest_summary_df: Optional[pd.DataFrame] = None
latest_combined_data: Optional[Dict[str, pd.DataFrame]] = None


# -----------------------------
# Export summary CSV
# -----------------------------
def export_summary_to_csv():
    global latest_summary_df
    if latest_summary_df is None or latest_summary_df.empty:
        messagebox.showinfo("No Data", "Please fetch data before exporting.")
        return

    file_path = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv")],
        title="Save Summary CSV File",
        initialfile="crypto_summary.csv"
    )
    if not file_path:
        return

    try:
        latest_summary_df.to_csv(file_path, index=False)
        messagebox.showinfo("Export Successful", f"Summary exported successfully to:\n{file_path}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to export CSV:\n{e}")


# -----------------------------
# Export full historical CSV
# -----------------------------
def export_full_data_to_csv():
    global latest_combined_data
    if latest_combined_data is None:
        messagebox.showinfo("No Data", "Please fetch data before exporting full historical dataset.")
        return

    file_path = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv")],
        title="Save Full Data CSV File",
        initialfile="crypto_full_data.csv"
    )
    if not file_path:
        return

    try:
        combined_df = pd.concat(latest_combined_data.values())
        combined_df.reset_index(inplace=True)
        combined_df.to_csv(file_path, index=False)
        messagebox.showinfo("Export Successful", f"Full historical data exported to:\n{file_path}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to export full dataset:\n{e}")


# -----------------------------
# Plot and summarize performance
# -----------------------------
def display_crypto_data():
    global latest_summary_df, latest_combined_data

    symbols = [s.strip() for s in crypto_entry.get().split(",") if s.strip()]
    if not symbols:
        messagebox.showwarning("Input Error", "Please enter at least one cryptocurrency symbol.")
        return

    period = period_combo.get()
    interval = interval_combo.get()

    try:
        combined_data = fetch_crypto_data(symbols, period, interval)
        if not combined_data:
            messagebox.showerror("Error", "No valid data fetched. Check your symbols or internet connection.")
            return

        latest_combined_data = combined_data

        # --- Clear old content ---
        for widget in content_frame.winfo_children():
            widget.destroy()

        # --- Plot section ---
        fig, ax = plt.subplots(figsize=(8, 4))
        for sym, data in combined_data.items():
            ax.plot(data.index, data["Close"], label=sym)

        ax.set_title("Cryptocurrency Performance", fontsize=12)
        ax.set_xlabel("Date")
        ax.set_ylabel("Price (USD)")
        ax.legend()
        ax.grid(True, linestyle="--", alpha=0.5)

        canvas = FigureCanvasTkAgg(fig, master=content_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

        # --- Summary Table ---
        summary_data = []
        for sym, data in combined_data.items():
            try:
                if "Close" not in data or data["Close"].empty:
                    continue

                # Using .to_numpy().flatten() to safely extract the scalar price value
                # This clears the pandas FutureWarning
                start_price = float(data["Close"].to_numpy().flatten()[0])
                end_price = float(data["Close"].to_numpy().flatten()[-1])

                if start_price == 0:
                    continue
                change_pct = float(((end_price - start_price) / start_price) * 100)
                summary_data.append([
                    sym,
                    round(start_price, 2),
                    round(end_price, 2),
                    f"{change_pct:.2f}%"
                ])
            except Exception as e:
                print(f"Skipping {sym} due to data error: {e}")

        if not summary_data:
            messagebox.showinfo("Info", "No summary data available for selected symbols.")
            return

        summary_df = pd.DataFrame(summary_data, columns=["Symbol", "Start Price", "End Price", "% Change"])
        latest_summary_df = summary_df

        # Using tb.Labelframe to comply with ttkbootstrap styling and clear linter warnings
        summary_frame = tb.Labelframe(content_frame, text="Summary Performance", bootstyle=SUCCESS)
        summary_frame.pack(side="bottom", fill="x", padx=10, pady=10)

        summary_tree = ttk.Treeview(summary_frame, columns=list(summary_df.columns), show="headings", height=5)
        summary_tree.pack(fill="x")

        for col in summary_df.columns:
            summary_tree.heading(col, text=col)
            summary_tree.column(col, width=150)

        for _, row in summary_df.iterrows():
            summary_tree.insert("", "end", values=list(row))

        # --- Export Buttons ---
        button_frame = ttk.Frame(summary_frame)
        button_frame.pack(pady=8)

        # Using tb.Button to comply with ttkbootstrap styling and clear linter warnings
        export_summary_btn = tb.Button(
            button_frame, text="💾 Export Summary to CSV", bootstyle=INFO, command=export_summary_to_csv
        )
        export_summary_btn.pack(side="left", padx=10)

        # Using tb.Button to comply with ttkbootstrap styling and clear linter warnings
        export_full_btn = tb.Button(
            button_frame, text="📈 Export Full Historical Data", bootstyle=SECONDARY, command=export_full_data_to_csv
        )
        export_full_btn.pack(side="left", padx=10)

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")


# -----------------------------
# Define the exit handler (New Fix)
# -----------------------------
def on_closing():
    """Handles cleanup and termination of the application safely."""
    try:
        root.destroy()
        root.quit()
    except Exception:
        # Avoid crashing on shutdown errors
        pass


# -----------------------------
# Build GUI
# -----------------------------
root = tb.Window(themename="darkly")
root.title("📊 Crypto Performance Dashboard")
root.geometry("950x700")

# --- Top input frame ---
input_frame = ttk.Frame(root, padding=10)
input_frame.pack(fill="x")

ttk.Label(input_frame, text="Enter Crypto Symbols (comma separated):").pack(side="left", padx=5)
crypto_entry = ttk.Entry(input_frame, width=40)
crypto_entry.pack(side="left", padx=5)
crypto_entry.insert(0, "BTC-USD, ETH-USD, SOL-USD")

# --- Period dropdown ---
ttk.Label(input_frame, text="Period:").pack(side="left", padx=5)
period_combo = ttk.Combobox(input_frame, values=["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y"], width=7)
period_combo.current(2)
period_combo.pack(side="left", padx=5)

# --- Interval dropdown ---
ttk.Label(input_frame, text="Interval:").pack(side="left", padx=5)
interval_combo = ttk.Combobox(input_frame, values=["1h", "1d", "1wk"], width=7)
interval_combo.current(1)
interval_combo.pack(side="left", padx=5)

# Using tb.Button to comply with ttkbootstrap styling and clear linter warnings
fetch_btn = tb.Button(input_frame, text="Show Performance", command=display_crypto_data, bootstyle=PRIMARY)
fetch_btn.pack(side="left", padx=10)

# --- Content frame (Graph + Table) ---
content_frame = ttk.Frame(root, padding=10)
content_frame.pack(fill="both", expand=True)

# --- Footer ---
footer_label = ttk.Label(
    root,
    text="Built with 💻 Python + yFinance + ttkbootstrap | Crypto Dashboard © 2025",
    anchor="center",
    font=("Segoe UI", 9),
)
footer_label.pack(side="bottom", pady=5)

# --- Bind the protocol for clean exit ---
root.protocol("WM_DELETE_WINDOW", on_closing)

# --- Start app ---
root.mainloop()