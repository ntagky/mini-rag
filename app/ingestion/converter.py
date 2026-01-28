from pathlib import Path
from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import (PdfPipelineOptions, TableStructureOptions)


class PdfToMarkdownConverter:
    def __init__(self, markdown_dir: Path, ocr_langs=("eng",), num_threads=4, device=AcceleratorDevice.AUTO):
        self.markdown_dir = markdown_dir
        self.converter = self._build_converter(ocr_langs, num_threads, device)

    @staticmethod
    def _build_converter(ocr_langs, num_threads, device):
        pipeline_options = PdfPipelineOptions()
        pipeline_options.images_scale = 2.0
        pipeline_options.generate_picture_images = True
        pipeline_options.do_ocr = True
        pipeline_options.do_table_structure = True
        pipeline_options.table_structure_options = TableStructureOptions(
            do_cell_matching=True
        )
        pipeline_options.ocr_options.lang = list(ocr_langs)
        pipeline_options.accelerator_options = AcceleratorOptions(
            num_threads=num_threads,
            device=device,
        )

        return DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=pipeline_options
                )
            }
        )

    def convert_files(self, files):
        print(f"Starting markdown conversion of {len(files)} file{'s' if len(files) > 1 else ''}...")
        results = list(self.converter.convert_all(files))

        for result in results:
            self._handle_result(result)
        return [result.document for result in results]

    def convert_file(self, files):
        print(f"Starting conversion of 1 file...")
        result = self.converter.convert(files)
        self._handle_result(result)
        return result.document

    def _handle_result(self, result):
        if result.status == "success":
            out_file = self.markdown_dir / f"{result.input.file.stem}.md"
            out_file.write_text(
                result.document.export_to_markdown(),
                encoding="utf-8",
            )
            print(f"✅ Successfully converted: {result.input.file.name}")
        else:
            print(f"❌ Failed to convert: {result.input.file.name}")
