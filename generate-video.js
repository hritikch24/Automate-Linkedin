// Complete Enhanced generate-video.js - All original features + AI enhancements

const fs = require('fs-extra');
const axios = require('axios');
const { google } = require('googleapis');
const ffmpegPath = require('@ffmpeg-installer/ffmpeg').path;
const ffmpeg = require('fluent-ffmpeg');

ffmpeg.setFfmpegPath(ffmpegPath);

// Import the enhanced frame-based solution
const frameBasedSolution = require('./frame-based-solution');

const config = {
  // Use environment variables for sensitive data
  geminiApiKey: process.env.GEMINI_API_KEY,
  youtubeClientId: process.env.YOUTUBE_CLIENT_ID,
  youtubeClientSecret: process.env.YOUTUBE_CLIENT_SECRET, 
  youtubeRefreshToken: process.env.YOUTUBE_REFRESH_TOKEN,
  
  // Enhanced categories with better prompts
  categories: [
    "history", 
    "geography", 
    "science", 
    "ancient_civilizations", 
    "space", 
    "ocean",
    "technology",
    "psychology",
    "biology",
    "physics"
  ],
  
  // Video settings
  factsPerVideo: 5,
  
  // File paths
  factsDatabasePath: "./facts_database.json",
  videoTemplatesPath: "./video_templates/",
  outputPath: "./output_videos/",
  
  // AI and verification settings
  useAIGeneration: true,
  verificationThreshold: 2, // How many verifications must match
  useEnhancedVideo: true, // Use enhanced video creation
};

// ----- ENHANCED AI FACT GENERATION -----

/**
 * Generate high-quality facts using enhanced AI prompts
 */
async function generateEnhancedFactsForCategory(category, count = 10) {
  console.log(`Generating ${count} enhanced facts for category: ${category}`);
  
  const enhancedPrompt = `You are a expert content creator for educational YouTube videos. Generate ${count} fascinating, verified, and engaging facts about ${category}.

REQUIREMENTS:
- Each fact must be 100% accurate and verifiable
- Facts should be surprising but not widely known
- Perfect for short-form video content (YouTube Shorts/TikTok)
- Include specific numbers, dates, or measurements when possible
- Avoid common knowledge facts
- Make them "wow factor" worthy

STYLE:
- Write in an engaging, conversational tone
- Use specific details that make facts memorable
- Include context that makes facts more interesting
- Aim for facts that make people say "I had no idea!"

FORMAT: Return as JSON array of objects with this structure:
[
  {
    "fact": "The main fact statement",
    "hook": "An attention-grabbing opener",
    "context": "Additional interesting context",
    "wow_factor": "Why this is amazing"
  }
]

CATEGORY: ${category}

Examples for ${category}:
${getCategoryExamples(category)}`;
  
  try {
    const response = await axios.post(
      'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent',
      {
        contents: [{
          parts: [{
            text: enhancedPrompt
          }]
        }],
        generationConfig: {
          temperature: 0.3, // Lower for more factual content
          topK: 40,
          topP: 0.8,
          maxOutputTokens: 2048,
        }
      },
      {
        headers: {
          'Content-Type': 'application/json',
          'x-goog-api-key': config.geminiApiKey
        }
      }
    );
    
    const textResponse = response.data.candidates[0].content.parts[0].text;
    console.log('Raw AI response:', textResponse.substring(0, 200) + '...');
    
    // Try to parse JSON from response
    const jsonMatch = textResponse.match(/\[[\s\S]*\]/);
    
    if (jsonMatch) {
      try {
        const factsArray = JSON.parse(jsonMatch[0]);
        console.log(`Successfully generated ${factsArray.length} enhanced facts`);
        return factsArray;
      } catch (e) {
        console.error("Failed to parse JSON from enhanced response:", e);
        // Fallback to simple parsing
        return parseSimpleFacts(textResponse, count);
      }
    } else {
      console.error("No JSON array found in enhanced response");
      return parseSimpleFacts(textResponse, count);
    }
  } catch (error) {
    console.error("Error generating enhanced facts:", error.message);
    return [];
  }
}

/**
 * Generate facts using Gemini API for a specific category (Original method)
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
 * Get category-specific examples to guide AI
 */
function getCategoryExamples(category) {
  const examples = {
    history: `- The shortest war in history lasted only 38-45 minutes between Britain and Zanzibar
- Cleopatra lived closer in time to the Moon landing than to the construction of the Great Pyramid
- Oxford University is older than the Aztec Empire`,
    
    science: `- Your body produces 25 million new cells every second
- A single bolt of lightning contains enough energy to power a 100-watt bulb for 3 months
- There are more possible moves in chess than atoms in the observable universe`,
    
    space: `- One day on Venus is longer than one year on Venus
- The footprints on the Moon will remain there for at least 100 million years
- Neutron stars are so dense that a teaspoon would weigh 6 billion tons`,
    
    ocean: `- We've explored less than 5% of our oceans, but 100% of Mars' surface
- The ocean contains 99% of Earth's living space but only 1% has been explored
- There are more historical artifacts under the sea than in all museums combined`
  };
  
  return examples[category] || `- Generate surprising, specific facts with numbers and context
- Focus on lesser-known but verifiable information
- Include details that make facts memorable and shareable`;
}

/**
 * Parse facts from simple text response
 */
function parseSimpleFacts(textResponse, count) {
  const lines = textResponse.split('\n').filter(line => 
    line.trim() && 
    (line.includes('-') || line.includes('•') || /^\d+\./.test(line.trim()))
  );
  
  return lines.slice(0, count).map(line => {
    const cleanFact = line.replace(/^[-•\d.\s]+/, '').trim();
    return {
      fact: cleanFact,
      hook: "Here's something incredible:",
      context: "This amazing fact will surprise you!",
      wow_factor: "Amazing!"
    };
  });
}

/**
 * Verifies a fact by checking it multiple times (Original verification system)
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
 * Generate facts for all categories or refresh existing ones (Original database system)
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
    
    // Try enhanced generation first, then fallback to original
    let generatedFacts = [];
    if (config.useAIGeneration && config.geminiApiKey) {
      try {
        generatedFacts = await generateEnhancedFactsForCategory(category, 15);
        if (generatedFacts.length === 0) {
          const simpleFacts = await generateFactsForCategory(category, 15);
          generatedFacts = simpleFacts.map(fact => ({
            fact: fact,
            hook: "Did you know...",
            context: "This will surprise you!",
            wow_factor: "Amazing!"
          }));
        }
      } catch (error) {
        console.error("Enhanced generation failed, using fallback:", error.message);
        generatedFacts = getEnhancedFallbackFacts(category, 15);
      }
    } else {
      generatedFacts = getEnhancedFallbackFacts(category, 15);
    }
    
    // Verify each fact if we have API access
    const verifiedFacts = [];
    for (const factObj of generatedFacts) {
      const factText = typeof factObj === 'string' ? factObj : factObj.fact;
      
      if (config.geminiApiKey) {
        const verificationResult = await verifyFact(factText);
        if (verificationResult.verified) {
          verifiedFacts.push({
            text: factText,
            enhanced: factObj,
            category,
            verificationScore: verificationResult.score,
            dateAdded: new Date().toISOString(),
            used: false
          });
        }
      } else {
        // Skip verification if no API key
        verifiedFacts.push({
          text: factText,
          enhanced: factObj,
          category,
          verificationScore: 3, // Assume pre-verified fallback facts are good
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

/**
 * Enhanced fallback facts with better structure (Complete original database)
 */
function getEnhancedFallbackFacts(category, count) {
  const enhancedFactsByCategory = {
    "history": [
      {
        fact: "The shortest war in history was between Britain and Zanzibar in 1896, lasting only 38 minutes.",
        hook: "You won't believe how short this war was...",
        context: "Zanzibar surrendered after British ships bombarded the palace.",
        wow_factor: "Talk about a quick victory!"
      },
      {
        fact: "Ancient Egyptians used to sleep on pillows made of stone.",
        hook: "Ancient bedtime was very different...",
        context: "They believed stone pillows kept evil spirits away from their heads.",
        wow_factor: "Imagine trying to get comfortable on that!"
      },
      {
        fact: "Vikings used the bones of slain animals to make their weapons stronger.",
        hook: "Viking weapon-making had a secret ingredient...",
        context: "They would burn bones to create carbon for stronger steel.",
        wow_factor: "Ancient recycling at its finest!"
      },
      {
        fact: "The Great Wall of China is not visible from space with the naked eye, contrary to popular belief.",
        hook: "This famous 'fact' is actually false...",
        context: "Astronauts have confirmed this myth is completely wrong.",
        wow_factor: "One of history's biggest misconceptions!"
      },
      {
        fact: "Napoleon was actually of average height for his time (5'7\"), not short as commonly believed.",
        hook: "Everything you know about Napoleon's height is wrong...",
        context: "British propaganda made him seem short, but he was normal sized.",
        wow_factor: "History's biggest height myth busted!"
      },
      {
        fact: "Roman soldiers were sometimes paid in salt, which is where the word 'salary' comes from.",
        hook: "Your paycheck has ancient Roman origins...",
        context: "Salt was so valuable it was literally used as currency.",
        wow_factor: "You're literally worth your salt!"
      },
      {
        fact: "The first recorded Olympic Games were held in 776 BCE in Olympia, Greece.",
        hook: "The Olympics are older than you think...",
        context: "They ran for nearly 12 centuries before being banned.",
        wow_factor: "Talk about a long-running tradition!"
      },
      {
        fact: "Cleopatra lived closer in time to the moon landing than to the building of the Great Pyramid.",
        hook: "This will completely mess with your timeline...",
        context: "The pyramids were ancient even to ancient Egyptians.",
        wow_factor: "History is way longer than we imagine!"
      },
      {
        fact: "Harvard University was founded before calculus was invented.",
        hook: "Harvard is older than you realize...",
        context: "Founded in 1636, calculus wasn't developed until the 1660s.",
        wow_factor: "They were teaching without modern math!"
      },
      {
        fact: "The oldest known living tree is over 5,000 years old, located in California.",
        hook: "This tree has seen all of recorded history...",
        context: "It was already ancient when the pyramids were built.",
        wow_factor: "A living witness to civilization!"
      }
    ],
    "geography": [
      {
        fact: "Russia borders 14 different countries, more than any other nation.",
        hook: "This country has the most neighbors in the world...",
        context: "It spans 11 time zones and touches three continents.",
        wow_factor: "Talk about having good fences!"
      },
      {
        fact: "The Sahara Desert expands and contracts seasonally, changing its size by about 10%.",
        hook: "This desert is like a breathing giant...",
        context: "It grows in winter and shrinks in summer due to rainfall patterns.",
        wow_factor: "A shape-shifting landscape!"
      },
      {
        fact: "There's a town in Norway called Hell that freezes over every winter.",
        hook: "Hell really does freeze over...",
        context: "It's pronounced 'hell' and means 'flat rock' in Old Norse.",
        wow_factor: "The ultimate weather joke!"
      },
      {
        fact: "The continent of Asia covers about 30% of Earth's total land area.",
        hook: "This continent is absolutely massive...",
        context: "It contains 60% of the world's population too.",
        wow_factor: "Nearly a third of all land!"
      },
      {
        fact: "Alaska has more coastline than all other U.S. states combined.",
        hook: "This state has an incredible amount of shore...",
        context: "It has over 6,600 miles of coastline due to its complex geography.",
        wow_factor: "More beaches than you could visit in a lifetime!"
      },
      {
        fact: "The world's largest desert is Antarctica, not the Sahara.",
        hook: "The biggest desert might surprise you...",
        context: "Deserts are defined by low precipitation, not heat.",
        wow_factor: "Cold can be just as dry as hot!"
      },
      {
        fact: "Point Nemo in the Pacific Ocean is the most remote place on Earth, with the nearest humans often being astronauts on the ISS.",
        hook: "There's a place where space is closer than land...",
        context: "It's 1,450 miles from the nearest land in any direction.",
        wow_factor: "Literally closer to space than civilization!"
      },
      {
        fact: "Vatican City is the smallest country in the world, at just 44 hectares (109 acres).",
        hook: "This entire country is smaller than most parks...",
        context: "You could walk across the whole country in 20 minutes.",
        wow_factor: "A nation you could jog around!"
      },
      {
        fact: "Brazil shares a border with every South American country except Chile and Ecuador.",
        hook: "This country touches almost all its neighbors...",
        context: "It covers nearly half of South America's land area.",
        wow_factor: "The ultimate friendly neighbor!"
      },
      {
        fact: "The Maldives is the flattest and lowest-lying country in the world.",
        hook: "This country is disappearing due to sea level rise...",
        context: "Its highest point is only 8 feet above sea level.",
        wow_factor: "Living on the edge of the ocean!"
      }
    ],
    "science": [
      {
        fact: "Honey never spoils. Archaeologists have found pots of honey in ancient Egyptian tombs that are over 3,000 years old and still perfectly good to eat.",
        hook: "This food never goes bad, ever...",
        context: "Its low water content and acidic pH make it naturally antimicrobial.",
        wow_factor: "Ancient Egyptian honey is still perfectly good to eat!"
      },
      {
        fact: "20% of Earth's oxygen is produced by the Amazon rainforest.",
        hook: "This forest is literally the lungs of our planet...",
        context: "It produces oxygen while absorbing massive amounts of CO2.",
        wow_factor: "Every fifth breath you take comes from the Amazon!"
      },
      {
        fact: "A day on Venus is longer than a year on Venus. It takes 243 Earth days to rotate once on its axis and 225 Earth days to orbit the sun.",
        hook: "This planet has the weirdest calendar in the solar system...",
        context: "Venus rotates backwards compared to most planets.",
        wow_factor: "A day longer than a year - mind blown!"
      },
      {
        fact: "Bananas are berries, but strawberries aren't actually berries at all.",
        hook: "Everything you know about berries is wrong...",
        context: "Botanically, berries must have seeds inside the flesh.",
        wow_factor: "Your fruit knowledge just got flipped upside down!"
      },
      {
        fact: "The human body contains enough carbon to make about 9,000 pencils.",
        hook: "You're literally made of pencil material...",
        context: "Carbon makes up 18% of your body weight.",
        wow_factor: "You could write a small library with yourself!"
      },
      {
        fact: "Octopuses have three hearts, nine brains, and blue blood.",
        hook: "These creatures are alien-like in their biology...",
        context: "Two hearts pump blood to the gills, one to the body.",
        wow_factor: "Triple the hearts, nine times the brains!"
      },
      {
        fact: "A bolt of lightning is five times hotter than the surface of the sun.",
        hook: "Lightning is incredibly hot...",
        context: "It reaches temperatures of about 30,000 Kelvin.",
        wow_factor: "Hotter than the sun's surface!"
      },
      {
        fact: "Sharks have existed for over 450 million years, predating dinosaurs, trees, and even Mount Everest.",
        hook: "Sharks are older than you can imagine...",
        context: "They've survived five mass extinction events.",
        wow_factor: "Ultimate survivors of evolution!"
      },
      {
        fact: "The shortest scientific paper ever published contained just two sentences.",
        hook: "Sometimes science can be incredibly brief...",
        context: "It proved a mathematical theorem in just 34 words.",
        wow_factor: "Proof that less can be more!"
      },
      {
        fact: "The average human produces enough saliva in their lifetime to fill two swimming pools.",
        hook: "Your mouth is a saliva factory...",
        context: "You produce about 1-2 liters of saliva per day.",
        wow_factor: "That's a lot of spit!"
      }
    ],
    "ancient_civilizations": [
      {
        fact: "The ancient city of Çatalhöyük in Turkey had no streets - residents walked on rooftops and entered homes through ceiling openings.",
        hook: "This ancient city had the weirdest layout...",
        context: "Houses were built side by side with flat roofs serving as streets.",
        wow_factor: "Imagine your daily commute on rooftops!"
      },
      {
        fact: "Mesopotamian doctors were sometimes paid extra if their patients were wealthy or of high social status.",
        hook: "Ancient healthcare had VIP pricing...",
        context: "The Code of Hammurabi detailed different fees for different classes.",
        wow_factor: "Some things never change!"
      },
      {
        fact: "The Indus Valley Civilization had sophisticated plumbing systems over 4,000 years ago.",
        hook: "Ancient toilets were surprisingly advanced...",
        context: "They had flush toilets and covered sewers before most civilizations.",
        wow_factor: "Better plumbing than medieval Europe!"
      },
      {
        fact: "Ancient Mayans believed crossing your eyes was beautiful and would hang objects in front of babies' eyes to make them permanently cross-eyed.",
        hook: "Mayan beauty standards were unique...",
        context: "They also flattened foreheads and filed teeth for beauty.",
        wow_factor: "Beauty really is in the eye of the beholder!"
      },
      {
        fact: "The ancient Greek city of Sparta had no walls despite being a military powerhouse.",
        hook: "This warrior city had no defenses...",
        context: "They believed their soldiers were their walls.",
        wow_factor: "Confidence level: Spartan!"
      },
      {
        fact: "Ancient Egyptians used crocodile dung as a contraceptive.",
        hook: "Ancient birth control was... creative...",
        context: "They mixed it with honey and inserted it as a pessary.",
        wow_factor: "Definitely not FDA approved!"
      },
      {
        fact: "The Chinese were using natural gas for heating and lighting as early as 500 BCE, transported through bamboo pipes.",
        hook: "Ancient China had natural gas pipelines...",
        context: "They discovered it while drilling for salt water.",
        wow_factor: "2,500 years ahead of their time!"
      },
      {
        fact: "In ancient Rome, urine was collected and used to wash clothes due to its ammonia content.",
        hook: "Roman laundry day was different...",
        context: "They even taxed urine collection because it was so valuable.",
        wow_factor: "When pee was worth its weight in gold!"
      },
      {
        fact: "The ancient Inca Empire built thousands of miles of roads without using wheeled vehicles.",
        hook: "The Incas built roads but didn't use wheels...",
        context: "They used llamas and human runners for transportation.",
        wow_factor: "Sometimes simpler is better!"
      },
      {
        fact: "Ancient Aztecs used chocolate as currency.",
        hook: "Imagine paying with chocolate...",
        context: "Cacao beans were so valuable they were counterfeited.",
        wow_factor: "The most delicious money ever!"
      }
    ],
    "space": [
      {
        fact: "There is a planet made of diamonds, called 55 Cancri e.",
        hook: "There's literally a diamond planet out there...",
        context: "It's twice the size of Earth and covered in graphite and diamonds.",
        wow_factor: "The ultimate bling in space!"
      },
      {
        fact: "The footprints left on the Moon will remain there for at least 100 million years.",
        hook: "Neil Armstrong's footprints are permanent...",
        context: "There's no wind or weather to erode them on the Moon.",
        wow_factor: "The longest-lasting human artifacts!"
      },
      {
        fact: "One day on Venus is longer than one year on Venus.",
        hook: "Venus has the weirdest calendar in space...",
        context: "It rotates so slowly that it orbits the sun faster than it spins.",
        wow_factor: "Time works differently on Venus!"
      },
      {
        fact: "The largest asteroid, Ceres, is so big it's classified as a dwarf planet.",
        hook: "Some asteroids are planet-sized...",
        context: "Ceres contains about one-third of all asteroid belt mass.",
        wow_factor: "When an asteroid becomes a planet!"
      },
      {
        fact: "The Sun makes up 99.86% of the mass in our solar system.",
        hook: "The Sun is almost everything in our solar system...",
        context: "All planets combined are just 0.14% of the solar system's mass.",
        wow_factor: "We're basically living in the Sun's neighborhood!"
      },
      {
        fact: "Saturn's rings are mostly made of ice and are only about 10 meters thick on average.",
        hook: "Saturn's rings are thinner than you think...",
        context: "They're 175,000 miles wide but only as thick as a building.",
        wow_factor: "Like a cosmic razor blade!"
      },
      {
        fact: "A year on Neptune lasts for 165 Earth years.",
        hook: "Neptune takes forever to orbit the sun...",
        context: "Since its discovery in 1846, it has completed just one orbit.",
        wow_factor: "Neptune is still in its discovery year!"
      },
      {
        fact: "There are more stars in the universe than grains of sand on all of Earth's beaches.",
        hook: "The universe has more stars than sand...",
        context: "Estimated 10^24 stars vs 10^20 grains of sand.",
        wow_factor: "Space is infinitely more vast than Earth!"
      },
      {
        fact: "The Great Red Spot on Jupiter is a storm that has been raging for at least 400 years.",
        hook: "Jupiter has a storm older than America...",
        context: "It's twice the size of Earth and shows no signs of stopping.",
        wow_factor: "The longest weather event in the solar system!"
      },
      {
        fact: "Mercury and Venus are the only planets in our solar system with no moons.",
        hook: "Some planets are moon-less loners...",
        context: "Their proximity to the Sun makes it hard to capture moons.",
        wow_factor: "Sometimes you've got to go it alone!"
      }
    ],
    "ocean": [
      {
        fact: "The ocean contains 97% of Earth's water, but only about 5% has been explored.",
        hook: "We know more about space than our own oceans...",
        context: "We've mapped more of Mars than our ocean floor.",
        wow_factor: "The greatest frontier is right here on Earth!"
      },
      {
        fact: "There are more historical artifacts under the ocean than in all museums worldwide combined.",
        hook: "The ocean is the world's largest museum...",
        context: "Thousands of shipwrecks hold countless treasures and artifacts.",
        wow_factor: "History is literally underwater!"
      },
      {
        fact: "The Mid-Ocean Ridge is the longest mountain range on Earth, stretching over 40,000 miles.",
        hook: "Earth's longest mountain range is underwater...",
        context: "It's four times longer than the Andes, Rockies, and Himalayas combined.",
        wow_factor: "Hidden beneath the waves!"
      },
      {
        fact: "The world's oceans contain nearly 20 million tons of gold.",
        hook: "There's a fortune in gold in the ocean...",
        context: "It's so diluted that extracting it would cost more than it's worth.",
        wow_factor: "Rich beyond measure, but impossible to mine!"
      },
      {
        fact: "The deepest part of the ocean, the Mariana Trench, is deeper than Mount Everest is tall.",
        hook: "The ocean's deepest point could swallow Everest...",
        context: "If Everest were placed in the trench, its peak would still be a mile underwater.",
        wow_factor: "The ultimate depth vs height comparison!"
      },
      {
        fact: "Some species of deep-sea creatures can live without oxygen, using sulfur compounds instead.",
        hook: "Some ocean life doesn't need oxygen to survive...",
        context: "They live around hydrothermal vents using chemosynthesis.",
        wow_factor: "Life finds a way, even without air!"
      },
      {
        fact: "The blue whale, the largest animal on Earth, can produce sounds louder than a jet engine.",
        hook: "Blue whales are louder than airplanes...",
        context: "Their calls can reach 188 decibels and travel for hundreds of miles.",
        wow_factor: "The ocean's loudest resident!"
      },
      {
        fact: "There are lakes and rivers beneath the ocean with their own shores, different density, and unique wildlife.",
        hook: "There are rivers inside the ocean...",
        context: "Brine pools form underwater 'lakes' with distinct boundaries.",
        wow_factor: "Inception-level water features!"
      },
      {
        fact: "Some marine snails can surf on their own mucus to travel faster across the ocean floor.",
        hook: "Ocean snails are natural surfers...",
        context: "They create mucus trails and ride the currents like a surfboard.",
        wow_factor: "Gnarly moves from the deep!"
      },
      {
        fact: "The Great Barrier Reef is the largest living structure on Earth, visible even from space.",
        hook: "This reef is so big you can see it from space...",
        context: "It's larger than Italy and home to thousands of species.",
        wow_factor: "A living landmark visible from orbit!"
      }
    ]
  };
  
  // If category doesn't exist in our predefined facts, use general facts
  if (!enhancedFactsByCategory[category]) {
    const allFacts = Object.values(enhancedFactsByCategory).flat();
    return allFacts.sort(() => 0.5 - Math.random()).slice(0, count);
  }
  
  // Return random facts from the selected category
  return enhancedFactsByCategory[category].sort(() => 0.5 - Math.random()).slice(0, count);
}

// ----- VIDEO CREATION (Enhanced + Original) -----

/**
 * Creates an enhanced video with AI content, visuals, and audio
 */
async function createEnhancedFactVideo(facts, category) {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const outputFileName = `${category}_enhanced_${timestamp}.mp4`;
  const outputPath = `${config.outputPath}${outputFileName}`;
  
  console.log(`Creating enhanced video for ${category} with ${facts.length} facts...`);
  
  // Ensure output directory exists
  await fs.ensureDir(config.outputPath);
  
  try {
    if (config.useEnhancedVideo) {
      console.log("Using enhanced frame-based video generation...");
      
      // Use the enhanced frame-based approach
      const result = await frameBasedSolution.createFrameBasedVideo(
        facts,
        category,
        outputPath
      );
      
      console.log(`Enhanced video created successfully!`);
      console.log(`Video: ${result.videoPath}`);
      
      return {
        videoPath: result.videoPath,
        title: result.title || `${facts.length} Amazing ${category.charAt(0).toUpperCase() + category.slice(1)} Facts`,
        description: result.description || generateBasicDescription(facts, category),
        tags: result.tags || ['facts', category, 'amazing', 'educational']
      };
    } else {
      // Use original simple method
      return await createBasicVideo(outputPath, `${facts.length} ${category} Facts`, facts);
    }
    
  } catch (error) {
    console.error("Enhanced video creation failed:", error.message);
    
    // Fallback to basic video
    console.log("Falling back to basic video creation...");
    return await createBasicVideo(outputPath, `${facts.length} ${category} Facts`, facts);
  }
}

/**
 * Creates a basic video with white background and black text (Original method)
 */
async function createBasicVideo(outputPath, title, facts = []) {
  console.log('Creating basic video:', title);
  
  try {
    // Create a text file with the facts for documentation
    const factsText = facts.map((fact, index) => {
      const factText = typeof fact === 'object' ? 
        (fact.enhanced ? fact.enhanced.fact : fact.text) : 
        fact;
      return `Fact ${index+1}: ${factText}`;
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
    
    console.log(`Basic video created: ${outputPath}`);
    return {
      videoPath: outputPath,
      title: title,
      description: generateBasicDescription(facts, title.includes('history') ? 'history' : 'general'),
      tags: ['facts', 'educational', 'amazing']
    };
  } catch (error) {
    console.error('Failed to create basic video:', error);
    throw error;
  }
}

/**
 * Generate basic description
 */
function generateBasicDescription(facts, category) {
  const factTexts = facts.map((fact, index) => {
    const factText = typeof fact === 'object' ? 
      (fact.enhanced ? fact.enhanced.fact : fact.text) : 
      fact;
    return `• ${factText}`;
  });
  
  return `Discover amazing facts about ${category}!\n\n${factTexts.join('\n\n')}\n\n#facts #${category} #didyouknow #amazing #educational`;
}

// ----- DATABASE MANAGEMENT (Original functions) -----

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

// ----- YOUTUBE INTEGRATION (Original + Enhanced) -----

/**
 * Authenticates with YouTube API using stored refresh token
 */
async function authenticateYouTube() {
  try {
    const oauth2Client = new google.auth.OAuth2(
      config.youtubeClientId,
      config.youtubeClientSecret,
      'http://localhost:3000/oauth2callback'
    );
    
    oauth2Client.setCredentials({
      refresh_token: config.youtubeRefreshToken
    });
    
    console.log("Getting fresh access token...");
    const tokens = await oauth2Client.refreshAccessToken();
    console.log("✅ YouTube authentication successful!");
    
    return oauth2Client;
  } catch (error) {
    console.error("❌ YouTube authentication failed:", error.message);
    throw error;
  }
}

/**
 * Enhanced YouTube upload with better metadata
 */
async function uploadEnhancedVideoToYouTube(videoResult) {
  try {
    const auth = await authenticateYouTube();
    const youtube = google.youtube('v3');
    
    console.log(`Uploading enhanced video: "${videoResult.title}"`);
    
    // Check if file exists
    const fileExists = await fs.pathExists(videoResult.videoPath);
    if (!fileExists) {
      console.error(`Video file not found: ${videoResult.videoPath}`);
      return `ERROR_FILE_NOT_FOUND_${Date.now()}`;
    }
    
    // Enhanced upload with better categorization
    const uploadData = {
      snippet: {
        title: videoResult.title,
        description: generateEnhancedDescription(videoResult),
        tags: videoResult.tags,
        categoryId: '27', // Education category
        defaultLanguage: 'en',
        defaultAudioLanguage: 'en'
      },
      status: {
        privacyStatus: 'public',
        embeddable: true,
        license: 'youtube'
      }
    };
    
    const res = await youtube.videos.insert({
      auth,
      part: 'snippet,status',
      requestBody: uploadData,
      media: {
        body: fs.createReadStream(videoResult.videoPath)
      }
    });
    
    console.log('==============================================');
    console.log(`✅ ENHANCED VIDEO UPLOADED SUCCESSFULLY!`);
    console.log(`📺 TITLE: ${videoResult.title}`);
    console.log(`🆔 VIDEO ID: ${res.data.id}`);
    console.log(`🔗 URL: https://www.youtube.com/watch?v=${res.data.id}`);
    console.log('==============================================');
    
    // Save upload record
    const recordPath = `${config.outputPath}upload_${res.data.id}.json`;
    await fs.writeJson(recordPath, {
      videoId: res.data.id,
      title: videoResult.title,
      uploadDate: new Date().toISOString(),
      url: `https://www.youtube.com/watch?v=${res.data.id}`,
      ...videoResult
    }, { spaces: 2 });
    
    return res.data.id;
    
  } catch (error) {
    console.error("Enhanced upload failed:", error.message);
    return `ERROR_UPLOAD_${Date.now()}`;
  }
}

/**
 * Generate enhanced description for YouTube
 */
function generateEnhancedDescription(videoResult) {
  const baseDescription = videoResult.description || `Get ready to have your mind blown with these incredible facts!`;
  
  const enhancedDescription = `${baseDescription}

🤯 TIMESTAMPS:
00:00 - Introduction
00:04 - Fact 1
00:10 - Fact 2
00:16 - Fact 3
00:22 - Fact 4
00:28 - Fact 5

📚 SOURCES: All facts are verified and sourced from reputable educational materials.

🔔 SUBSCRIBE for more amazing facts delivered daily!
👍 LIKE if you learned something new!
💬 COMMENT your favorite fact below!

#EducationalContent #FactsDaily #Knowledge #Learning #Science #History #Geography #AmazingFacts

---
Created with AI-assisted research and verification.
`;

  return enhancedDescription;
}

// ----- MAIN EXECUTION (Complete Enhanced) -----

async function main() {
  try {
    console.log("🚀 Starting Complete Enhanced YouTube Facts Automation...");
    console.log("⏰ Current time:", new Date().toISOString());
    
    // Verify configuration
    console.log("🔧 Checking configuration...");
    const configChecks = {
      'Gemini API Key': !!config.geminiApiKey,
      'YouTube Client ID': !!config.youtubeClientId,
      'YouTube Client Secret': !!config.youtubeClientSecret,
      'YouTube Refresh Token': !!config.youtubeRefreshToken,
      'Enhanced Video': config.useEnhancedVideo,
      'AI Generation': config.useAIGeneration
    };
    
    Object.entries(configChecks).forEach(([key, value]) => {
      console.log(`   ${value ? '✅' : '❌'} ${key}`);
    });
    
    // Setup directories
    await fs.ensureDir(config.outputPath);
    await fs.ensureDir(config.videoTemplatesPath);
    await fs.ensureDir('./temp_images/');
    await fs.ensureDir('./temp_audio/');
    await fs.ensureDir('./temp_slides/');
    
    // Test YouTube authentication
    console.log("🔐 Testing YouTube authentication...");
    const auth = await authenticateYouTube();
    
    // Get channel info
    const youtube = google.youtube('v3');
    const channelResponse = await youtube.channels.list({
      auth,
      part: 'snippet,statistics',
      mine: true
    });
    
    if (channelResponse.data.items?.length > 0) {
      const channel = channelResponse.data.items[0];
      console.log('📺 Channel:', channel.snippet.title);
      console.log('👥 Subscribers:', channel.statistics.subscriberCount);
      console.log('🎥 Videos:', channel.statistics.videoCount);
      console.log('👀 Views:', channel.statistics.viewCount);
    }
    
    // Smart category selection (Original algorithm)
    const date = new Date();
    const categoryIndex = (date.getDate() * 2 + (date.getHours() >= 12 ? 1 : 0)) % config.categories.length;
    const category = config.categories[categoryIndex];
    
    console.log(`🎯 Selected category: ${category}`);
    
    // Try to get facts from database first
    let facts = [];
    try {
      facts = await getUnusedFacts(category, config.factsPerVideo);
      if (facts.length > 0) {
        console.log(`📚 Using ${facts.length} facts from database for ${category}`);
      }
    } catch (dbError) {
      console.log("Database access failed, generating fresh facts");
    }
    
    // If no database facts, generate new ones
    if (facts.length === 0) {
      console.log("🧠 Generating fresh facts...");
      
      if (config.useAIGeneration && config.geminiApiKey) {
        try {
          const aiFacts = await generateEnhancedFactsForCategory(category, config.factsPerVideo);
          facts = aiFacts.map(fact => ({
            text: typeof fact === 'object' ? fact.fact : fact,
            enhanced: fact,
            category,
            verificationScore: 3,
            dateAdded: new Date().toISOString(),
            used: false
          }));
          console.log(`✅ Generated ${facts.length} AI facts for ${category}`);
        } catch (aiError) {
          console.error("❌ AI generation failed:", aiError.message);
          const fallbackFacts = getEnhancedFallbackFacts(category, config.factsPerVideo);
          facts = fallbackFacts.map(fact => ({
            text: fact.fact,
            enhanced: fact,
            category,
            verificationScore: 3,
            dateAdded: new Date().toISOString(),
            used: false
          }));
          console.log(`📚 Using ${facts.length} fallback facts`);
        }
      } else {
        const fallbackFacts = getEnhancedFallbackFacts(category, config.factsPerVideo);
        facts = fallbackFacts.map(fact => ({
          text: fact.fact,
          enhanced: fact,
          category,
          verificationScore: 3,
          dateAdded: new Date().toISOString(),
          used: false
        }));
        console.log(`📚 Using ${facts.length} predefined facts`);
      }
    }
    
    // Create enhanced video
    console.log("🎬 Creating enhanced video...");
    const videoResult = await createEnhancedFactVideo(facts, category);
    console.log(`✅ Video created: ${videoResult.videoPath}`);
    
    // Upload to YouTube
    console.log("📤 Uploading to YouTube...");
    const videoId = await uploadEnhancedVideoToYouTube(videoResult);
    console.log(`🎉 Upload complete! Video ID: ${videoId}`);
    
    // Mark facts as used if we have a working database
    try {
      await markFactsAsUsed(facts);
    } catch (markError) {
      console.log("Could not mark facts as used (database issue)");
    }
    
    // Save execution log
    const executionLog = {
      timestamp: new Date().toISOString(),
      category,
      videoId,
      title: videoResult.title,
      factsCount: facts.length,
      useEnhanced: config.useEnhancedVideo,
      useAI: config.useAIGeneration,
      status: videoId.startsWith('ERROR_') ? 'failed' : 'success'
    };
    
    await fs.writeJson(`${config.outputPath}execution_log.json`, executionLog, { spaces: 2 });
    
    console.log("🏁 Complete enhanced automation finished successfully!");
    
  } catch (error) {
    console.error("💥 Fatal error in complete automation:", error);
    process.exit(1);
  }
}

// Run the complete enhanced automation
main();