import requests
from bs4 import BeautifulSoup
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import json
import re

class ReraScraper:
    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        self.base_url = "https://rera.odisha.gov.in"
        self.projects_data = []

    def wait_for_page_load(self, timeout=20):
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            time.sleep(3)  
        except Exception as e:
            print(f"")

    def scroll_to_load_content(self):
        try:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)
        except:
            pass

    def get_project_table_data(self):
        try:
            url = "https://rera.odisha.gov.in/projects/project-list"
            print(f"To: {url}")
            self.driver.get(url)
            self.wait_for_page_load()
            self.scroll_to_load_content()
            project_rows = []
            
            try:
                table_selectors = [
                    "table.table tbody tr",
                    ".table tbody tr", 
                    "table tbody tr",
                    ".data-table tbody tr",
                    ".projects-table tbody tr"
                ]
                
                for selector in table_selectors:
                    rows = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if rows and len(rows) > 1: 
                        print(f"{len(rows)} rows")
                        for i, row in enumerate(rows[:6]):
                            cells = row.find_elements(By.TAG_NAME, "td")
                            if len(cells) >= 2:  
                                view_details_link = None
                                try:
                                    view_details_link = row.find_element(By.XPATH, 
                                        ".//a[contains(text(), 'View Details') or contains(text(), 'Details') or contains(text(), 'View')]")
                                except:
                                    pass
                                
                                row_data = {
                                    'row_index': i,
                                    'cells_text': [cell.text.strip() for cell in cells],
                                    'row_element': row,
                                    'view_details_link': view_details_link,
                                    'all_links': row.find_elements(By.TAG_NAME, "a")
                                }
                                project_rows.append(row_data)
                        break
                
                if project_rows:
                    return project_rows
                        
            except:
                pass
            
            try:
                list_selectors = [
                    ".project-item",
                    ".list-group-item", 
                    ".project-card",
                    "[class*='project']",
                    ".row .col"
                ]
                
                for selector in list_selectors:
                    items = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if items:
                        print(f"Found {len(items)} items")
                        valid_items = []
                        for i, item in enumerate(items[:10]):  
                            text = item.text.strip()
                            
                            if (len(text) > 20 and 
                                not any(nav_text in text.lower() for nav_text in 
                                       ['home', 'back', 'filter', 'clear', 'project applications', 'ongoing projects', 'completed projects'])):
                                
                                view_details_link = None
                                try:
                                    view_details_link = item.find_element(By.XPATH, 
                                        ".//a[contains(text(), 'View Details') or contains(text(), 'Details')]")
                                except:
                                    pass
                                
                                item_data = {
                                    'row_index': len(valid_items),
                                    'element': item,
                                    'text': text,
                                    'view_details_link': view_details_link,
                                    'all_links': item.find_elements(By.TAG_NAME, "a")
                                }
                                valid_items.append(item_data)
                                
                                if len(valid_items) >= 6:
                                    break
                        
                        if valid_items:
                            return valid_items[:6]
                            
            except:
                pass
            
            try:
                all_links = self.driver.find_elements(By.TAG_NAME, "a")
                project_links = []
                
                for link in all_links:
                    href = link.get_attribute('href')
                    text = link.text.strip()
                    if (href and 
                        ('project' in href.lower() or 'detail' in href.lower()) and
                        text and len(text) > 5 and
                        not any(nav_text in text.lower() for nav_text in 
                               ['home', 'back', 'filter', 'clear', 'login', 'register'])):
                        
                        link_data = {
                            'row_index': len(project_links),
                            'element': link,
                            'text': text,
                            'href': href,
                            'view_details_link': link
                        }
                        project_links.append(link_data)
                        
                        if len(project_links) >= 6:
                            break
                
                if project_links:
                    print(f"Found {len(project_links)} project links")
                    return project_links
                    
            except:
                pass
                
            return []
            
        except Exception as e:
            print(f"Error")
            return []

    def extract_project_details(self, project_info):
        try:
            project_name_from_card = ""
            project_text = project_info.get('text', '')
            if project_text:
                lines = project_text.split('\n')
                if lines:
                    for line in lines:
                        line = line.strip()
                        if (line and 
                            len(line) > 2 and 
                            not any(word in line.lower() for word in ['by ', 'address', 'project type', 'started from', 'possession', 'units', 'available', 'contact', 'view details'])):
                            project_name_from_card = line
                            break
        
            view_details_link = None
            
            element = project_info.get('element')
            if element:
                try:
                    view_details_links = element.find_elements(By.XPATH, ".//a[contains(text(), 'View Details')]")
                    if view_details_links:
                        view_details_link = view_details_links[0]
                except:
                    pass
            
            if not view_details_link:
                all_links = project_info.get('all_links', [])
                for link in all_links:
                    try:
                        if 'view details' in link.text.lower() or 'details' in link.text.lower():
                            view_details_link = link
                            break
                    except:
                        continue

            if not view_details_link:
                try:
                    view_details_links = self.driver.find_elements(By.XPATH, "//a[contains(text(), 'View Details')]")
                    if view_details_links and len(view_details_links) > project_info.get('row_index', 0):
                        view_details_link = view_details_links[project_info.get('row_index', 0)]
                except:
                    pass
            
            if not view_details_link:
                return {}
            
            original_window = self.driver.current_window_handle
            
            print(f"{view_details_link.text[:50]}")
            try:
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", view_details_link)
                time.sleep(1)
                view_details_link.click()
            except:
                try:
                    self.driver.execute_script("arguments[0].click();", view_details_link)
                except:
                    ActionChains(self.driver).move_to_element(view_details_link).click().perform()
            
            time.sleep(4)  
            if len(self.driver.window_handles) > 1:
                for handle in self.driver.window_handles:
                    if handle != original_window:
                        self.driver.switch_to.window(handle)
                        break
                self.wait_for_page_load()

            project_data = self.extract_details_from_current_page()
            if (project_name_from_card and 
                (not project_data.get('Project Name') or 
                 project_data.get('Project Name', '').lower() in ['projects', 'project', 'rera', 'odisha', ''])):
                project_data['Project Name'] = project_name_from_card
                print(f"Using project name from card: {project_name_from_card}")
            
            if len(self.driver.window_handles) > 1:
                self.driver.close()
                self.driver.switch_to.window(original_window)
            
            return project_data
            
        except Exception as e:
            print(f"Error")
            return {}

    def extract_details_from_current_page(self):
        try:
            project_data = {}
            time.sleep(2)
            
            def get_field_xpaths(field_terms):
                return [
                    f"//td[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{term}')]/following-sibling::td[1]"
                    for term in field_terms
                ] + [
                    f"//th[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{term}')]/following-sibling::td[1]"
                    for term in field_terms
                ] + [
                    f"//label[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{term}')]/following-sibling::*"
                    for term in field_terms
                ]
            
            rera_xpaths = get_field_xpaths(['rera', 'registration']) + [
                "//input[contains(translate(@name, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'rera')]"
            ]
            project_data['Rera Regd. No'] = self.find_field_value(rera_xpaths)
            
            project_name_xpaths = get_field_xpaths(['project name']) + [
                "//tr[td[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'project name')]]/td[2]",
                "//*[@class='project-name']"
            ]
            project_name = self.find_field_value(project_name_xpaths)
            
            if not project_name or project_name.lower() in ['projects', 'project', 'rera', 'odisha']:
                heading_xpaths = [
                    f"//h{i}[normalize-space(text()) != '' and not(contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'project')) and not(contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'rera'))]"
                    for i in range(1, 4)
                ]
                heading_name = self.find_field_value(heading_xpaths)
                if heading_name and heading_name.lower() not in ['projects', 'project', 'rera', 'odisha']:
                    project_name = heading_name
            
            project_data['Project Name'] = project_name
            
            self.click_promoter_tab()
            
            promoter_xpaths = get_field_xpaths(['company name', 'promoter name'])
            project_data['Promoter Name'] = self.find_field_value(promoter_xpaths)
            
            address_xpaths = get_field_xpaths(['registered office', 'address']) + [
                "//textarea[contains(translate(@name, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'address')]"
            ]
            project_data['Address of the Promoter'] = self.find_field_value(address_xpaths)
            
            gst_xpaths = get_field_xpaths(['gst', 'gstin'])
            project_data['GST No.'] = self.find_field_value(gst_xpaths)
            
            return project_data
            
        except:
            return {}

    def find_field_value(self, xpath_patterns):
        for pattern in xpath_patterns:
            try:
                elements = self.driver.find_elements(By.XPATH, pattern)
                for element in elements:
                    value = element.text.strip()
                    if value and len(value) > 1 and value.lower() not in ['', 'n/a', 'na', 'nil']:
                        return value
                    value = element.get_attribute('value')
                    if value and value.strip() and len(value.strip()) > 1:
                        return value.strip()
            except:
                continue
        return ""

    def click_promoter_tab(self):
        try:
            tab_patterns = [
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'promoter')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'promoter')]",
                "//li[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'promoter')]",
                "//tab[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'promoter')]",
                "//*[@id='promoter-tab' or contains(@id, 'promoter')]"
            ]
            
            for pattern in tab_patterns:
                try:
                    tabs = self.driver.find_elements(By.XPATH, pattern)
                    if tabs:
                        tabs[0].click()
                        time.sleep(2)
                        return True
                except:
                    continue
            
            return False
            
        except:
            return False

    def scrape_projects(self):
        try:
            for i in range(6):
                print(f"\nProcessing{i+1}/6...")
                
                project_list = self.get_project_table_data()
                
                if not project_list or i >= len(project_list):
                    print(f"Project {i+1} not found")
                    continue

                project_info = project_list[i]
                project_text = project_info.get('text', 'Unknown')[:100] + "..." if len(project_info.get('text', '')) > 100 else project_info.get('text', 'Unknown')
                print(f"{project_text}")
                project_data = self.extract_project_details(project_info)
                
                if project_data and any(v for v in project_data.values() if v):
                    self.projects_data.append(project_data)
                    print(f"Successfully extracted data for project {i+1}")
                else:
                    print(f"Failed for project {i+1}")
                
                self.driver.get("https://rera.odisha.gov.in/projects/project-list")
                self.wait_for_page_load()
                self.scroll_to_load_content()
                
                time.sleep(3)
            
            return self.projects_data
            
        except:
            return []

    def save_data(self, json_filename="scraped.json", csv_filename="rera_projects.csv"):
        if self.projects_data:
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(self.projects_data, f, indent=2, ensure_ascii=False)
            print(f"\nData saved to {json_filename}")
            df = pd.DataFrame(self.projects_data)
            df.to_csv(csv_filename, index=False, encoding='utf-8')
            print(f"Data also saved to {csv_filename}")
            
            return df
        else:
            print("No data to save")
            return None

    def display_data(self):
        if not self.projects_data:
            print("No data")
            return
        print("SCRAPED RERA PROJECT DATA")
        
        for i, project in enumerate(self.projects_data, 1):
            print(f"\nProject {i}:")
            print("-" * 50)
            for key, value in project.items():
                print(f"   {key}: {value or 'N/A'}")

    def close(self):
        try:
            self.driver.quit()
        except:
            pass

def main():
    scraper = ReraScraper()
    
    try:
        print("Starting RERA Odisha project scraping...6")
        
        projects = scraper.scrape_projects()
        
        if projects:
            print(f"\nSuccessfully scraped {len(projects)} projects")
            scraper.display_data()
            scraper.save_data("scraped.json")
            
        else:
            print("No projects were scraped successfully")
    
    except KeyboardInterrupt:
        print("\nScraping interrupted by user")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        scraper.close()
        print("\nScraping completed")

if __name__ == "__main__":
    main()