



# GoogleTranslateOCRExtractTextFromPDF

## Overview
This project extracts text from PDF files using Optical Character Recognition (OCR) and Google Translate's image translation feature. It converts PDF pages to images, uploads them to Google Translate, and extracts the recognized text or optionally translates it into a target language.

## Install Required Dependencies
Use `pip` to install the required Python libraries:

```bash
pip install -r requirements.txt
```

### Basic Example Usage Code 
Below is a step-by-step guide to get started to extract text from a book in Arabic from pages 10 to 92:
```bash
python main.py --pdf_path "Books/رباعيات مولانا جلال الدين الرومي.pdf" \
               --start_page 10 \
               --end_page 92 \
               --source_lang auto \
               --target_lang ar \
               --cleaning_text True \
               --action continue
```

Alternatively, you can use the provided `run.sh` script:
```bash
bash run.sh
```

## Arguments
Run the script with the required arguments:
| Argument        | Type  | Description |
|----------------|-------|-------------|
| `--pdf_path`   | str   | Path to the PDF file. |
| `--start_page` | int   | The first page to process. |
| `--end_page`   | int   | The last page to process. |
| `--source_lang` | str  | Source language (default: `auto`). |
| `--target_lang` | str  | Target language for translation. |
| `--cleaning_text` | bool | Whether to clean the extracted text, it cleaning text From `(_, -, numbers)`. Set it to False or modify the `clean_text` function to suit the type of cleaning you want. |
| `--action` | str | `"continue"` to resume, `"clear"` to restart extraction, if files exists. |

## Output
- Extracted images are saved at `<pdf_name>/Images`.
- Extracted text is saved at `<pdf_name>/Extracted_Data/<pdf_name>.txt`.

## Notes
- This script uses Google Chrome with certain options so that crawling is not detected and text extraction fails.
- There is a problem that may occur when using the code specifically in the function for extracting images from a PDF file `pdf_to_image`. It is solved in different ways depending on the type of operating system on which the code is running. Follow the instructions here: [stackoverflow.com](https://stackoverflow.com/questions/53481088/poppler-in-path-for-pdf2image)
- The process may take time depending on the number of pages.

## License
This project is licensed under the MIT License.
