"""Graphical user interface for CV Maker."""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import threading

from .parser import parse_file
from .docx_generator import generate_docx
from .pdf_generator import generate_pdf


class CVMakerApp:
    """Main GUI application."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title('CV Maker')
        self.root.geometry('500x350')
        self.root.resizable(True, True)

        self.input_path = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.format_var = tk.StringVar(value='docx')
        self.status_var = tk.StringVar(value='Ready')

        self._create_widgets()

    def _create_widgets(self):
        """Create GUI widgets."""
        # Main frame with padding
        main_frame = ttk.Frame(self.root, padding='10')
        main_frame.grid(row=0, column=0, sticky='nsew')

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        # Input file section
        ttk.Label(main_frame, text='Input File:').grid(row=0, column=0, sticky='w', pady=5)
        input_frame = ttk.Frame(main_frame)
        input_frame.grid(row=0, column=1, sticky='ew', pady=5)
        input_frame.columnconfigure(0, weight=1)

        ttk.Entry(input_frame, textvariable=self.input_path).grid(row=0, column=0, sticky='ew')
        ttk.Button(input_frame, text='Browse...', command=self._browse_input).grid(row=0, column=1, padx=(5, 0))

        # Output directory section
        ttk.Label(main_frame, text='Output Dir:').grid(row=1, column=0, sticky='w', pady=5)
        output_frame = ttk.Frame(main_frame)
        output_frame.grid(row=1, column=1, sticky='ew', pady=5)
        output_frame.columnconfigure(0, weight=1)

        ttk.Entry(output_frame, textvariable=self.output_dir).grid(row=0, column=0, sticky='ew')
        ttk.Button(output_frame, text='Browse...', command=self._browse_output).grid(row=0, column=1, padx=(5, 0))

        # Format selection
        ttk.Label(main_frame, text='Output Format:').grid(row=2, column=0, sticky='w', pady=10)
        format_frame = ttk.Frame(main_frame)
        format_frame.grid(row=2, column=1, sticky='w', pady=10)

        ttk.Radiobutton(format_frame, text='DOCX', variable=self.format_var, value='docx').pack(side='left')
        ttk.Radiobutton(format_frame, text='PDF', variable=self.format_var, value='pdf').pack(side='left', padx=10)
        ttk.Radiobutton(format_frame, text='Both', variable=self.format_var, value='both').pack(side='left')

        # Generate button
        self.generate_btn = ttk.Button(main_frame, text='Generate CV', command=self._generate)
        self.generate_btn.grid(row=3, column=0, columnspan=2, pady=20)

        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=4, column=0, columnspan=2, sticky='ew', pady=5)

        # Status label
        status_label = ttk.Label(main_frame, textvariable=self.status_var)
        status_label.grid(row=5, column=0, columnspan=2, pady=5)

        # Instructions
        instructions = ttk.Label(
            main_frame,
            text='Select a markdown (.md) file and choose your output format.\n'
                 'The generated files will be saved in the output directory.',
            justify='center',
            foreground='gray'
        )
        instructions.grid(row=6, column=0, columnspan=2, pady=20)

    def _browse_input(self):
        """Open file dialog for input file."""
        filepath = filedialog.askopenfilename(
            title='Select CV Markdown File',
            filetypes=[
                ('Markdown files', '*.md *.markdown'),
                ('Text files', '*.txt'),
                ('All files', '*.*')
            ]
        )
        if filepath:
            self.input_path.set(filepath)
            # Auto-set output directory if not set
            if not self.output_dir.get():
                self.output_dir.set(str(Path(filepath).parent))

    def _browse_output(self):
        """Open directory dialog for output."""
        dirpath = filedialog.askdirectory(title='Select Output Directory')
        if dirpath:
            self.output_dir.set(dirpath)

    def _generate(self):
        """Generate CV documents."""
        input_path = self.input_path.get()
        output_dir = self.output_dir.get()

        if not input_path:
            messagebox.showerror('Error', 'Please select an input file.')
            return

        if not Path(input_path).exists():
            messagebox.showerror('Error', f'Input file not found: {input_path}')
            return

        if not output_dir:
            output_dir = str(Path(input_path).parent)
            self.output_dir.set(output_dir)

        # Disable button and start progress
        self.generate_btn.config(state='disabled')
        self.progress.start()
        self.status_var.set('Generating...')

        # Run generation in a thread
        thread = threading.Thread(
            target=self._generate_thread,
            args=(input_path, output_dir)
        )
        thread.start()

    def _generate_thread(self, input_path: str, output_dir: str):
        """Generate documents in background thread."""
        try:
            cv = parse_file(input_path)
            base_name = Path(input_path).stem
            fmt = self.format_var.get()
            generated_files = []

            if fmt in ['docx', 'both']:
                output_path = str(Path(output_dir) / f'{base_name}.docx')
                generate_docx(cv, output_path)
                generated_files.append(output_path)

            if fmt in ['pdf', 'both']:
                output_path = str(Path(output_dir) / f'{base_name}.pdf')
                generate_pdf(cv, output_path)
                generated_files.append(output_path)

            self.root.after(0, lambda: self._generation_complete(generated_files))

        except Exception as e:
            self.root.after(0, lambda: self._generation_error(str(e)))

    def _generation_complete(self, files: list[str]):
        """Handle successful generation."""
        self.progress.stop()
        self.generate_btn.config(state='normal')
        self.status_var.set('Complete!')

        files_list = '\n'.join(files)
        messagebox.showinfo('Success', f'Generated files:\n{files_list}')

    def _generation_error(self, error: str):
        """Handle generation error."""
        self.progress.stop()
        self.generate_btn.config(state='normal')
        self.status_var.set('Error')

        messagebox.showerror('Error', f'Failed to generate CV:\n{error}')


def run_gui():
    """Launch the GUI application."""
    root = tk.Tk()
    app = CVMakerApp(root)
    root.mainloop()


if __name__ == '__main__':
    run_gui()
