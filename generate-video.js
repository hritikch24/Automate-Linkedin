// generate-video.js - GitHub Actions compatible version

const fs = require('fs-extra');
const axios = require('axios');
const { google } = require('googleapis');
const ffmpegPath = require('@ffmpeg-installer/ffmpeg').path;
const ffmpeg = require('fluent-ffmpeg');

ffmpeg.setFfmpegPath(ffmpegPath);

// ----- CONFIGURATION -----
const config = {
  // Use environment variables for sensitive data
  geminiApiKey: process.env.GEMINI_API_KEY,
  youtubeClientId: process.env.YOUTUBE_CLIENT_ID,
  youtubeClientSecret: process.env.YOUTUBE_CLIENT_SECRET, 
  youtubeRefreshToken: process.env.YOUTUBE_REFRESH_TOKEN,
  
  // Categories to rotate through
  categories: [
    "history", 
    "geography", 
    "science", 
    "ancient_civilizations", 
    "space", 
    "ocean"
  ],
  
  // Video settings
  factsPerVideo: 5,
  
  // File paths
  factsDatabasePath: "./facts_database.json",
  videoTemplatesPath: "./video_templates/",
  outputPath: "./output_videos/",
  
  // Verification settings
  verificationThreshold: 2, // How many verifications must match
};

// ----- FACT GENERATION AND VERIFICATION -----

/**
 * Generates facts using Gemini API for a specific category
 */
async function generateFactsForCategory(category, count = 10) {
  console.log(`Generating ${count} facts for category: ${category}`);
  
  const prompt = `Generate ${count} interesting, uncommon, and verified facts about ${category}. 
  Each fact should be 1-2 sentences, accurate, engaging, and suitable for a YouTube shorts or reels video.
  Format the output as a JSON array of strings, with each string being a single fact.`;
  
  try {
    const response = await axios.post(
      'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent',
      {
        contents: [{
          parts: [{
            text: prompt
          }]
        }],
        generationConfig: {
          temperature: 0.2,
          topK: 40,
          topP: 0.95,
          maxOutputTokens: 1024,
        }
      },
      {
        headers: {
          'Content-Type': 'application/json',
          'x-goog-api-key': config.geminiApiKey
        }
      }
    );
    
    // Extract the text response and parse JSON from it
    const textResponse = response.data.candidates[0].content.parts[0].text;
    const jsonMatch = textResponse.match(/\[[\s\S]*\]/);
    
    if (jsonMatch) {
      try {
        const factsArray = JSON.parse(jsonMatch[0]);
        return factsArray;
      } catch (e) {
        console.error("Failed to parse JSON from Gemini response:", e);
        return [];
      }
    } else {
      console.error("No JSON array found in Gemini response");
      return [];
    }
  } catch (error) {
    console.error("Error generating facts:", error.message);
    return [];
  }
}

/**
 * Verifies a fact by checking it multiple times
 */
async function verifyFact(fact) {
  console.log(`Verifying fact: ${fact.substring(0, 50)}...`);
  
  // Three different verification prompts
  const verificationPrompts = [
    `Is the following fact accurate? "${fact}" Please respond with only "TRUE" or "FALSE" and nothing else.`,
    `Verify if this statement is factually correct: "${fact}" Respond only with "TRUE" or "FALSE".`,
    `Fact-check the following: "${fact}" Answer only "TRUE" or "FALSE" based on factual accuracy.`
  ];
  
  const results = [];
  
  // Run three separate verification checks
  for (const prompt of verificationPrompts) {
    try {
      const response = await axios.post(
        'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent',
        {
          contents: [{
            parts: [{
              text: prompt
            }]
          }],
          generationConfig: {
            temperature: 0,
            topK: 1,
            topP: 0.1,
            maxOutputTokens: 10,
          }
        },
        {
          headers: {
            'Content-Type': 'application/json',
            'x-goog-api-key': config.geminiApiKey
          }
        }
      );
      
      const verification = response.data.candidates[0].content.parts[0].text.trim().toUpperCase();
      results.push(verification.includes("TRUE"));
      
      // Add delay to avoid rate limiting
      await new Promise(resolve => setTimeout(resolve, 1000));
      
    } catch (error) {
      console.error("Error during verification:", error.message);
      results.push(false);
    }
  }
  
  // Count how many verifications passed
  const verificationsPassed = results.filter(result => result).length;
  console.log(`Verification results: ${results.join(', ')} (${verificationsPassed}/${results.length} passed)`);
  
  return {
    fact,
    verified: verificationsPassed >= config.verificationThreshold,
    score: verificationsPassed
  };
}

/**
 * Generate facts for all categories or refresh existing ones
 */
async function generateAndVerifyFacts() {
  let factsDatabase = { 
    lastUpdated: new Date().toISOString(),
    categories: {}
  };
  
  // Try to load existing database
  try {
    if (await fs.pathExists(config.factsDatabasePath)) {
      factsDatabase = await fs.readJson(config.factsDatabasePath);
      console.log("Loaded existing facts database");
    }
  } catch (error) {
    console.log("No existing database found, creating new one");
  }
  
  // Process each category
  for (const category of config.categories) {
    // Only generate facts if we don't have enough unused ones
    const existingFacts = factsDatabase.categories[category] || [];
    const unusedFacts = existingFacts.filter(fact => !fact.used);
    
    if (unusedFacts.length >= config.factsPerVideo * 2) {
      console.log(`Sufficient facts for ${category}, skipping generation`);
      continue;
    }
    
    console.log(`Processing category: ${category}`);
    
    // Generate initial facts
    const generatedFacts = await generateFactsForCategory(category, 15);
    
    // Verify each fact
    const verifiedFacts = [];
    for (const fact of generatedFacts) {
      const verificationResult = await verifyFact(fact);
      if (verificationResult.verified) {
        verifiedFacts.push({
          text: fact,
          category,
          verificationScore: verificationResult.score,
          dateAdded: new Date().toISOString(),
          used: false
        });
      }
    }
    
    // Add to database
    if (!factsDatabase.categories[category]) {
      factsDatabase.categories[category] = [];
    }
    factsDatabase.categories[category].push(...verifiedFacts);
    console.log(`Added ${verifiedFacts.length} verified facts for ${category}`);
    
    // Artificial delay to avoid API rate limits
    await new Promise(resolve => setTimeout(resolve, 5000));
  }
  
  // Update timestamp
  factsDatabase.lastUpdated = new Date().toISOString();
  
  // Save to file
  await fs.writeJson(config.factsDatabasePath, factsDatabase, { spaces: 2 });
  console.log("Facts database updated successfully");
  
  return factsDatabase;
}

// ----- VIDEO CREATION -----

/**
 * Creates a video for a set of facts using a template
 */
async function createFactVideo(facts, category) {
  const outputFileName = `${category}_${new Date().toISOString().replace(/[:.]/g, '-')}.mp4`;
  const outputPath = `${config.outputPath}${outputFileName}`;
  
  console.log(`Creating video for ${category} with ${facts.length} facts...`);
  
  // Ensure output directory exists
  await fs.ensureDir(config.outputPath);
  
  // For GitHub Actions, we'll use a simpler approach by creating image slides
  // and combining them with FFmpeg
  const slidesDir = './temp_slides/';
  await fs.ensureDir(slidesDir);
  
  // Here we would normally create image slides for each fact
  // But for MVP purposes, we'll just create a text file with the facts
  const factsText = facts.map((fact, index) => `Fact ${index + 1}: ${fact.text}`).join('\n\n');
  await fs.writeFile(`${config.outputPath}${category}_facts.txt`, factsText);
  
  // In a real implementation, this would create a video using FFmpeg
  // For now, we'll just return the text file path to demonstrate
  console.log(`Created facts text file: ${config.outputPath}${category}_facts.txt`);
  return `${config.outputPath}${category}_facts.txt`;
}

// ----- YOUTUBE INTEGRATION -----

/**
 * Authenticates with YouTube API using stored refresh token
 */
async function authenticateYouTube() {
  const oauth2Client = new google.auth.OAuth2(
    config.youtubeClientId,
    config.youtubeClientSecret,
    'http://localhost:3000/oauth2callback'
  );
  
  // Use refresh token from environment variable
  oauth2Client.setCredentials({
    refresh_token: config.youtubeRefreshToken
  });
  
  try {
    // Force token refresh
    const tokens = await oauth2Client.refreshAccessToken();
    oauth2Client.setCredentials(tokens.credentials);
    console.log("YouTube API authentication successful");
    return oauth2Client;
  } catch (error) {
    console.error("Error refreshing YouTube token:", error.message);
    throw error;
  }
}

/**
 * Uploads a video to YouTube (simplified for demo)
 */
async function uploadToYouTube(videoPath, title, description, tags, categoryId = '27') {
  try {
    const auth = await authenticateYouTube();
    const youtube = google.youtube('v3');
    
    console.log(`Preparing to upload to YouTube: ${title}`);
    
    // Since we don't have a real video in this demo, we'll just output the metadata
    console.log(`VIDEO UPLOAD SIMULATION`);
    console.log(`Title: ${title}`);
    console.log(`Description: ${description}`);
    console.log(`Tags: ${tags.join(', ')}`);
    
    // In a real implementation, this would be the upload code:
    /*
    const res = await youtube.videos.insert({
      auth,
      part: 'snippet,status',
      requestBody: {
        snippet: {
          title,
          description,
          tags,
          categoryId
        },
        status: {
          privacyStatus: 'private'  // Start as private for review
        }
      },
      media: {
        body: fs.createReadStream(videoPath)
      }
    });
    
    return res.data.id;
    */
    
    // For demo purposes, return a fake video ID
    return `DEMO_VIDEO_${Date.now()}`;
  } catch (error) {
    console.error("Error preparing YouTube upload:", error.message);
    throw error;
  }
}

// ----- MAIN AUTOMATION FUNCTIONS -----

/**
 * Gets unused facts from the database
 */
async function getUnusedFacts(category, count) {
  try {
    const database = await fs.readJson(config.factsDatabasePath);
    const categoryFacts = database.categories[category] || [];
    
    // Get unused facts
    const unusedFacts = categoryFacts.filter(fact => !fact.used).slice(0, count);
    
    // If we don't have enough, generate more
    if (unusedFacts.length < count) {
      console.log(`Not enough unused facts for ${category}, generating more...`);
      await generateAndVerifyFacts();
      
      // Read the updated database
      const updatedDb = await fs.readJson(config.factsDatabasePath);
      const updatedCategoryFacts = updatedDb.categories[category] || [];
      return updatedCategoryFacts.filter(fact => !fact.used).slice(0, count);
    }
    
    return unusedFacts;
  } catch (error) {
    console.error("Error getting unused facts:", error);
    return [];
  }
}

/**
 * Marks facts as used in the database
 */
async function markFactsAsUsed(facts) {
  try {
    const database = await fs.readJson(config.factsDatabasePath);
    
    facts.forEach(fact => {
      const category = fact.category;
      const factIndex = database.categories[category].findIndex(f => 
        f.text === fact.text && f.dateAdded === fact.dateAdded
      );
      
      if (factIndex !== -1) {
        database.categories[category][factIndex].used = true;
        database.categories[category][factIndex].usedDate = new Date().toISOString();
      }
    });
    
    await fs.writeJson(config.factsDatabasePath, database, { spaces: 2 });
    console.log(`Marked ${facts.length} facts as used in the database`);
  } catch (error) {
    console.error("Error marking facts as used:", error);
  }
}

/**
 * Creates and uploads a video for a category
 */
async function createAndUploadVideo(category) {
  try {
    console.log(`Starting video creation process for category: ${category}`);
    
    // Get facts for this video
    const facts = await getUnusedFacts(category, config.factsPerVideo);
    
    if (facts.length < config.factsPerVideo) {
      console.warn(`Warning: Only found ${facts.length} facts for ${category}`);
      if (facts.length === 0) {
        console.error(`Error: No facts available for ${category}`);
        return;
      }
    }
    
    // Create the video
    const videoPath = await createFactVideo(facts, category);
    
    // Upload to YouTube
    const title = `${facts.length} Amazing ${category.charAt(0).toUpperCase() + category.slice(1)} Facts You Never Knew!`;
    const description = `Discover these amazing facts about ${category}!\n\n` +
                        facts.map(fact => `• ${fact.text}`).join('\n\n') + 
                        '\n\n#facts #' + category + ' #didyouknow';
    
    const tags = ['facts', category, 'did you know', 'amazing facts', 'interesting'];
    
    const videoId = await uploadToYouTube(videoPath, title, description, tags);
    
    // Mark facts as used
    await markFactsAsUsed(facts);
    
    console.log(`Complete video process for ${category}, Video ID: ${videoId}`);
    return videoId;
  } catch (error) {
    console.error(`Error in video creation/upload for ${category}:`, error);
  }
}

// ----- MAIN EXECUTION FOR GITHUB ACTIONS -----

/**
 * Main function to run in GitHub Actions
 */
async function main() {
  try {
    console.log("Starting YouTube Facts Video Automation...");
    
    // Ensure directories exist
    await fs.ensureDir(config.outputPath);
    await fs.ensureDir(config.videoTemplatesPath);
    
    // Check if facts database exists, create if not
    const databaseExists = await fs.pathExists(config.factsDatabasePath);
    if (!databaseExists) {
      console.log("Facts database not found, generating initial facts...");
      await generateAndVerifyFacts();
    }
    
    // Determine which category to use for this run
    // For GitHub Actions, we'll rotate based on the current day/time
    const date = new Date();
    const categoryIndex = (date.getDate() * 2 + (date.getHours() >= 12 ? 1 : 0)) % config.categories.length;
    const category = config.categories[categoryIndex];
    
    console.log(`Selected category for this run: ${category}`);
    
    // Create and upload video
    await createAndUploadVideo(category);
    
    console.log("Video automation completed successfully");
  } catch (error) {
    console.error("Error in main execution:", error);
    process.exit(1);
  }
}

// Run the main function
main();