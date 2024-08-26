import os
import datetime
import sys
import csv
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog,
    QMessageBox, QLabel, QHBoxLayout, QSpacerItem, QSizePolicy,
    QTableWidget, QTableWidgetItem, QTabWidget, QLineEdit, QFormLayout,
    QSplitter, QProgressDialog
)
from PyQt5.QtGui import QIcon, QFont, QPixmap
from PyQt5.QtCore import Qt
from fpdf import FPDF


class CSVProcessor(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Set window title and icon
        self.setWindowTitle('CSV Processor & Monitor')
        self.setWindowIcon(QIcon('icon.png'))

        # Layouts
        main_layout = QVBoxLayout()
        button_layout = QHBoxLayout()
        search_layout = QFormLayout()

        # Create a horizontal layout for the logo
        logo_layout = QHBoxLayout()

        # Image Label
        self.image_label = QLabel(self)
        self.image_label.setPixmap(QPixmap('peruri.png'))
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setScaledContents(True)
        self.image_label.setFixedSize(300, 200)
        logo_layout.addWidget(self.image_label)
        logo_layout.setAlignment(Qt.AlignCenter)

        # Add the logo layout to the main layout
        main_layout.addLayout(logo_layout)

        # Text Label
        self.label = QLabel('Select file to process')
        self.label.setFont(QFont('Arial', 14))
        self.label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.label)

        # Button Layout
        button_layout.addSpacerItem(QSpacerItem(
            40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        # Select file button
        self.btn_select_file = QPushButton('Select File', self)
        self.btn_select_file.setFont(QFont('Arial', 12))
        self.btn_select_file.setIcon(QIcon('select_file_icon.png'))
        self.btn_select_file.clicked.connect(self.select_file)
        button_layout.addWidget(self.btn_select_file)

        # Process file button
        self.btn_process = QPushButton('Process File', self)
        self.btn_process.setFont(QFont('Arial', 12))
        self.btn_process.setIcon(QIcon('right_arrow_icon.png'))
        self.btn_process.clicked.connect(self.process_file)
        self.btn_process.setEnabled(False)
        button_layout.addWidget(self.btn_process)

        # Export Good Data to PDF button
        self.btn_export_pdf_good = QPushButton('Export Good Data to PDF', self)
        self.btn_export_pdf_good.setFont(QFont('Arial', 12))
        self.btn_export_pdf_good.setIcon(QIcon('export_pdf_icon.png'))
        self.btn_export_pdf_good.clicked.connect(self.export_to_pdf_good)
        self.btn_export_pdf_good.setEnabled(False)
        button_layout.addWidget(self.btn_export_pdf_good)

        # Export Defect Data to PDF button
        self.btn_export_pdf_defect = QPushButton(
            'Export Defect Data to PDF', self)
        self.btn_export_pdf_defect.setFont(QFont('Arial', 12))
        self.btn_export_pdf_defect.setIcon(QIcon('export_pdf_icon.png'))
        self.btn_export_pdf_defect.clicked.connect(self.export_to_pdf_defect)
        self.btn_export_pdf_defect.setEnabled(False)
        button_layout.addWidget(self.btn_export_pdf_defect)

        button_layout.addSpacerItem(QSpacerItem(
            40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        # Add the button layout to the main layout
        main_layout.addLayout(button_layout)

        # Search Bar
        self.search_bar = QLineEdit(self)
        self.search_bar.setPlaceholderText("Search...")
        self.search_bar.setFont(QFont('Arial', 12))
        self.search_bar.textChanged.connect(self.filter_data)
        search_layout.addRow(QLabel("Search:"), self.search_bar)

        # Add the search layout to the main layout
        main_layout.addLayout(search_layout)

        # Tabs for displaying data
        self.tabs = QTabWidget(self)
        self.good_data_table = QTableWidget()
        self.defect_data_table = QTableWidget()

        self.tabs.addTab(self.good_data_table, "Good Data")
        self.tabs.addTab(self.defect_data_table, "Defect Data")

        # Summary Tab
        self.summary_tab = QWidget()
        self.summary_layout = QVBoxLayout()
        self.summary_tab.setLayout(self.summary_layout)

        self.summary_tabs = QTabWidget()
        self.summary_tabs.addTab(self.summary_tab, "Summary")

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.tabs)
        splitter.addWidget(self.summary_tabs)
        main_layout.addWidget(splitter)

        # Set layout and window size
        self.setLayout(main_layout)
        self.setMinimumSize(1000, 600)
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 10px;
                padding: 10px 20px;
            }
            QPushButton:disabled {
                background-color: #9E9E9E;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QLabel {
                color: #333;
            }
            QTableWidget {
                background-color: white;
                font-size: 14px;
            }
        """)

    def select_file(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Select trace.txt file", "", "Text Files (*.txt);;All Files (*)", options=options)
        if file_name:
            self.file_path = file_name
            self.label.setText(f"Selected file: {file_name}")
            self.btn_process.setEnabled(True)

    def process_file(self):
        try:
            # Setup progress dialog
            progress_dialog = QProgressDialog(
                "Processing...", "Cancel", 0, 100, self)
            progress_dialog.setWindowModality(Qt.WindowModal)
            progress_dialog.setMinimumDuration(0)
            progress_dialog.setValue(0)
            progress_dialog.show()

            with open(self.file_path, 'r') as file:
                data = file.read()

            # Hapus baris pertama dan terakhir
            lines = data.splitlines()[1:-1]

            self.cleaned_data_good = []
            self.cleaned_data_defect = []

            total_lines = len(lines)
            progress_step = 100 / total_lines if total_lines else 0
            current_progress = 0

            for i, line in enumerate(lines):
                if progress_dialog.wasCanceled():
                    QMessageBox.warning(self, "Cancelled",
                                        "Operation cancelled.")
                    return

                row = line.replace("-", "").replace("*", "").split(";")
                row = [item.strip() for item in row if item.strip()]

                if row:
                    if len(row) == 24:
                        self.cleaned_data_good.append(row)
                    else:
                        self.cleaned_data_defect.append(row)

                # Update progress
                current_progress += progress_step
                progress_dialog.setValue(int(current_progress))

            # Create folder based on today's date
            today = datetime.datetime.now().strftime('%Y-%m-%d')
            folder_path = os.path.join(os.getcwd(), today)

            if not os.path.exists(folder_path):
                os.makedirs(folder_path)

            # Prepare file paths
            good_csv_filename = os.path.join(folder_path, 'good_output.csv')
            defect_csv_filename = os.path.join(
                folder_path, 'defect_output.csv')

            # Save good data CSV
            with open(good_csv_filename, mode='w', newline='') as file:
                writer = csv.writer(file)
                for row in self.cleaned_data_good:
                    writer.writerow(row)

            # Save defect data CSV
            with open(defect_csv_filename, mode='w', newline='') as file:
                writer = csv.writer(file)
                for row in self.cleaned_data_defect:
                    writer.writerow(row)

            # Complete progress
            progress_dialog.setValue(100)

            self.btn_export_pdf_good.setEnabled(True)
            self.btn_export_pdf_defect.setEnabled(True)

            # Generate summary chart
            self.generate_summary_chart()

            # Load data into tables
            self.load_csv_to_table(good_csv_filename, self.good_data_table)
            self.load_csv_to_table(defect_csv_filename, self.defect_data_table)

            QMessageBox.information(
                self, "Success", f"Data processed successfully.\nGood data saved in:        {good_csv_filename}\nDefect data saved in: {defect_csv_filename}")
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to process file: {str(e)}")

    def load_csv_to_table(self, file_path, table_widget):
        try:
            with open(file_path, 'r') as file:
                reader = csv.reader(file)
                data = list(reader)
                self.populate_table(table_widget, data)
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to load CSV file: {str(e)}")

    def populate_table(self, table_widget, data):
        table_widget.clear()
        if data:
            table_widget.setColumnCount(len(data[0]))
            table_widget.setRowCount(len(data))

            for row_num, row_data in enumerate(data):
                for col_num, item in enumerate(row_data):
                    table_widget.setItem(
                        row_num, col_num, QTableWidgetItem(item))

            headers = [f"Column {i+1}" for i in range(len(data[0]))]
            table_widget.setHorizontalHeaderLabels(headers)

    def generate_summary_chart(self):
        if not hasattr(self, 'cleaned_data_good') or not hasattr(self, 'cleaned_data_defect'):
            return

        # Example pie chart generation
        good_data_count = len(self.cleaned_data_good)
        defect_data_count = len(self.cleaned_data_defect)

        total_count = good_data_count + defect_data_count
        if total_count == 0:
            return  # Avoid division by zero if no data

        fig, ax = plt.subplots()
        categories = ['Good Data', 'Defect Data']
        counts = [good_data_count, defect_data_count]
        percentages = [(count / total_count) * 100 for count in counts]

        wedges, texts, autotexts = ax.pie(counts, labels=categories, autopct='%1.1f%%', colors=[
            'green', 'red'], startangle=140)
        ax.set_title('Summary Pie Chart')

        # Style the labels
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(10)
        for text in texts:
            text.set_fontsize(12)

        # Add the summary text
        fig.text(0.05, 0.05, f"Total Data: {total_count}\nGood Data: {good_data_count}\nDefect Data: {defect_data_count}",
                 fontsize=12, verticalalignment='bottom', horizontalalignment='left', bbox=dict(facecolor='white', alpha=0.8))

        # Clear the previous chart and add the new one
        for i in reversed(range(self.summary_tab.layout().count())):
            widget = self.summary_tab.layout().itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        canvas = FigureCanvas(fig)
        self.summary_tab.layout().addWidget(canvas)
        canvas.draw()

    def export_to_pdf_good(self):
        try:
            # Initialize progress dialog
            progress = QProgressDialog(
                "Exporting to PDF and CSV...", "Cancel", 0, 100, self)
            progress.setWindowModality(Qt.WindowModal)
            progress.setMinimumDuration(0)
            progress.setValue(0)

            pdf = FPDF()
            pdf.add_page()

            # Title
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(0, 10, "Good Data Report", ln=True, align='C')

            # Header
            pdf.set_font("Arial", 'B', 6)
            pdf.cell(10, 10, "Jumlah", 1, 0, 'C')  # Jumlah total data
            pdf.cell(30, 10, "No", 1, 0, 'C')  # Nomor urut data
            pdf.cell(30, 10, "TGL", 1, 0, 'C')
            pdf.cell(30, 10, "STATUS 1", 1, 0, 'C')
            pdf.cell(30, 10, "STATUS 2", 1, 0, 'C')
            pdf.cell(30, 10, "NOMOR SERI BANKNOTE", 1, 0, 'C')
            pdf.cell(30, 10, "DATA ID", 1, 0, 'C')
            pdf.ln()

            # Data
            pdf.set_font("Arial", '', 6)
            total_rows = len(self.cleaned_data_good)
            for i, row in enumerate(self.cleaned_data_good, start=1):
                if progress.wasCanceled():
                    QMessageBox.warning(self, "Cancelled",
                                        "Export was cancelled")
                    return

                pdf.cell(10, 10, str(i), 1, 0, 'C')  # Nomor urut data
                pdf.cell(30, 10, row[0], 1, 0, 'C')
                pdf.cell(30, 10, row[3], 1, 0, 'C')
                pdf.cell(30, 10, row[18], 1, 0, 'C')
                pdf.cell(30, 10, row[20], 1, 0, 'C')
                pdf.cell(30, 10, row[22], 1, 0, 'C')
                pdf.cell(30, 10, row[23], 1, 0, 'C')
                pdf.ln()

                # Update progress dialog
                progress.setValue(int(i / total_rows * 100))
                QApplication.processEvents()  # Allow dialog to update

            # Create folder based on today's date
            today = datetime.datetime.now().strftime('%Y-%m-%d')
            folder_path = os.path.join(os.getcwd(), today)

            if not os.path.exists(folder_path):
                os.makedirs(folder_path)

            # Prepare file paths
            output_filename_pdf = os.path.join(
                folder_path, 'good_data_output.pdf')
            output_filename_csv = os.path.join(
                folder_path, 'good_data_output.csv')

            # Output PDF
            pdf.output(output_filename_pdf)

            # Export to CSV
            with open(output_filename_csv, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["Jumlah", "No", "TGL", "STATUS 1",
                                "STATUS 2", "NOMOR SERI BANKNOTE", "DATA ID"])
                for i, row in enumerate(self.cleaned_data_good, start=1):
                    writer.writerow([i, row[0], row[3], row[18],
                                    row[20], row[22], row[23]])

            QMessageBox.information(
                self, "Success", f"Good data PDF and CSV exported successfully.\nPDF saved in:  {output_filename_pdf}\nCSV saved in: {output_filename_csv}")

        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to export data: {str(e)}")

    def export_to_pdf_defect(self):
        try:
            # Initialize progress dialog
            progress = QProgressDialog(
                "Exporting to PDF and CSV...", "Cancel", 0, 100, self)
            progress.setWindowModality(Qt.WindowModal)
            progress.setMinimumDuration(0)
            progress.setValue(0)

            pdf = FPDF()
            pdf.add_page()

            # Title
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(0, 10, "Defect Data Report", ln=True, align='C')

            # Header
            pdf.set_font("Arial", 'B', 6)
            pdf.cell(10, 10, "Jumlah", 1, 0, 'C')  # Jumlah total data
            pdf.cell(30, 10, "No", 1, 0, 'C')  # Nomor urut data
            pdf.cell(30, 10, "TGL", 1, 0, 'C')
            pdf.cell(30, 10, "STATUS 1", 1, 0, 'C')
            pdf.cell(30, 10, "STATUS 2", 1, 0, 'C')
            pdf.cell(30, 10, "NOMOR SERI BANKNOTE", 1, 0, 'C')
            pdf.cell(30, 10, "DATA ID", 1, 0, 'C')
            pdf.ln()

            # Data
            pdf.set_font("Arial", '', 6)
            total_rows = len(self.cleaned_data_defect)
            has_valid_row = False

            for i, row in enumerate(self.cleaned_data_defect, start=1):
                if progress.wasCanceled():
                    QMessageBox.warning(self, "Cancelled",
                                        "Export was cancelled")
                    return

                if len(row) > 23 and len(row[23]) == 9 and row[23].isalnum():
                    pdf.cell(10, 10, str(i), 1, 0, 'C')
                    pdf.cell(30, 10, row[0], 1, 0, 'C')
                    pdf.cell(30, 10, row[3], 1, 0, 'C')
                    pdf.cell(30, 10, row[18], 1, 0, 'C')
                    pdf.cell(30, 10, row[20], 1, 0, 'C')
                    pdf.cell(30, 10, row[23], 1, 0, 'C')
                    pdf.cell(30, 10, row[24], 1, 0, 'C')
                    pdf.ln()
                    has_valid_row = True

                # Update progress dialog
                progress.setValue(int(i / total_rows * 100))
                QApplication.processEvents()  # Allow dialog to update

            if has_valid_row:
                # Create folder based on today's date
                today = datetime.datetime.now().strftime('%Y-%m-%d')
                folder_path = os.path.join(os.getcwd(), today)

                if not os.path.exists(folder_path):
                    os.makedirs(folder_path)

                # Prepare file paths
                output_filename_pdf = os.path.join(
                    folder_path, 'defect_data_output.pdf')
                output_filename_csv = os.path.join(
                    folder_path, 'defect_data_output.csv')

                # Output PDF
                pdf.output(output_filename_pdf)

                # Export to CSV
                with open(output_filename_csv, 'w', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow(["Jumlah", "No", "TGL", "STATUS 1",
                                    "STATUS 2", "NOMOR SERI BANKNOTE", "DATA ID"])
                    for i, row in enumerate(self.cleaned_data_defect, start=1):
                        if len(row) > 23 and len(row[23]) == 9 and row[23].isalnum():
                            writer.writerow(
                                [i, row[0], row[3], row[18], row[20], row[23], row[24]])

                QMessageBox.information(
                    self, "Success", f"Defect data PDF and CSV exported successfully.\nPDF saved    in: {output_filename_pdf}\nCSV saved in: {output_filename_csv}")
            else:
                QMessageBox.warning(
                    self, "No Data", "No valid data found to export.")

        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to export data: {str(e)}")

    def filter_data(self):
        search_text = self.search_bar.text().lower()

        for row in range(self.good_data_table.rowCount()):
            item = self.good_data_table.item(row, 0)
            if item and search_text in item.text().lower():
                self.good_data_table.setRowHidden(row, False)
            else:
                self.good_data_table.setRowHidden(row, True)

        for row in range(self.defect_data_table.rowCount()):
            item = self.defect_data_table.item(row, 0)
            if item and search_text in item.text().lower():
                self.defect_data_table.setRowHidden(row, False)
            else:
                self.defect_data_table.setRowHidden(row, True)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = CSVProcessor()
    ex.show()
    sys.exit(app.exec_())
