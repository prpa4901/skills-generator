import time
import re

from selenium import webdriver

from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import openai
from openai import OpenAI
from transformers import GPT2Tokenizer



# Now you have your text limited to approximately 10000 tokens


#commenting the token for now
client = OpenAI(api_key="")

# driver = webdriver.Chrome(ChromeDriverManager().install())

service = Service('/usr/local/bin/chromedriver')

service.start()

options = Options()

driver = webdriver.Remote(command_executor=service.service_url, options=options)

driver.maximize_window()

#need way to feed linked creds
email = ""
password = ""

driver.get('https://www.linkedin.com/login')
time.sleep(2)
driver.find_element(By.ID, 'username').send_keys(email)
driver.find_element(By.ID, 'password').send_keys(password)
driver.find_element(By.ID, 'password').send_keys(Keys.RETURN)

time.sleep(15)
driver.get("https://www.linkedin.com/jobs/search/?keywords=network+automation&location=United+States")
print(driver.title)
time.sleep(3) # Let the user actually see something!

#change the prompt according to your job requirement
question_prompt = "Given the following job descriptions, identify the key skills" \
    "and technology, give me a comma seperated csv with list of technology, tools and protocols, mainly which I can study and prepare for the job of network automation, network devops, network toolings, IAC, SDN, Virtual Networking with MLOps, dont say anything else, please be specific to network automation and IAC, all the entries of csv should have one single word entry :{}"

WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "job-card-container")))

# Pattern to match desired keywords/phrases in job titles
include_pattern = re.compile(r'\b(infrastructure|network|devops|cloud|SRE|SDN|network systems|IAC|IAAC)\b', re.IGNORECASE)
# responsibilities_pattern = re.compile(r"Responsibilities \(including but not limited to\):([\s\S]*?)(?=Experience, Knowledge, Skills and Abilities:)", re.IGNORECASE)

# Regex to check for specified keywords in different categories within the captured section
category1_pattern = re.compile(r"\b(network|infrastructure|cloud|SDN|IAC|AI|ML)\b", re.IGNORECASE)
category2_pattern = re.compile(r"\b(automation|devops|SRE|IAC)\b", re.IGNORECASE)

criteria_match = []
skillset_array = {}
jid_unique = []

# Now extract job details (simplified example, adjust according to actual requirements)
for page in range(1,5):
    jobs = driver.find_elements(By.CLASS_NAME, "occludable-update")
    time.sleep(2)
    # jobs = driver.find_elements(By.CLASS_NAME, "job-card-container")
    for job in jobs:
        driver.execute_script("arguments[0].scrollIntoView();", job)
        job.click()
        time.sleep(3)  # Adjust based on your internet speed and LinkedIn's response time
        
        # Now extract job details. This is an example; actual selectors might differ.
        job_title = driver.find_element(By.CLASS_NAME, "job-details-jobs-unified-top-card__job-title").text
        if include_pattern.search(job_title):
            company_name = driver.find_element(By.CLASS_NAME, "job-details-jobs-unified-top-card__primary-description-container").text
            job_location = driver.find_element(By.CLASS_NAME, "job-details-jobs-unified-top-card__primary-description-container").text
            jid = (job_title, company_name, job_location)
            if jid in jid_unique:
                continue
            jid_unique.append(jid)
            job_description = driver.find_element(By.CLASS_NAME, "jobs-description-content__text").text
            '''
            responsibilities_match = responsibilities_pattern.search(job_description)
            if responsibilities_match:
                responsibilities_section = responsibilities_match.group(1)
            else:
                responsibilities_section = ""
            '''
            # print(responsibilities_section)
            contains_category1 = bool(category1_pattern.search(job_description))
            contains_category2 = bool(category2_pattern.search(job_description))
            if contains_category1 and contains_category2:
                print("This job matches the criteria:")
                
                # print(job_description)

                # Initialize the tokenizer
                tokenizer = GPT2Tokenizer.from_pretrained('gpt2')

                # Your text
                # job_description = "Your long job description text here..."

                # Tokenize the text
                tokens = tokenizer.encode(question_prompt.format(job_description), return_tensors='pt')

                # Truncate to the first 10000 tokens if necessary
                if tokens.shape[1] > 1024:
                    tokens = tokens[:, :1024]

                # Convert back to text
                truncated_text = tokenizer.decode(tokens[0])
                # print(truncated_text)
                
                stream = client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content":truncated_text}],
                    stream=True)
                fin_res = ''
                for chunk in stream:
                    if chunk.choices[0].delta.content is not None:
                        cont = chunk.choices[0].delta.content
                        # print(cont)
                        fin_res += str(cont)
                # print(fin_res)
                keywords = [item.strip() for item in fin_res.replace('\n', ' ').split(',')]
                # print(keywords)
                for kw in keywords:
                    if '.' in kw:
                        kw = kw.replace('.', '')
                    kw = kw.upper()
                    if kw not in skillset_array:
                        skillset_array[kw] = 1
                    else:
                        skillset_array[kw]+=1
                # print(skillset_array) 
            else:
                print("This job does not match the criteria.")        
    time.sleep(2) 
    next_page_btn = driver.find_element(By.CSS_SELECTOR, 'button[aria-label="View next page"]')
    if next_page_btn:
        next_page_btn.click()

b = {k:v for k,v in skillset_array.items() if v!=1}
skillset_array = dict(sorted(b.items(), key=lambda item: item[1], reverse=True))

driver.quit()

for k, v in skillset_array.items():
    print((k,v))


