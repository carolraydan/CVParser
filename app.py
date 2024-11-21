
from dotenv import load_dotenv
import os
import nest_asyncio
import json
from llama_parse import LlamaParse
import gradio as gr

# Retrieve the API key from environment variables
api_key = os.getenv("apikey")

nest_asyncio.apply()

# If theres any css code you would like to add or design further. 
css = """ 



 """



# Define parsing instruction (you can keep this as is)
parsing_instruction = """Now first:
• Read and understand the content of the CV thoroughly.
• Please follow this prompt without making any assumptions. 
• Identify relevant sections by Analyzing the context of the words before or after each section.

Fields to extract and format even if the language in the document is classified as arabic:

For each field, ensure that the extracted information follows this structure:

 - Full Name: [Extracted Full Name ]
 - First Name: [Extracted First Name]
 - Fathers Name: [Extracted Fathers (Middle) Name]
 - Last Name: [Extracted Last Name]
 - Nationality: [Extracted Nationality]

Education Section:

For each education entry, label it as Education 1, Education 2, etc., and structure the output like this:

 - Education 1:
    - University/School: [Extracted Institution Name]
    - Degree/Certificate: [Extracted Degree]
    - Date: [Extracted Date of Attendance]

Certifications Section:

 - Certifications: [Extracted Certifications]

 Experience Section:

Ensure no experience entry is ignored, even if similar keywords or phrases are repeated. Label each instance as 'Experience 1,' 'Experience 2,' and so on, and structure the output as follows:

 - Experience 1:
    - Job Title: [Job Title/Position]
    - Company: [Company Name]
    - LOE (Location of Experience): [Location]
    - Date: [Start Date] – [End Date]

 Membership committee section: 

    - Board Name: [Job Title/Position]
    - Organisation Name: [Job Title/Position]
    - Date: [Start Date] – [End Date]



Further Instructions:

• If any field cannot be found or is blank, leave it empty under that section name.
• If there are multiple "Experience" or "Education" sections, label them as Experience 1, Experience 2, or Education 1, Education 2, respectively, and follow the structure provided for each section.
• Ensure all duties in the experience section are presented as bullet points, if available.
• please do not add fields that are not included or mentioned in the prompt. 

Warning: Some CVs may have a two-column layout, where important information (such as personal details, contact info, or experience) is split across two columns or multiple sections. This layout may cause the following irregularities: 
 - Experience, education, or skills may also be distributed across different columns, requiring careful attention to combine them correctly. 
- Information such as job titles, companies, dates, and descriptions of responsibilities may not always be presented in a single, continuous flow and might be split between the two columns. In such cases: 
- Be aware of the layout structure and pay attention to how information flows across columns. - If a field appears split or fragmented across the CV, carefully merge the pieces to provide a coherent, complete output. 
- Use context to understand where certain details belong, even if they are presented in irregular or non-standard ways (such as duties listed in one column, and job title in another).

please output the parsed cv in this json format template: 

{
  "Full Name": "John michael Doe",
  "First Name": "John",
  "Fathers Name": "michael",
  "Last Name": "Doe",
  "Nationality": "American",
  "Education": [
    {
      "University/School": "University of Example",
      "Degree/Certificate": "Bachelor of Science",
      "Date": "2010-2014"
    },
    {
      "University/School": "Another University",
      "Degree/Certificate": "Master of Science",
      "Date": "2015-2017"
    }
  ],
  "Certifications": [
    "Certified Professional Engineer",
    "Project Management Professional"
  ],
  "Experience": [
    {
      "Job Title": "Software Engineer",
      "Company": "Tech Solutions Inc.",
      "LOE": "New York",
      "Date": "2015-2020",
    },
    {
      "Job Title": "Senior Software Engineer",
      "Company": "Innovatech",
      "LOE": "San Francisco",
      "Date": "2020-Present",
    }
  ],
  "Membership Committee": [
    {
      "Board Name": "Engineering Standards Board",
      "Organisation Name": "Tech Community",
      "Date": "2021-Present"
    },
    {
      "Board Name": "Tech Advisory Board",
      "Organisation Name": "Global Innovations Group",
      "Date": "2018-2021"
    }
  ]
}

"""

 #Define parsing instruction (you can keep this as is)
def extract_field(content, field_name):
    """Helper function to extract specific fields from the content, including multi-line entries."""
    entries = []
    lines = content.split('\n')
    capture = False
    entry = ""

    for line in lines:
        stripped_line = line.strip()
        
        if stripped_line.startswith(field_name):
            if entry:
                entries.append(entry.strip())  # Add the previous entry
            entry = stripped_line  # Start a new entry with the matched line
            capture = True
        elif capture and not stripped_line.startswith("Experience") and not stripped_line.startswith("Education") and stripped_line:
            entry += " " + stripped_line  # Append content to the current entry
        elif capture and stripped_line == "":
            capture = False  # Stop capturing on an empty line, end of entry

    if entry:
        entries.append(entry.strip())  # Add the last entry

    return entries if entries else ["Not Found"]




# Set up parser with the API key
parser = LlamaParse(
    api_key=api_key,
    premium_mode=True,
    result_type="markdown",
    parsing_instruction=parsing_instruction,
    num_workers=4,
    verbose=True,
    disable_ocr=True,
    language='en'
)

def parse_cv(profile_picture, file):
    # Load and parse the document
    parsed_output = parser.load_data(file.name)  # Load the uploaded file
    
    # Try to retrieve JSON-like data from the document
    content = getattr(parsed_output[0], 'text', None)  # or 'content' if 'text' doesn't work
    
    # Parse the JSON data if available
    if content:
        parsed_data = json.loads(content)  # Convert the JSON-like string to a dictionary
    else:
        return "Error: Could not retrieve content from Document object"

    # Map parsed data to Gradio output format
    result = {
        "Full Name": parsed_data.get("Full Name", "Not Found"),
        "First Name": parsed_data.get("First Name", "Not Found"),
        "Fathers Name": parsed_data.get("Fathers Name", "Not Found"),
        "Last Name": parsed_data.get("Last Name", "Not Found"),
        "Nationality": parsed_data.get("Nationality", "Not Found"),
        "Education": "\n\n".join(
            [f"University/School: {edu.get('University/School', 'N/A')}\n"
             f"Degree/Certificate: {edu.get('Degree/Certificate', 'N/A')}\n"
             f"Date: {edu.get('Date', 'N/A')}" for edu in parsed_data.get("Education", [])]
        ),
        "Experience": "\n\n".join(
            [f"Job Title: {exp.get('Job Title', 'N/A')}\n"
             f"Company: {exp.get('Company', 'N/A')}\n"
             f"Location of Experience: {exp.get('LOE', 'N/A')}\n"
             f"Date: {exp.get('Date', 'N/A')}" for exp in parsed_data.get("Experience", [])]
        ),
        "Certification": "\n".join(parsed_data.get("Certifications", ["Not Found"])),
    }

    return (
        result["Full Name"],
        result["First Name"],
        result["Fathers Name"],
        result["Last Name"],
        result["Nationality"],
        result["Education"] if result["Education"] else "Not Found",
        result["Experience"] if result["Experience"] else "Not Found",
        result["Certification"] if result["Certification"] else "Not Found",
    )


# Set up the Gradio interface with editable textboxes
iface = gr.Interface(
    fn=parse_cv,
    inputs=[
        gr.Image(label="Upload Profile Picture (optional)", type="filepath"),  # Placeholder for profile picture
        gr.File(label="Upload CV (PDF, DOCX, PPTX)")
    ],
    
    outputs=[
        gr.Textbox(label="Full Name", interactive=True),
        gr.Textbox(label="First Name", interactive=True),
        gr.Textbox(label="Fathers Name", interactive=True),
        gr.Textbox(label="Last Name", interactive=True),
        gr.Textbox(label="Nationality", interactive=True),
        gr.Textbox(label="Education", interactive=True),  
        gr.Textbox(label="Experience", interactive=True),  
        gr.Textbox(label="Certification", interactive=True ),
    ],
    title="CV Parser",
    description="Upload a CV document, and it will be parsed to extract relevant information.",
    flagging_mode="never", css=css
)

# Launch the Gradio app
iface.launch(share=True)