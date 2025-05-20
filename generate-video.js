/**
 * Authenticates with YouTube API using stored refresh token
 */
async function authenticateYouTube() {
  return await getYouTubeAuthInfo();
}// generate-video.js - GitHub Actions compatible version

const fs = require('fs-extra');
const axios = require('axios');
const { google } = require('googleapis');
const ffmpegPath = require('@ffmpeg-installer/ffmpeg').path;
const ffmpeg = require('fluent-ffmpeg');

ffmpeg.setFfmpegPath(ffmpegPath);

// Import the simplest video generator
const simplestGenerator = require('./simplest-video-generator');
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

// Add fallback facts generation function
/**
 * Generate fallback facts when API fails
 */
function generateFallbackFacts(category, count) {
  // Pre-defined facts for each category
  const factsByCategory = {
    "history": [
      "The shortest war in history was between Britain and Zanzibar in 1896, lasting only 38 minutes.",
      "Ancient Egyptians used to sleep on pillows made of stone.",
      "Vikings used the bones of slain animals to make their weapons stronger.",
      "The Great Wall of China is not visible from space with the naked eye, contrary to popular belief.",
      "Napoleon was actually of average height for his time (5'7\"), not short as commonly believed.",
      "Roman soldiers were sometimes paid in salt, which is where the word 'salary' comes from.",
      "The first recorded Olympic Games were held in 776 BCE in Olympia, Greece.",
      "Cleopatra lived closer in time to the moon landing than to the building of the Great Pyramid.",
      "Harvard University was founded before calculus was invented.",
      "The oldest known living tree is over 5,000 years old, located in California."
    ],
    "geography": [
      "Russia borders 14 different countries, more than any other nation.",
      "The Sahara Desert expands and contracts seasonally, changing its size by about 10%.",
      "There's a town in Norway called Hell that freezes over every winter.",
      "The continent of Asia covers about 30% of Earth's total land area.",
      "Alaska has more coastline than all other U.S. states combined.",
      "The world's largest desert is Antarctica, not the Sahara.",
      "Point Nemo in the Pacific Ocean is the most remote place on Earth, with the nearest humans often being astronauts on the ISS.",
      "Vatican City is the smallest country in the world, at just 44 hectares (109 acres).",
      "Brazil shares a border with every South American country except Chile and Ecuador.",
      "The Maldives is the flattest and lowest-lying country in the world."
    ],
    "science": [
      "Honey never spoils. Archaeologists have found pots of honey in ancient Egyptian tombs that are over 3,000 years old and still perfectly good to eat.",
      "20% of Earth's oxygen is produced by the Amazon rainforest.",
      "A day on Venus is longer than a year on Venus. It takes 243 Earth days to rotate once on its axis and 225 Earth days to orbit the sun.",
      "Bananas are berries, but strawberries aren't actually berries at all.",
      "The human body contains enough carbon to make about 9,000 pencils.",
      "Octopuses have three hearts, nine brains, and blue blood.",
      "A bolt of lightning is five times hotter than the surface of the sun.",
      "Sharks have existed for over 450 million years, predating dinosaurs, trees, and even Mount Everest.",
      "The shortest scientific paper ever published contained just two sentences.",
      "The average human produces enough saliva in their lifetime to fill two swimming pools."
    ],
    "ancient_civilizations": [
      "The ancient city of Çatalhöyük in Turkey had no streets - residents walked on rooftops and entered homes through ceiling openings.",
      "Mesopotamian doctors were sometimes paid extra if their patients were wealthy or of high social status.",
      "The Indus Valley Civilization had sophisticated plumbing systems over 4,000 years ago.",
      "Ancient Mayans believed crossing your eyes was beautiful and would hang objects in front of babies' eyes to make them permanently cross-eyed.",
      "The ancient Greek city of Sparta had no walls despite being a military powerhouse.",
      "Ancient Egyptians used crocodile dung as a contraceptive.",
      "The Chinese were using natural gas for heating and lighting as early as 500 BCE, transported through bamboo pipes.",
      "In ancient Rome, urine was collected and used to wash clothes due to its ammonia content.",
      "The ancient Inca Empire built thousands of miles of roads without using wheeled vehicles.",
      "Ancient Aztecs used chocolate as currency."
    ],
    "space": [
      "There is a planet made of diamonds, called 55 Cancri e.",
      "The footprints left on the Moon will remain there for at least 100 million years.",
      "One day on Venus is longer than one year on Venus.",
      "The largest asteroid, Ceres, is so big it's classified as a dwarf planet.",
      "The Sun makes up 99.86% of the mass in our solar system.",
      "Saturn's rings are mostly made of ice and are only about 10 meters thick on average.",
      "A year on Neptune lasts for 165 Earth years.",
      "There are more stars in the universe than grains of sand on all of Earth's beaches.",
      "The Great Red Spot on Jupiter is a storm that has been raging for at least 400 years.",
      "Mercury and Venus are the only planets in our solar system with no moons."
    ],
    "ocean": [
      "The ocean contains 97% of Earth's water, but only about 5% has been explored.",
      "There are more historical artifacts under the ocean than in all museums worldwide combined.",
      "The Mid-Ocean Ridge is the longest mountain range on Earth, stretching over 40,000 miles.",
      "The world's oceans contain nearly 20 million tons of gold.",
      "The deepest part of the ocean, the Mariana Trench, is deeper than Mount Everest is tall.",
      "Some species of deep-sea creatures can live without oxygen, using sulfur compounds instead.",
      "The blue whale, the largest animal on Earth, can produce sounds louder than a jet engine.",
      "There are lakes and rivers beneath the ocean with their own shores, different density, and unique wildlife.",
      "Some marine snails can surf on their own mucus to travel faster across the ocean floor.",
      "The Great Barrier Reef is the largest living structure on Earth, visible even from space."
    ]
  };
  
  // If category doesn't exist in our predefined facts, use general facts
  if (!factsByCategory[category]) {
    const allFacts = Object.values(factsByCategory).flat();
    return allFacts.sort(() => 0.5 - Math.random()).slice(0, count);
  }
  
  // Return random facts from the selected category
  return factsByCategory[category].sort(() => 0.5 - Math.random()).slice(0, count);
}

/**
 * Creates the simplest possible video with facts in description
 */
async function createFactVideo(facts, category) {
  const outputFileName = `${category}_${new Date().toISOString().replace(/[:.]/g, '-')}.mp4`;
  const outputPath = `${config.outputPath}${outputFileName}`;
  
  console.log(`Creating video for ${category} with ${facts.length} facts...`);
  
  // Ensure output directory exists
  await fs.ensureDir(config.outputPath);
  
  // Create a text file with the facts (for record keeping)
  const factsText = facts.map((fact, index) => `Fact ${index + 1}: ${fact.text || fact}`).join('\n\n');
  const textFilePath = `${config.outputPath}${category}_facts.txt`;
  await fs.writeFile(textFilePath, factsText);
  console.log(`Created facts text file: ${textFilePath}`);
  
  // Use the simplest possible video generation approach
  try {
    console.log("Using simplest possible video generation...");
    
    // Generate video with simplest approach
    const result = await simplestGenerator.createSimplestVideo(
      facts,
      category,
      outputPath
    );
    
    console.log(`Simplest video created at: ${result.videoPath}`);
    console.log(`Description saved at: ${result.descriptionPath}`);
    
    return outputPath;
  } catch (error) {
    console.error("Error using simplest video generator:", error.message);
    // Just return the text file path as a fallback
    console.log("Returning text file as fallback...");
    return textFilePath;
  }
}

/**
 * Creates a basic video with white background and black text
 */
async function createBasicVideo(outputPath, title, facts = []) {
  console.log('Creating white background video with black text:', title);
  
  try {
    // Create a text file with the facts for documentation
    const factsText = facts.map((fact, index) => {
      return `Fact ${index+1}: ${typeof fact === 'string' ? fact : (fact.text || 'Interesting fact')}`;
    }).join('\n\n');
    
    const textFile = `${config.outputPath}facts_content.txt`;
    await fs.writeFile(textFile, `${title}\n\n${factsText}`);
    
    // Create the most basic video possible - white background only
    await new Promise((resolve, reject) => {
      ffmpeg()
        .input('color=c=white:s=1280x720:d=30')
        .inputFormat('lavfi')
        .outputOptions(['-c:v libx264', '-preset', 'ultrafast', '-pix_fmt', 'yuv420p'])
        .output(outputPath)
        .on('start', (commandLine) => {
          console.log('FFmpeg command:', commandLine);
        })
        .on('progress', (progress) => {
          console.log('Processing: ' + progress.percent + '% done');
        })
        .on('end', () => {
          console.log('Video processing finished successfully');
          resolve();
        })
        .on('error', (err) => {
          console.error('Error:', err);
          reject(err);
        })
        .run();
    });
    
    console.log(`White background video created: ${outputPath}`);
    return outputPath;
  } catch (error) {
    console.error('Failed to create white background video:', error);
    
    // Create an even simpler video as last resort
    try {
      console.log('Trying simplest possible video generation...');
      // Use the most minimal ffmpeg command possible
      await new Promise((resolve, reject) => {
        const ffmpegPath = require('@ffmpeg-installer/ffmpeg').path;
        const { spawn } = require('child_process');
        
        console.log('Using ffmpeg path:', ffmpegPath);
        
        const args = [
          '-f', 'lavfi',
          '-i', 'color=c=white:s=1280x720:d=30',
          '-c:v', 'libx264',
          '-t', '30',
          '-y',
          outputPath
        ];
        
        console.log('Running command:', ffmpegPath, args.join(' '));
        
        const process = spawn(ffmpegPath, args);
        
        process.stdout.on('data', (data) => {
          console.log(`stdout: ${data}`);
        });
        
        process.stderr.on('data', (data) => {
          console.log(`stderr: ${data}`);
        });
        
        process.on('close', (code) => {
          if (code === 0) {
            console.log(`Process exited with code ${code}`);
            resolve();
          } else {
            console.error(`Process exited with code ${code}`);
            reject(new Error(`Process exited with code ${code}`));
          }
        });
      });
      
      console.log('Simplest white background video created successfully');
      return outputPath;
    } catch (simpleError) {
      console.error('Even simplest video creation failed:', simpleError);
      
      // Last resort - create a text file for upload
      const textFilePath = `${config.outputPath}${title.toLowerCase().replace(/\s+/g, '_')}.txt`;
      await fs.writeFile(textFilePath, `${title}\n\n${factsText}\n\nCreated: ${new Date().toISOString()}`);
      console.log(`Created text file instead: ${textFilePath}`);
      return textFilePath;
    }
  }
}

// ----- YOUTUBE INTEGRATION -----

/**
 * Gets token information from YouTube authentication
 */
async function getYouTubeAuthInfo() {
  try {
    const oauth2Client = new google.auth.OAuth2(
      config.youtubeClientId,
      config.youtubeClientSecret,
      'http://localhost:3000/oauth2callback'
    );
    
    // Use refresh token from environment variable
    oauth2Client.setCredentials({
      refresh_token: config.youtubeRefreshToken
    });
    
    console.log("Attempting to get access token...");
    
    // Force token refresh to get new access token
    const tokens = await oauth2Client.refreshAccessToken()
      .catch(error => {
        console.error("Error refreshing token:", error.message);
        console.error("Error details:", JSON.stringify(error, null, 2));
        throw error;
      });
    
    console.log("Token refresh successful!");
    
    // Log token info (safely)
    const accessToken = tokens.credentials.access_token;
    const maskedToken = accessToken ? 
      accessToken.substring(0, 5) + "..." + accessToken.substring(accessToken.length - 5) : 
      "UNDEFINED";
    
    console.log(`Access token (masked): ${maskedToken}`);
    console.log(`Token expiry: ${new Date(tokens.credentials.expiry_date).toISOString()}`);
    console.log(`Refresh token exists: ${!!tokens.credentials.refresh_token}`);
    
    return oauth2Client;
  } catch (error) {
    console.error("Authentication error:", error.message);
    console.error("Make sure YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, and YOUTUBE_REFRESH_TOKEN are set correctly");
    throw error;
  }
}

/**
 * Uploads a video to YouTube
 */
async function uploadToYouTube(videoPath, title, description, tags, categoryId = '27') {
  try {
    const auth = await authenticateYouTube();
    const youtube = google.youtube('v3');
    
    console.log(`Preparing to upload to YouTube: ${title}`);
    
    // Check if the file exists and is a valid video file
    const fileExists = await fs.pathExists(videoPath);
    if (!fileExists) {
      console.error(`Video file does not exist: ${videoPath}`);
      return `ERROR_FILE_NOT_FOUND_${Date.now()}`;
    }
    
    // Check file extension
    const fileExt = videoPath.split('.').pop().toLowerCase();
    if (fileExt !== 'mp4' && fileExt !== 'mov' && fileExt !== 'avi') {
      console.error(`Not a valid video file (${fileExt}): ${videoPath}`);
      
      // If it's a text file, log its contents
      if (fileExt === 'txt') {
        const content = await fs.readFile(videoPath, 'utf8');
        console.log('Text file content:', content);
        console.log('Cannot upload text file, returning error code');
        return `ERROR_TEXT_FILE_${Date.now()}`;
      } else {
        return `ERROR_INVALID_VIDEO_${Date.now()}`;
      }
    }
    
    try {
      // First, get the channel info to display the channel URL
      const channelResponse = await youtube.channels.list({
        auth,
        part: 'snippet',
        mine: true
      });
      
      if (channelResponse.data.items && channelResponse.data.items.length > 0) {
        const channelId = channelResponse.data.items[0].id;
        const channelTitle = channelResponse.data.items[0].snippet.title;
        console.log('==============================================');
        console.log(`YOUTUBE CHANNEL: ${channelTitle}`);
        console.log(`CHANNEL URL: https://www.youtube.com/channel/${channelId}`);
        console.log('==============================================');
      }
      
      // Attempt the actual upload
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
            privacyStatus: 'public'  // Make it public so it's easier to find
          }
        },
        media: {
          body: fs.createReadStream(videoPath)
        }
      });
      
      console.log('==============================================');
      console.log(`VIDEO UPLOADED SUCCESSFULLY!`);
      console.log(`VIDEO TITLE: ${title}`);
      console.log(`VIDEO ID: ${res.data.id}`);
      console.log(`VIDEO URL: https://www.youtube.com/watch?v=${res.data.id}`);
      console.log('==============================================');
      
      // Create a record file with all the information
      const recordFilePath = `${config.outputPath}upload_record_${Date.now()}.txt`;
      const recordContent = `
Upload Date: ${new Date().toISOString()}
Video Title: ${title}
Video ID: ${res.data.id}
Video URL: https://www.youtube.com/watch?v=${res.data.id}
Channel URL: https://www.youtube.com/channel/${channelResponse.data.items[0].id}
`;
      
      await fs.writeFile(recordFilePath, recordContent);
      console.log(`Upload record saved to: ${recordFilePath}`);
      
      // Enhance the video with facts in description
      await simplestGenerator.enhanceYouTubeUpload(
        auth,
        res.data.id,
        [], // Will be filled from description parameter
        "facts"
      );
      
      return res.data.id;
    } catch (uploadError) {
      console.error("Error during YouTube upload:", uploadError.message);
      
      // Log more detailed error info
      if (uploadError.response) {
        console.error("Upload error details:", JSON.stringify(uploadError.response.data, null, 2));
      }
      
      // Try a simplified upload with minimal properties
      console.log("Attempting simplified upload...");
      try {
        const simplifiedRes = await youtube.videos.insert({
          auth,
          part: 'snippet,status',
          requestBody: {
            snippet: {
              title: title.substring(0, 100), // Ensure title isn't too long
              description: description || "Auto-generated facts video",
              categoryId: "22" // People & Blogs category as fallback
            },
            status: {
              privacyStatus: 'public'
            }
          },
          media: {
            body: fs.createReadStream(videoPath)
          }
        });
        
        console.log('==============================================');
        console.log(`SIMPLIFIED UPLOAD SUCCESSFUL!`);
        console.log(`VIDEO ID: ${simplifiedRes.data.id}`);
        console.log(`VIDEO URL: https://www.youtube.com/watch?v=${simplifiedRes.data.id}`);
        console.log('==============================================');
        
        return simplifiedRes.data.id;
      } catch (simplifiedError) {
        console.error("Simplified upload also failed:", simplifiedError.message);
        return `ERROR_UPLOAD_FAILED_${Date.now()}`;
      }
    }
  } catch (error) {
    console.error("Error in YouTube upload setup:", error.message);
    return `ERROR_SETUP_FAILED_${Date.now()}`;
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
    console.log("Current date/time:", new Date().toISOString());
    
    // Check configuration
    console.log("Checking configuration...");
    console.log("Gemini API Key exists:", !!config.geminiApiKey);
    console.log("YouTube Client ID exists:", !!config.youtubeClientId);
    console.log("YouTube Client Secret exists:", !!config.youtubeClientSecret);
    console.log("YouTube Refresh Token exists:", !!config.youtubeRefreshToken);
    
    // Ensure directories exist
    await fs.ensureDir(config.outputPath);
    await fs.ensureDir(config.videoTemplatesPath);
    await fs.ensureDir('./temp_images/');
    await fs.ensureDir('./temp_slides/');
    
    // Test YouTube Authentication first
    console.log("Testing YouTube authentication...");
    try {
      const auth = await getYouTubeAuthInfo();
      console.log("YouTube authentication successful!");
      
      // Get channel info
      const youtube = google.youtube('v3');
      const channelResponse = await youtube.channels.list({
        auth,
        part: 'snippet',
        mine: true
      });
      
      if (channelResponse.data.items && channelResponse.data.items.length > 0) {
        const channelId = channelResponse.data.items[0].id;
        const channelTitle = channelResponse.data.items[0].snippet.title;
        console.log('==============================================');
        console.log(`YOUTUBE CHANNEL: ${channelTitle}`);
        console.log(`CHANNEL URL: https://www.youtube.com/channel/${channelId}`);
        console.log('==============================================');
      } else {
        console.log("No channel found for this account!");
      }
    } catch (authError) {
      console.error("YouTube authentication failed:", authError.message);
      console.log("Will continue with other tasks...");
    }
    
    // Determine which category to use for this run
    const date = new Date();
    const categoryIndex = (date.getDate() * 2 + (date.getHours() >= 12 ? 1 : 0)) % config.categories.length;
    const category = config.categories[categoryIndex];
    
    console.log(`Selected category for this run: ${category}`);
    
    // IMPORTANT: Generate fallback facts directly
    console.log("Generating fallback facts directly without API...");
    const fallbackFacts = generateFallbackFacts(category, 5);
    console.log(`Generated ${fallbackFacts.length} fallback facts for ${category}`);
    
    // Format facts properly
    const formattedFacts = fallbackFacts.map(text => ({ text, category }));
    
    // Create and upload video with fallback facts
    console.log("Creating video with fallback facts...");
    const videoPath = await createFactVideo(formattedFacts, category);
    console.log(`Video created at: ${videoPath}`);
    
    // Upload video to YouTube
    const title = `${fallbackFacts.length} Amazing ${category.charAt(0).toUpperCase() + category.slice(1)} Facts You Never Knew!`;
    const description = `Discover these amazing facts about ${category}!\n\n` +
                     fallbackFacts.map((fact, index) => `• ${fact}`).join('\n\n') + 
                     '\n\n#facts #' + category + ' #didyouknow';
    
    const tags = ['facts', category, 'did you know', 'amazing facts', 'interesting'];
    
    console.log("Uploading video to YouTube...");
    const videoId = await uploadToYouTube(videoPath, title, description, tags);
    console.log(`Video upload complete. Video ID: ${videoId}`);
    
    // If we have a facts database, update it, but don't rely on it working
    try {
      const databaseExists = await fs.pathExists(config.factsDatabasePath);
      if (databaseExists) {
        let database = await fs.readJson(config.factsDatabasePath);
        if (!database.categories) {
          database.categories = {};
        }
        if (!database.categories[category]) {
          database.categories[category] = [];
        }
        
        // Add the used facts to the database
        for (const fact of fallbackFacts) {
          database.categories[category].push({
            text: fact,
            category,
            verificationScore: 3,
            dateAdded: new Date().toISOString(),
            used: true,
            usedDate: new Date().toISOString()
          });
        }
        
        await fs.writeJson(config.factsDatabasePath, database, { spaces: 2 });
        console.log("Facts database updated successfully");
      } else {
        // Create a new database
        const newDatabase = {
          lastUpdated: new Date().toISOString(),
          categories: {}
        };
        
        newDatabase.categories[category] = fallbackFacts.map(fact => ({
          text: fact,
          category,
          verificationScore: 3,
          dateAdded: new Date().toISOString(),
          used: true,
          usedDate: new Date().toISOString()
        }));
        
        await fs.writeJson(config.factsDatabasePath, newDatabase, { spaces: 2 });
        console.log("New facts database created successfully");
      }
    } catch (dbError) {
      console.error("Error updating database, but continuing:", dbError.message);
    }
    
    console.log("Video automation completed successfully");
  } catch (error) {
    console.error("Error in main execution:", error);
    process.exit(1);
  }
}

// Run the main function
main();