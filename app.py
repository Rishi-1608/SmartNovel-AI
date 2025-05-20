from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Configure Gemini
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

WORKING_MODELS = [
    'gemini-1.5-flash',
    'gemini-1.5-pro',
    'gemini-pro'
]

def get_working_model():
    """Find first available model from the recommended list"""
    try:
        available_models = [m.name for m in genai.list_models()]
        for model in WORKING_MODELS:
            if model in available_models:
                return model
    except Exception as e:
        pass
    return 'gemini-1.5-flash'

def is_hindi(text):
    """Check if text contains Hindi characters"""
    hindi_range = range(0x0900, 0x097F+1)
    return any(ord(char) in hindi_range for char in text)

def generate_story_continuation(current_story, choice, genre, tone, language, setting, characters):
    """Generate continuation based on user's choice"""
    model = genai.GenerativeModel(get_working_model())
    
    if language == 'hindi':
        prompt = f"""निम्नलिखित कहानी को आगे बढ़ाएं:
        {current_story}
        
        उपयोगकर्ता का चयन:
        {choice}
        
        विवरण:
        - शैली: {genre}
        - स्वर: {tone}
        - सेटिंग: {setting}
        - मुख्य पात्र: {characters['protagonist']}
        - प्रतिपक्षी: {characters['antagonist']}
        
        नई सामग्री उत्पन्न करें जो:
        - चयन के साथ सहजता से जुड़ती हो
        - कहानी को आगे बढ़ाए
        - 3-5 नए पैराग्राफ जोड़े
        - उचित चरमोत्कर्ष की ओर बढ़े"""
    else:
        prompt = f"""Continue the following story:
        {current_story}
        
        User's choice:
        {choice}
        
        Details:
        - Genre: {genre}
        - Tone: {tone}
        - Setting: {setting}
        - Protagonist: {characters['protagonist']}
        - Antagonist: {characters['antagonist']}
        
        Generate new content that:
        - Flows naturally from the choice
        - Advances the story
        - Adds 3-5 new paragraphs
        - Moves toward a proper climax"""
    
    response = model.generate_content(prompt)
    return response.text
@app.route('/')
def landing():
    """Landing page route"""
    return render_template('landing.html')

@app.route('/start', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            # Get all form inputs
            prompt = request.form['prompt']
            genre = request.form['genre']
            length = request.form['length']
            language = request.form['language']
            tone = request.form['tone']
            setting = request.form.get('setting', '')
            protagonist = request.form.get('protagonist', '')
            antagonist = request.form.get('antagonist', '')
            
            model_name = get_working_model()
            model = genai.GenerativeModel(model_name)
            
            if language == 'hindi':
                instruction = f"""आप एक पेशेवर {genre} कहानी लेखक हैं।
                {tone} स्वर में एक {length} कहानी लिखें उचित चरमोत्कर्ष और अंत के साथ।
                upvukt seershak k sath.
                
                मुख्य विवरण:
                - संकेत: {prompt}
                - सेटिंग: {setting or 'अनिर्दिष्ट'}
                - मुख्य पात्र: {protagonist or 'अनिर्दिष्ट'}
                - प्रतिपक्षी: {antagonist or 'कोई नहीं'}
                
                आवश्यकताएँ:
                - उचित लंबाई ({length})
                - {tone} स्वर बनाए रखें
                - पात्र विकास
                - संतोषजनक समापन"""
            else:
                instruction = f"""You are a professional {genre} story writer.
                Write a {length} story in a {tone} tone with proper climax and ending.
                Generate a sutaible title as well.
                
                Key Details:
                - Prompt: {prompt}
                - Setting: {setting or 'unspecified'}
                - Protagonist: {protagonist or 'unnamed'}
                - Antagonist: {antagonist or 'none'}
                
                Requirements:
                - Appropriate length ({length})
                - Maintain {tone} tone throughout
                - Character development
                - Satisfying ending
                - Rich descriptions of {setting or 'the environment'}"""
            
            response = model.generate_content(instruction)
            story = response.text
            
            # Also generate initial continuation options
            continuation_options = generate_continuation_options(
                story, 
                genre, 
                tone, 
                language,
                setting,
                {
                    'protagonist': protagonist,
                    'antagonist': antagonist
                }
            )
            
            return render_template('story.html', 
                                story=story, 
                                prompt=prompt,
                                is_hindi=is_hindi(story),
                                genre=genre,
                                tone=tone,
                                setting=setting,
                                characters={
                                    'protagonist': protagonist,
                                    'antagonist': antagonist
                                },
                                continuation_options=continuation_options)
            
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            return render_template('error.html', message=error_msg)
    
    return render_template('index.html')

def generate_continuation_options(story, genre, tone, language, setting, characters):
    """Generate possible continuation options for the story"""
    model = genai.GenerativeModel(get_working_model())
    
    if language == 'hindi':
        prompt = f"""इस कहानी के लिए 3 संभावित जारी रखने के विकल्प सुझाएं:
        {story}
        
        विवरण:
        - शैली: {genre}
        - स्वर: {tone}
        - सेटिंग: {setting}
        - मुख्य पात्र: {characters['protagonist']}
        - प्रतिपक्षी: {characters['antagonist']}
        
        प्रत्येक विकल्प:
        - 1-2 वाक्य लंबा हो
        - कहानी को अलग-अलग दिशाओं में ले जाए
        - पात्रों और सेटिंग के अनुरूप हो"""
    else:
        prompt = f"""Suggest 3 possible continuation options for this story:
        {story}
        
        Details:
        - Genre: {genre}
        - Tone: {tone}
        - Setting: {setting}
        - Protagonist: {characters['protagonist']}
        - Antagonist: {characters['antagonist']}
        
        Each option should:
        - Be 1-2 sentences long
        - Take the story in different directions
        - Be consistent with characters and setting"""
    
    response = model.generate_content(prompt)
    options_text = response.text
    
    # Parse the options from the response
    options = []
    for line in options_text.split('\n'):
        line = line.strip()
        if line and (line.startswith('1.') or line.startswith('2.') or line.startswith('3.')):
            option_text = line.split('.', 1)[1].strip()
            options.append(option_text)
    
    return options[:3]  # Return max 3 options
@app.route('/generate_options', methods=['POST'])
def generate_options():
    try:
        story_so_far = request.form['story_so_far']
        genre = request.form.get('genre', 'fantasy')
        language = request.form.get('language', 'english')
        
        model = genai.GenerativeModel(get_working_model())
        
        if language == 'hindi':
            prompt = f"""यह कहानी अब तक:
            {story_so_far}
            
            कृपया इस कहानी के लिए 3 संभावित अगले चरण सुझाएं। प्रत्येक विकल्प 1-2 वाक्यों में होना चाहिए।"""
        else:
            prompt = f"""Here's the story so far:
            {story_so_far}
            
            Please suggest 3 possible next steps for this story. Each option should be 1-2 sentences long.
            
            Format as:
            1. [Option 1]
            2. [Option 2]
            3. [Option 3]"""
        
        response = model.generate_content(prompt)
        options_text = response.text
        
        # Parse the options
        options = []
        for line in options_text.split('\n'):
            line = line.strip()
            if line and (line.startswith('1.') or line.startswith('2.') or line.startswith('3.')):
                option_text = line.split('.', 1)[1].strip()
                options.append(option_text)
        
        return jsonify({
            'success': True,
            'options': options[:3]  # Return max 3 options
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })
@app.route('/continue_story', methods=['POST'])
def continue_story():
    """Endpoint for continuing the story based on user choice"""
    try:
        data = request.json
        continuation = generate_story_continuation(
            data['current_story'],
            data['choice'],
            data['genre'],
            data['tone'],
            data['language'],
            data['setting'],
            data['characters']
        )
        
        # Generate new options for the continued story
        new_options = generate_continuation_options(
            continuation,
            data['genre'],
            data['tone'],
            data['language'],
            data['setting'],
            data['characters']
        )
        
        return jsonify({
            'success': True,
            'continued_story': continuation,
            'new_options': new_options
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    app.run(debug=True)