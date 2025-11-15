# Image Description Generator

A web application that uses OpenAI's GPT-4 Vision API to generate detailed descriptions of images from URLs.

## Features

- 🖼️ Input an image URL and get a detailed description
- 🤖 Powered by OpenAI GPT-4 Vision
- 🎨 Beautiful, modern UI
- 📱 Responsive design
- 🔒 Secure API key management using environment variables

## Prerequisites

- Python 3.7 or higher
- OpenAI API key (get one from [OpenAI Platform](https://platform.openai.com/api-keys))

## Installation

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up your OpenAI API key:**
   
   a. Copy the example environment file:
   ```bash
   copy .env.example .env
   ```
   (On Linux/Mac: `cp .env.example .env`)
   
   b. Open the `.env` file and replace `YOUR_API_KEY_HERE` with your actual OpenAI API key:
   ```
   OPENAI_API_KEY=sk-your-actual-api-key-here
   ```

   **How to get your OpenAI API key:**
   1. Go to [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
   2. Sign in or create an account
   3. Click "Create new secret key"
   4. Copy the key (it starts with `sk-`)
   5. Paste it in your `.env` file

   ⚠️ **Important:** Never share your API key or commit it to version control. The `.env` file is already in `.gitignore` to prevent accidental commits.

## Running the Application

1. **Start the Flask server:**
   ```bash
   python app.py
   ```

2. **Open your browser and navigate to:**
   ```
   http://localhost:5000
   ```

3. **Enter an image URL** in the input field and click "Describe Image"

## Usage

1. Find an image URL (e.g., from the internet)
2. Paste the URL into the input field
3. Click "Describe Image"
4. Wait for the AI to analyze and describe the image
5. View the detailed description and image preview

## Example Image URLs

You can test with these example URLs:
- `https://images.unsplash.com/photo-1506905925346-21bda4d32df4`
- `https://images.unsplash.com/photo-1518791841217-8f162f1e1131`
- `https://images.unsplash.com/photo-1498050108023-c5249f4df085`

## Troubleshooting

### "OpenAI API key is not configured"
- Make sure you created a `.env` file (not just `.env.example`)
- Verify your API key is correct in the `.env` file
- Restart the Flask server after adding the API key

### "Invalid OpenAI API key"
- Check that your API key is correct
- Make sure there are no extra spaces or quotes around the key
- Verify your API key is active on the OpenAI platform

### "Rate limit exceeded"
- You've made too many requests. Wait a moment and try again
- Check your OpenAI account usage limits

### Image won't load
- Verify the image URL is accessible
- Some images may be blocked by CORS policies
- Try a different image URL

## Project Structure

```
.
├── app.py              # Flask application and OpenAI integration
├── templates/
│   └── index.html     # Frontend HTML/CSS/JavaScript
├── requirements.txt    # Python dependencies
├── .env.example       # Example environment file
├── .env               # Your actual API key (create this, don't commit)
└── README.md          # This file
```

## Notes

- The application downloads images from URLs and converts them to base64 for OpenAI API
- Image data is included in the response for preview
- The app uses GPT-4 Vision Preview model for image analysis
- All API calls are made server-side for security

## License

This project is open source and available for personal and educational use.

