import base64
from pathlib import Path
from ..config.configer import (
    SYSTEM_PROMPT_IMAGE_DESCRIBER,
    USER_PROMPT_IMAGE_DESCRIBER,
    TMP_IMAGES_DIR,
)
from typing import List
from app.model.chat_client import ChatClient
from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableStructureOptions
from docling.datamodel.document import ConversionResult
from docling_core.types.doc.document import (
    PictureItem,
    DocItemLabel,
    TextItem,
    DoclingDocument,
)
from app.config.logger import get_logger

logger = get_logger("mini-rag." + __name__)


class PdfToMarkdownConverter:
    def __init__(
        self,
        markdown_dir: Path,
        chat_client: ChatClient,
        ocr_langs=("eng",),
        num_threads=4,
        device=AcceleratorDevice.AUTO,
    ):
        """
        Initialize the PDF to Markdown converter.

        Args:
            markdown_dir (Path): Directory where converted markdown files will be saved.
            chat_client (ChatClient): LLM client to describe images in the PDF.
            ocr_langs (tuple, optional): Languages for OCR extraction. Defaults to ('eng',).
            num_threads (int, optional): Number of threads for processing. Defaults to 4.
            device (AcceleratorDevice, optional): Device to run conversion on. Defaults to AUTO.
        """
        self.markdown_dir = markdown_dir
        self.chat_client = chat_client
        self.converter = self._build_converter(ocr_langs, num_threads, device)

    @staticmethod
    def _build_converter(ocr_langs, num_threads, device) -> DocumentConverter:
        """
        Build the underlying DocumentConverter with OCR, table, and image options.

        Args:
            ocr_langs (tuple): Languages to use for OCR.
            num_threads (int): Number of threads for conversion.
            device (AcceleratorDevice): Device to use for conversion.

        Returns:
            DocumentConverter: Configured document converter instance.
        """
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
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )

    def convert_files(self, files) -> List[DoclingDocument]:
        """
        Convert multiple PDF files to markdown and extract images with descriptions.

        Args:
            files (list[Path]): List of PDF file paths to convert.

        Returns:
            list[DoclingDocument]: List of converted document objects.
        """
        logger.debug(
            f"Starting markdown conversion of {len(files)} file{'s' if len(files) > 1 else ''}..."
        )
        results = list(self.converter.convert_all(files))

        for result in results:
            self._replace_images(result)
            self._handle_result(result)
        return [result.document for result in results]

    def convert_file(self, files) -> DoclingDocument:
        """
        Convert a single PDF file to markdown and process its images.

        Args:
            files (Path): Path to the PDF file.

        Returns:
            DoclingDocument: Converted document object.
        """
        logger.debug("Starting conversion of 1 file...")
        result = self.converter.convert(files)
        self._replace_images(result)
        self._handle_result(result)
        return result.document

    def _replace_images(self, result: ConversionResult):
        """
        Replace embedded images in the document with text descriptions from LLM.

        Args:
            result (ConversionResult): Conversion result containing the document with images.
        """

        if result.status == "success":
            replacements: list[tuple[PictureItem, TextItem]] = []
            for item, _ in result.document.iterate_items():
                if isinstance(item, PictureItem):
                    # Get image and prompt it to LLM
                    picture_uri = str(item.image.uri)
                    if picture_uri.startswith("data:image/png;base64,"):
                        element_image_filename = (
                            TMP_IMAGES_DIR
                            / f"{result.document.origin.filename}-image-{len(replacements) + 1}.png"
                        )
                        data = picture_uri.split(",")[1]
                        decoded_bytes = base64.b64decode(data)
                        with open(element_image_filename, "wb") as f:
                            logger.debug(f"Saved image at: {element_image_filename}")
                            f.write(decoded_bytes)

                        response = self.chat_client.chat(
                            [
                                {
                                    "role": "system",
                                    "content": [
                                        {"text": SYSTEM_PROMPT_IMAGE_DESCRIBER}
                                    ],
                                },
                                {
                                    "role": "user",
                                    "content": [
                                        {"text": USER_PROMPT_IMAGE_DESCRIBER},
                                        {"image": picture_uri},
                                    ],
                                },
                            ]
                        )

                        new_text = result.document.add_text(
                            label=DocItemLabel.TEXT,
                            orig=response,
                            text=response,
                            prov=item.prov[0],
                        )
                        replacements.append((item, new_text))

            for old_item, new_item in replacements:
                result.document.replace_item(new_item=new_item, old_item=old_item)

    def _handle_result(self, result: ConversionResult):
        """
        Save the converted markdown document to the markdown directory.

        Args:
            result (ConversionResult): Conversion result containing the processed document.
        """
        if result.status == "success":
            out_file = self.markdown_dir / f"{result.input.file.stem}.md"
            out_file.write_text(
                result.document.export_to_markdown(),
                encoding="utf-8",
            )
            logger.debug(f"Successfully converted: {result.input.file.name}")
        else:
            logger.warning(f"Failed to convert: {result.input.file.name}")
