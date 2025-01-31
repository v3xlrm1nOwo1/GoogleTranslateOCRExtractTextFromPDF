import re
import os
import time
import argparse
from tqdm import tqdm
from selenium import webdriver
from pdf2image import convert_from_path
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC



class GoogleTranslateOCRExtractTextFromPDF:
    def __init__(self, pdf_path: str, start_page: int, end_page: int, source_lang: str = "auto", target_lang: str = "en", cleaning_text: bool = False, action: str = "continue"):
        self.start_page = start_page
        self.end_page = end_page
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.cleaning_text = cleaning_text
        self.action = action

        self.url = f"https://translate.google.com/?sl={self.source_lang}&tl={self.target_lang}&op=images"
        self.start_crawl = 0
        self.page_num = self.start_page

        self.pdf_path = self.resolve_pdf_path(pdf_path=pdf_path)
        self.save_dict, self.save_images_path, self.save_text_path = self.get_folders_names(file_path=self.pdf_path)

        self._current_status_processing()

        self.driver = self._initialize_browser()

    def _current_status_processing(self):
        if os.path.exists(path=self.save_dict) and os.path.exists(path=self.save_images_path):
            if self.action == "continue":
                images = self.list_png_files_in_folder(folder_path=self.save_images_path)
                if images:
                    current_image = int(os.path.splitext(p=os.path.basename(p=images[-1]))[0].split("page_")[-1])
                    if current_image < self.end_page:
                        self.start_page = current_image + 1
                        self.pdf_to_image(pdf_path=self.pdf_path, start_page=self.start_page, end_page=self.end_page, output_path=self.save_images_path)
                        self.images = self.list_png_files_in_folder(folder_path=self.save_images_path)
                    else:
                        self.images = self.list_png_files_in_folder(folder_path=self.save_images_path)
                        if os.path.exists(path=self.save_text_path):
                            current_page = self.check_and_extract_last_page(save_path=self.save_text_path)
                            self.start_crawl = current_page - self.start_page + 1
                            self.page_num = current_page + 1
                else:
                    self.pdf_to_image(pdf_path=self.pdf_path, start_page=self.start_page, end_page=self.end_page, output_path=self.save_images_path)
                    self.images = self.list_png_files_in_folder(folder_path=self.save_images_path)
            elif self.action == "clear":
                images = self.list_png_files_in_folder(folder_path=self.save_images_path)
                if images:
                    self.remove_images(folder_path=self.save_images_path)
                if os.path.exists(path=self.save_text_path):
                    self.clear_file(save_path=self.save_text_path)
            else:
                self.pdf_to_image(pdf_path=self.pdf_path, start_page=self.start_page, end_page=self.end_page, output_path=self.save_images_path)
                self.images = self.list_png_files_in_folder(folder_path=self.save_images_path)
        else:
            self.pdf_to_image(pdf_path=self.pdf_path, start_page=self.start_page, end_page=self.end_page, output_path=self.save_images_path)
            self.images = self.list_png_files_in_folder(folder_path=self.save_images_path)
        
    def _initialize_browser(self):
        options = Options()
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("remote-debugging-port=9222")

        driver = webdriver.Chrome(options=options)
        return driver
    
    def upload_images_and_extract_texts(self):
        try:
            self.driver.get(self.url)
            
            for image in tqdm(self.images[self.start_crawl: self.end_page - self.start_page + 1]):
                time.sleep(3)

                upload_button = WebDriverWait(driver=self.driver, timeout=99).until(
                    EC.presence_of_element_located((By.XPATH, "/html/body/c-wiz/div/div[2]/c-wiz/div[5]/c-wiz/div[2]/c-wiz/div/div/div/div[1]/div[2]/div[2]/div[1]/input"))
                )
                upload_button.send_keys(image)  
                
                time.sleep(3)

                image_element = WebDriverWait(driver=self.driver, timeout=99).until(
                    EC.presence_of_element_located((By.XPATH, "/html/body/c-wiz/div/div[2]/c-wiz/div[5]/c-wiz/div[2]/c-wiz/div/div[2]/div[2]/img"))
                )
                                
                extracted_text = image_element.get_attribute("alt")
            
                if extracted_text:
                    if self.cleaning_text:
                        extracted_text = self.clean_text(text=extracted_text)
                    
                    self.save(save_path=self.save_text_path, text=extracted_text, page_num=self.page_num)
                    self.page_num += 1

                    # Clear
                    button = self.driver.find_element(by=By.XPATH, value="/html/body/c-wiz/div/div[2]/c-wiz/div[5]/c-wiz/div[2]/c-wiz/div/div[1]/div[2]/span[3]/button")
                    button.click()  
                else:
                    print("Extracted text not fond")                 
        
        except Exception as e:
            print(f"An error occurred: {e}")
            
        finally:
            self.driver.quit()
    
    def pdf_to_image(self, pdf_path: str, start_page: int, end_page: int, output_path: str):
        # poppler_path = r"<poppler_path>"
        self.check_dir(dic_name=output_path)
        
        for page_number in range(start_page, end_page + 1):
            images = convert_from_path(
                pdf_path=pdf_path,
                first_page=page_number,
                last_page=page_number,
                # poppler_path=poppler_path,
                use_pdftocairo=True,
                thread_count=6
            )

            image_name = f"page_{page_number}.png"
            image_path = os.path.join(output_path, image_name)
            
            images[0].save(image_path, "PNG", compress_level=1, quality=100)
    
    def list_png_files_in_folder(self, folder_path: str):
        try:
            abs_folder_path = os.path.abspath(folder_path)
            files = [
                os.path.join(abs_folder_path, f) 
                for f in os.listdir(abs_folder_path) 
                if os.path.isfile(os.path.join(abs_folder_path, f)) and f.endswith('.png')
            ]
            return sorted(files, key=lambda path: int(re.search(r'page_(\d+)', path).group(1)))
        except FileNotFoundError:
            print("\nThe folder does not exist.\n")
            return []

    def get_folders_names(self, file_path: str):
        file_name_with_extention = os.path.basename(p=file_path)
        file_name = os.path.splitext(p=file_name_with_extention)[0]
        
        save_images_path = os.path.join(file_name, "Images")
        save_text_path = os.path.join(file_name, "Extracted_Data", f"{file_name}.txt")
        
        return file_name, save_images_path, save_text_path
    
    def resolve_pdf_path(self, pdf_path):
        if os.path.isabs(pdf_path):
            if os.path.exists(path=pdf_path):
                return pdf_path
        else:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            full_path = os.path.join(script_dir, pdf_path)
            if os.path.exists(path=full_path):
                return full_path
        raise FileNotFoundError(f"Error: PDF file '{pdf_path}' not found in any expected location.")

    def check_dir(self, dic_name: str):
        dic_pat = os.path.join(os.getcwd(), dic_name)
        if not os.path.exists(path=dic_pat):
            os.makedirs(dic_pat)

    def clean_text(self, text: str):
        cleaned_text = re.sub(r'[\d٠-٩_-]', '', text)
        return cleaned_text
    
    def check_and_extract_last_page(self, save_path: str):
        with open(file=save_path, mode="r", encoding="utf-8") as file:
            text = file.read()
        
        numbers = re.findall(r'Page Number: \[(\d+)\]', text)
        if numbers:
            return int(numbers[-1])
        return None
    
    def clear_file(self, save_path: str):
        with open(file=save_path, mode='w', encoding='utf-8') as file:
            file.truncate(0)
    
    def remove_images(self, folder_path: str):
        for file in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file)
            if os.path.isfile(file_path) and file.lower().endswith(".png"):
                os.remove(file_path)

    def save(self, save_path: str, text: str, page_num: int):
        self.check_dir(dic_name=os.path.join(self.save_dict, "Extracted_Data"))     
        page_data = f"\t\tPage Number: [{page_num}] \n\n {text}\n\n"
        
        with open(file=save_path, mode="a", encoding="utf-8") as file:
            file.write(page_data)



if __name__ == "__main__":
    """
    - Run:
        python main.py --pdf_path <str> --start_page <int> --end_page <int> --source_lang <str> --target_lang <str> --cleaning_text <bool> --action <str>
    """
    parser = argparse.ArgumentParser(prog="PDF Text Extractor")
    parser.add_argument("--pdf_path", type=str, help="Path to the PDF file", required=True)
    parser.add_argument("--start_page", type=int, help="Start page for text extraction, index started from one", required=True)
    parser.add_argument("--end_page", type=int, help="End page for text extraction", required=True)
    parser.add_argument("--source_lang", type=str, help="Source language code (e.g., 'en')", default="auto", required=False)
    parser.add_argument("--target_lang", type=str, help="Target language code (e.g., 'es')", required=True)
    parser.add_argument("--cleaning_text", type=bool, help="Cleaning text From (_, -, numbers)", default=False, required=False)
    parser.add_argument("--action", choices=["continue", "clear"] , help="If files exists you whant 'continue' or 'clear' (default: 'continue')", default="continue")

    args = parser.parse_args()

    pdf_path = args.pdf_path
    start_page = args.start_page
    end_page = args.end_page
    source_lang = args.source_lang
    target_lang = args.target_lang
    cleaning_text = args.cleaning_text
    action= args.action

    print(f"- PDF Path: {pdf_path}")
    print(f"- Start Page: {start_page}")
    print(f"- End Page: {end_page}")
    print(f"- Source Language: {source_lang}")
    print(f"- Target Language: {target_lang}")
    print(f"- Cleaning Text: {cleaning_text}")
    print(f"- Action: {action}")

    ocr = GoogleTranslateOCRExtractTextFromPDF(
        pdf_path=pdf_path,
        start_page=start_page,
        end_page=end_page,
        source_lang=source_lang,
        target_lang=target_lang,
        cleaning_text=cleaning_text,
        action=action,
    )

    ocr.upload_images_and_extract_texts()
