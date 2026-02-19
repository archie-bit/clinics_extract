from playwright.async_api import async_playwright
import pandas as pd
import argparse
import time 
import logging
import os
from datetime import datetime
from dotenv import load_dotenv
from processor import filter_clinics_batch
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


load_dotenv()
level = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(level=level)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=5, max=30),
    before_sleep=lambda retry_state: logging.INFO(f"Rate limited. Retrying in {retry_state.next_action.sleep}s...")
)
class Business:
    def __init__(self, clinic_name= '', doctor_name= '', phone_number= '', website= '', maps_link='', address=''):
        self.clinic_name= clinic_name
        self.doctor_name= doctor_name
        self.address= address
        self.phone_number = phone_number
        self.website= website
        self.maps_link = maps_link

    def asdict(self):
         return {'clinic_name': self.clinic_name,
                 'doctor_name': self.doctor_name,
                 'address': self.address,   
                 'phone_number': self.phone_number,
                 'website': self.website,
                 'maps_link': self.maps_link}
    
async def scrapper(search_for):
    base_url= 'https://www.google.com/maps?hl=en'

    async with async_playwright() as p:
        #Start playwright and go to google maps
        browser= await p.chromium.launch(headless= True)
        context= await browser.new_context(
            locale='en-US',
            extra_http_headers={
                'Accept-Language': 'en-US,en;q=0.9'
            },
            java_script_enabled= True)
        page= await context.new_page()
        await page.goto(base_url, wait_until='load')

        #input seaech query
        input_box= page.locator('//input[@name="q"]')
        await input_box.fill(search_for)
        await page.keyboard.press('Enter')

        #select result container
        search_result_element= '//div[@role="feed"]'
        await page.wait_for_selector(search_result_element)
        result_container= await page.query_selector(search_result_element)
        await result_container.scroll_into_view_if_needed()

        #scroll to load all entries
        keep_scrolling= True
        while keep_scrolling:
            await result_container.press('Space')
            await asyncio.sleep(1)

            if await result_container.query_selector('//span[text()="You\'ve reached the end of the list."]'):
                await result_container.press('Space')
                keep_scrolling= False

        #scrape all listings
        listings = await page.locator('//a[contains(@href, "https://www.google.com/maps/place")]').all()
        business_list= []
        for listing in listings[:10]:
            #extract attributes
            try:
                raw_map_link = await listing.get_attribute('href')

                await listing.click()
                await asyncio.sleep(2)

                name_attibute = page.locator('//div[@role="main" and @aria-label]')
                name_attibute_await= await name_attibute.get_attribute("aria-label")
                name= name_attibute_await.replace('"', '').replace('“', '').replace('”', '').strip()

                address_xpath = page.locator('//button[@data-item-id="address"]')
                address_xpath_await= await address_xpath.inner_text() if await address_xpath.count() > 0 else ""
                address= address_xpath_await.split('\n')[-1].strip() if address_xpath_await else ""
                
                phone_number_xpath= page.locator('//button[contains(@data-item-id, "phone:tel:")]')
                phone_number_await= await phone_number_xpath.inner_text() if await phone_number_xpath.count() > 0 else ""
                phone_number= phone_number_await.split('\n')[-1].strip() if phone_number_xpath else ""

                website_xpath = page.locator('//a[@data-item-id="authority"]')
                website = await website_xpath.get_attribute('href') if await website_xpath.count() > 0 else ""

                business = Business(clinic_name=name, address=address, phone_number=phone_number, website= website, maps_link=raw_map_link)
                business_list.append(business.asdict())
            except Exception as e:
                        logging.error(f'Error occured: {e}')

        await browser.close()
        final_clinics = filter_clinics_batch(business_list)

        if final_clinics:
            df = pd.DataFrame(final_clinics)
            schema = ['clinic_name', 'doctor_name', 'phone_number', 'line_type','address', 'website', 'maps_link', 'confidence_score', 'decision']
            df = df[schema]
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
            filename= f'leads_{timestamp}.csv'
            output_path = os.path.join('data', filename)
            os.makedirs('data', exist_ok=True)
            df.to_csv(output_path, index=False)

if __name__ == "__main__":
    parser= argparse.ArgumentParser()
    parser.add_argument('-q', '--query', type=str, default="Dentist in Maadi")
    args= parser.parse_args()

    search_for= args.query
    asyncio.run(scrapper(search_for))